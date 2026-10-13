# -*- coding: utf-8 -*-
"""
Created on Sat Dec 14 01:32:37 2024

@author: Shoichi
"""
import Motion_storage
import visualization.panda.world as wd
import ObjectModelConfigManager
import graph_key_search as gks
import File_management as Fm
import copy
import basis.robot_math as rm
import tracemalloc
import random
import modeling.geometric_model as gm
import numpy as np
import math

class ExecutionChecker():
    reuse_robot = True  # False: 候補ごとにロボットモデルを作り直す（元の動作）/ rebuild the robot model for every candidate (original behaviour)

    def __init__(self, base):
        self.base = base
        self.OMCM = ObjectModelConfigManager.ObjectModelConfigManager(self.base)
        self._Ms = None

    def get_motion_storage(self):
        """ロボットモデルは1ステップにつき1回だけ生成し、候補ごとに初期状態へ戻す
        Build the robot model once per step and reset it to its initial state for each candidate"""
        if not self.reuse_robot:
            return Motion_storage.WRSA_motion_storage(self.base)
        if self._Ms is None:
            self._Ms = Motion_storage.WRSA_motion_storage(self.base)
            robot = self._Ms.robot_s
            # RobotiqHEは開き幅を返さないので指の関節値を保存 / RobotiqHE has no get_jawwidth, so store its finger joint value
            self._initial_state = {hnd: (robot.get_jnt_values(hnd), robot.hnd_dict[hnd].lft.jnts[1]['motion_val']) for hnd in ('rgt_hnd', 'lft_hnd')}
        else:
            robot = self._Ms.robot_s
            # 失敗した候補が把持したままのオブジェクトを解放 / release objects a failed candidate left in the hand
            for hnd, oih_infos in (('lft_hnd', robot.lft_oih_infos), ('rgt_hnd', robot.rgt_oih_infos)):
                for obj_info in list(oih_infos):
                    robot.release(hnd, obj_info['collision_model'])
            for hnd, (jnt_values, finger_value) in self._initial_state.items():
                robot.fk(hnd, jnt_values)
                robot.hnd_dict[hnd].fk(motion_val=finger_value)
        return self._Ms
 
    def get_target_node(self, tree, task_num):
        turget_nodes = [key for key in tree.nodes.keys() if tree.nodes[key]['level'] == task_num]
        return turget_nodes
 
    def get_environment_from_parent_node(self, node, Tree):  
        parent_node = Tree.get_parent(node)
        EG = copy.deepcopy(Tree.tree.nodes[parent_node]['EG'])
        available_area = copy.deepcopy(Tree.tree.nodes[parent_node]['available_area'])
        obj_pos_dic = copy.deepcopy(Tree.tree.nodes[parent_node]['obj_pos_dic'])
        obj_model_dic = self.OMCM.set_object_model(obj_pos_dic, EG)
        Ms = self.get_motion_storage()
        if Tree.tree.nodes[parent_node]['conf_list'] != {}:
            Ms.robot_s.fk('rgt_hnd', Tree.tree.nodes[parent_node]['conf_list']['rgt_hnd'][-1])
            Ms.robot_s.jaw_to('rgt_hnd', Tree.tree.nodes[parent_node]['jawwidth_list']['rgt_hnd'][-1])
            Ms.robot_s.fk('lft_hnd', Tree.tree.nodes[parent_node]['conf_list']['lft_hnd'][-1])
            Ms.robot_s.jaw_to('lft_hnd', Tree.tree.nodes[parent_node]['jawwidth_list']['lft_hnd'][-1])
            # mesh = Ms.robot_s.gen_meshmodel()
            # mesh.attach_to(self.base)
            # self.base.run()
        return EG, available_area, obj_model_dic, Ms, obj_pos_dic
    
    def del_available_area(self, available_area, area, place):
        available_area[place] = [area_i for area_i in available_area[place] if area_i != area]
 
    def Pic_checker(self, FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic):
        print('Pic')
        out_node = list(FOON.predecessors(task[0]))
        FU_obj_key = [node for node in out_node if FOON.nodes[node]['label'] == task[1]['object']]
        FU_hnd_key = [node for node in out_node if '_H_' in node]
        if FOON.nodes[FU_hnd_key[0]]['label'] == 'right_hand':
            hand_name = 'rgt_hnd'
            other_hand = 'lft_hnd'
        else:
            hand_name = 'lft_hnd'
            other_hand = 'rgt_hnd'
        grasp_info = Tree.tree.nodes[node]['grasp_id']
        ###条件分岐で使用可能な配置場所を追加
        place = FOON.nodes[FU_obj_key[0]]['place']
        area = EG.nodes[FOON.nodes[FU_obj_key[0]]['id']]['area']
        model = obj_model_dic[FOON.nodes[FU_obj_key[0]]['id']]
        goal_homomat_list = [model.get_homomat()]
        obstacle_list = [obj_model_dic[key] for key in obj_model_dic.keys() if FOON.nodes[FU_obj_key[0]]['id'] != key and '_F_' not in key]
        # Ms.visual_obj(obstacle_list + [model],toggle_detach=True)
        # Ms.visual_obj(obstacle_list)
        obstacle_list = []
        if FOON.nodes[FU_obj_key[0]]['type'] == 'ingredients':
            obstacle_list = [obj_model_dic[key] for key in obj_model_dic.keys() if key != FOON.nodes[FU_obj_key[0]]['container'][1] and FOON.nodes[FU_obj_key[0]]['id'] != key]
            # Ms.visual_obj(obstacle_list)
            conf_list, jawwidth_list, objpose_list = Ms.Pic_motion(hand_name, model, Ms.robot_s.get_jnt_values(hand_name), Ms.robot_s.get_jnt_values(hand_name), grasp_info, goal_homomat_list, obstacle_list=obstacle_list, toggle_grasp=False, toggle_sphere=False)
        else:
            if FOON.nodes[FU_obj_key[0]]['ingredients'] != [['', '']] and FOON.nodes[FU_obj_key[0]]['ingredients'] != ['', '']:
                model_list = [model]
                for ing in FOON.nodes[FU_obj_key[0]]['ingredients']:
                    if ing[1] in obj_model_dic.keys():
                        model_list.append(obj_model_dic[ing[1]])
                if len(model_list) == 1:
                    self.del_available_area(available_area, area, place)
                    conf_list, jawwidth_list, objpose_list = Ms.Pic_motion(hand_name, model, Ms.robot_s.get_jnt_values(hand_name), Ms.robot_s.get_jnt_values(hand_name), grasp_info, goal_homomat_list, obstacle_list=obstacle_list, toggle_grasp=False, toggle_sphere=False, toggle_obj=False)
                else:
                    self.del_available_area(available_area, area, place)
                    conf_list, jawwidth_list, objpose_list, ingpose_list = Ms.Pic_motion(hand_name, model_list, Ms.robot_s.get_jnt_values(hand_name), Ms.robot_s.get_jnt_values(hand_name), grasp_info, goal_homomat_list, obstacle_list=obstacle_list, toggle_grasp=False, toggle_sphere=False, toggle_obj=False)  
            else:
                self.del_available_area(available_area, area, place)
                conf_list, jawwidth_list, objpose_list = Ms.Pic_motion(hand_name, model, Ms.robot_s.get_jnt_values(hand_name), Ms.robot_s.get_jnt_values(hand_name), grasp_info, goal_homomat_list, obstacle_list=obstacle_list, toggle_grasp=False, toggle_sphere=False, toggle_obj=False)
        obj_list = obstacle_list + [model]
        # Ms.visual_obj(obj_list)
        if conf_list is None:
            print('把持計画失敗')
            Ms.gen_model.detach()
            Tree.remove_node_and_descendants(node)
            return False
        else:
            print('把持計画成功')
            obj_pos_dic[FOON.nodes[FU_obj_key[0]]['id']] = [objpose_list[-1][:3, 3], objpose_list[-1][:3, :3]]
            Tree.tree.nodes[node]['available_area'] = copy.deepcopy(available_area)
            Tree.tree.nodes[node]['EG'] = EG
            Tree.tree.nodes[node]['conf_list'] = {hand_name:conf_list, other_hand:[Ms.robot_s.get_jnt_values(other_hand) for i in range(len(conf_list))]}
            Tree.tree.nodes[node]['jawwidth_list'] = {hand_name:jawwidth_list, other_hand:[Ms.robot_s.hnd_dict[other_hand].jawwidth_rng[1] for i in range(len(jawwidth_list))]}
            Tree.tree.nodes[node]['obj_list'] = {FOON.nodes[FU_obj_key[0]]['id']:objpose_list}
            if FOON.nodes[FU_obj_key[0]]['ingredients'] != [['', '']] and FOON.nodes[FU_obj_key[0]]['ingredients'] != ['', ''] and len(model_list) > 1:
                for i, ing, pos in zip(range(len(FOON.nodes[FU_obj_key[0]]['ingredients'])), FOON.nodes[FU_obj_key[0]]['ingredients'], ingpose_list):
                    Tree.tree.nodes[node]['obj_list'].update({ing[1]:pos})
                    obj_pos_dic[ing[1]]  = [ingpose_list[i][-1][:3, 3], ingpose_list[i][-1][:3, :3]]
            Tree.tree.nodes[node]['obj_pos_dic'] = copy.deepcopy(obj_pos_dic)
            # Ms.animation(hand_name, model, conf_list, jawwidth_list, objpose_list, obstacle_list)
            # Ms.animation_dict(conf_list, jawwidth_list, objpose_list, objct_dic)
            return True
            
    def Place_checker(self, FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic):
        print('Place')
        out_node = list(FOON.successors(task[0]))
        FU_obj_key = [node for node in out_node if FOON.nodes[node]['label'] == task[1]['object']]
        FU_hnd_key = [node for node in out_node if '_H_' in node]
        if FOON.nodes[FU_hnd_key[0]]['label'] == 'right_hand':
            hand_name = 'rgt_hnd'
            other_hand = 'lft_hnd'
        else:
            hand_name = 'lft_hnd'
            other_hand = 'rgt_hnd'
        parent_node = Tree.get_parent(node)
        grasp_info = Tree.tree.nodes[parent_node]['grasp_id']
        ###条件分岐で使用可能な配置場所を追加
        place = FOON.nodes[FU_obj_key[0]]['place']
        area = Tree.tree.nodes[node]['area']
        model = obj_model_dic[FOON.nodes[FU_obj_key[0]]['id']]
        obj_homomat_list = Tree.tree.nodes[parent_node]['obj_list'][FOON.nodes[FU_obj_key[0]]['id']]
        rotmat = Tree.tree.nodes[node]['rotmat']
        # model_copy = copy.deepcopy(model)
        # model_copy.set_pos(area[1])
        # model_copy.set_rotmat(rotmat)
        goal_homomat_list = [rm.homomat_from_posrot(area[1], rotmat)]
        obstacle_list = [obj_model_dic[key] for key in obj_model_dic.keys() if FOON.nodes[FU_obj_key[0]]['id'] != key and '_F_'not in key]
        # Ms.visual_obj(obstacle_list)
        if FOON.nodes[FU_obj_key[0]]['type'] == 'ingredients':
            # Ms.visual_obj(obstacle_list+[model])
            container = [obj_model_dic[key] for key in obj_model_dic.keys() if key == FOON.nodes[FU_obj_key[0]]['container'][1]]
            obstacle_list = [obj_model_dic[key] for key in obj_model_dic.keys() if key != FOON.nodes[FU_obj_key[0]]['container'][1] and FOON.nodes[FU_obj_key[0]]['id'] != key]
            pos = container[0].get_pos() + np.array([0, 0, 0.01])
            goal_homomat_list = [rm.homomat_from_posrot(pos, rotmat)]
            conf_list, jawwidth_list, objpose_list = Ms.place_motion(Tree.tree.nodes[parent_node]['jawwidth_list'][hand_name][-1], Ms.robot_s.get_jnt_values(hand_name), hand_name, model, grasp_info, goal_homomat_list, obstacle_list=obstacle_list, toggle_sphere=False, toggle_gripper=False)
            obstacle_list += [container[0]]
        else:
            if FOON.nodes[FU_obj_key[0]]['ingredients'] != [['', '']] and FOON.nodes[FU_obj_key[0]]['ingredients'] != ['', '']:
                model_list = [model]
                for ing in FOON.nodes[FU_obj_key[0]]['ingredients']:
                    if ing[1] in obj_model_dic.keys():
                        model_list.append(obj_model_dic[ing[1]])
                if len(model_list) == 1:
                    conf_list, jawwidth_list, objpose_list = Ms.place_motion(Tree.tree.nodes[parent_node]['jawwidth_list'][hand_name][-1], Ms.robot_s.get_jnt_values(hand_name), hand_name, model, grasp_info, goal_homomat_list, obstacle_list=obstacle_list, toggle_sphere=False, toggle_gripper=False, toggle_obj=False)
                else:
                    conf_list, jawwidth_list, objpose_list, ingpose_list = Ms.place_motion(Tree.tree.nodes[parent_node]['jawwidth_list'][hand_name][-1], Ms.robot_s.get_jnt_values(hand_name), hand_name, model_list, grasp_info, goal_homomat_list, obstacle_list=obstacle_list, toggle_sphere=False, toggle_gripper=False, toggle_obj=False)
            else:
                conf_list, jawwidth_list, objpose_list = Ms.place_motion(Tree.tree.nodes[parent_node]['jawwidth_list'][hand_name][-1], Ms.robot_s.get_jnt_values(hand_name), hand_name, model, grasp_info, goal_homomat_list, obstacle_list=obstacle_list, toggle_sphere=False, toggle_gripper=False, toggle_obj=False)
        obj_list = obstacle_list + [model]
        # Ms.visual_obj(obj_list)
        if conf_list is None:
            print('配置計画失敗')
            Ms.gen_model.detach()
            Tree.remove_node_and_descendants(node)
            return False
        else:
            print('配置計画成功')
            obj_pos_dic[FOON.nodes[FU_obj_key[0]]['id']] = [objpose_list[-1][:3, 3], objpose_list[-1][:3, :3]]
            Tree.tree.nodes[node]['available_area'] = copy.deepcopy(available_area)
            Tree.tree.nodes[node]['EG'] = EG
            Tree.tree.nodes[node]['conf_list'] = {hand_name:conf_list, other_hand:[Ms.robot_s.get_jnt_values(other_hand) for i in range(len(conf_list))]}
            Tree.tree.nodes[node]['jawwidth_list'] = {hand_name:jawwidth_list, other_hand:[Ms.robot_s.hnd_dict[other_hand].jawwidth_rng[1] for i in range(len(jawwidth_list))]}
            Tree.tree.nodes[node]['obj_list'] = {FOON.nodes[FU_obj_key[0]]['id']:objpose_list}
            if FOON.nodes[FU_obj_key[0]]['ingredients'] != [['', '']] and FOON.nodes[FU_obj_key[0]]['ingredients'] != ['', ''] and len(model_list) > 1:
                for i, ing, pos in zip(range(len(FOON.nodes[FU_obj_key[0]]['ingredients'])), FOON.nodes[FU_obj_key[0]]['ingredients'], ingpose_list):
                    Tree.tree.nodes[node]['obj_list'].update({ing[1]:pos})
                    obj_pos_dic[ing[1]]  = [ingpose_list[i][-1][:3, 3], ingpose_list[i][-1][:3, :3]]
            Tree.tree.nodes[node]['obj_pos_dic'] = copy.deepcopy(obj_pos_dic)
            # Ms.visual_obj(obj_list)
            # Ms.animation(hand_name, model, conf_list, jawwidth_list, objpose_list, obstacle_list)
            return True
        
    def Cook_checker(self, FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic):
        print('Cook')
        out_node = list(FOON.predecessors(task[0]))
        FU_obj_key = [node for node in out_node if FOON.nodes[node]['label'] == 'stove']
        FU_hnd_key = [node for node in out_node if '_H_' in node]
        if FOON.nodes[FU_hnd_key[0]]['label'] == 'right_hand':
            hand_name = 'rgt_hnd'
            other_hand = 'lft_hnd'
        else:
            hand_name = 'lft_hnd'
            other_hand = 'rgt_hnd'
        grasp_info = Tree.tree.nodes[node]['grasp_id']
        ###条件分岐で使用可能な配置場所を追加
        place = FOON.nodes[FU_obj_key[0]]['place']
        area = EG.nodes[FOON.nodes[FU_obj_key[0]]['id']]['area']
        model = obj_model_dic[FOON.nodes[FU_obj_key[0]]['id']]
        goal_homomat_list = [model.get_homomat()]
        obstacle_list = [obj_model_dic[key] for key in obj_model_dic.keys() if FOON.nodes[FU_obj_key[0]]['id'] != key]
        obstacle_list = []
        conf_list, jawwidth_list, objpose_list = Ms.Cook_motion(hand_name, model, Ms.robot_s.get_jnt_values(hand_name), Ms.robot_s.get_jnt_values(hand_name), grasp_info, goal_homomat_list, obstacle_list=obstacle_list, toggle_grasp=False, toggle_sphere=False)
        obj_list = obstacle_list + [model]
        # Ms.visual_obj(obj_list)
        if conf_list is None:
            print('cook計画失敗')
            Ms.gen_model.detach()
            Tree.remove_node_and_descendants(node)
            return False
        else:
            print('cook計画成功')
            obj_pos_dic[FOON.nodes[FU_obj_key[0]]['id']] = [objpose_list[-1][:3, 3], objpose_list[-1][:3, :3]]
            Tree.tree.nodes[node]['available_area'] = copy.deepcopy(available_area)
            Tree.tree.nodes[node]['EG'] = EG
            Tree.tree.nodes[node]['conf_list'] = {hand_name:conf_list, other_hand:[Ms.robot_s.get_jnt_values(other_hand) for i in range(len(conf_list))]}
            Tree.tree.nodes[node]['jawwidth_list'] = {hand_name:jawwidth_list, other_hand:[Ms.robot_s.hnd_dict[other_hand].jawwidth_rng[1] for i in range(len(jawwidth_list))]}
            Tree.tree.nodes[node]['obj_list'] = {FOON.nodes[FU_obj_key[0]]['id']:objpose_list}
            Tree.tree.nodes[node]['obj_pos_dic'] = copy.deepcopy(obj_pos_dic)
            # Ms.animation(hand_name, model, conf_list, jawwidth_list, objpose_list, obstacle_list)
            # Ms.animation_dict(conf_list, jawwidth_list, objpose_list, objct_dic)
            return True    
    
    def Cut_checker(self, FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic, num_cuts=5, cut_range=0.01):
        ###FOONからIDを検索
        print('Cut')
        out_node = list(FOON.predecessors(task[0]))
        FU_container_key = [node for node in out_node if FOON.nodes[node]['label'] == 'cutting board']
        FU_knife_key = [node for node in out_node if FOON.nodes[node]['label'] == 'knife']
        FU_hnd_key = [node for node in out_node if '_H_' in node]
        
        ###ハンドの検索
        if FOON.nodes[FU_hnd_key[0]]['label'] == 'right_hand':
            hand_name = 'rgt_hnd'
            other_hand = 'lft_hnd'
        else:
            hand_name = 'lft_hnd'
            other_hand = 'rgt_hnd'
            
        ###条件分岐で使用可能な配置場所を追加
        parent_node = Tree.get_parent(node)
        grasp_info = Tree.tree.nodes[parent_node]['grasp_id']
        rotmat = Tree.tree.nodes[node]['rotmat']    #knifeのゴールの姿勢
        board_model = obj_model_dic[FOON.nodes[FU_container_key[0]]['id']]    #まな板のモデル
        knife_model = obj_model_dic[FOON.nodes[FU_knife_key[0]]['id']]    #まな板のモデル
        obstacle_list = [obj_model_dic[key] for key in obj_model_dic.keys() if FOON.nodes[FU_knife_key[0]]['id'] != key and '_F_' not in key]

        conf_list, jawwidth_list, objpose_list = Ms.Cut_motion(hand_name, board_model, knife_model, rotmat, Ms.robot_s.get_jnt_values(hand_name), Ms.robot_s.get_jnt_values(hand_name), grasp_info, Tree.tree.nodes[parent_node]['jawwidth_list'][hand_name][-1], obstacle_list=obstacle_list, toggle_gripper=False, toggle_sphere=False, toggle_goal_pos=False)
        obj_list = obstacle_list + [board_model, knife_model]
        # Ms.visual_obj(obj_list)
        if conf_list is None:
            print('Cut計画失敗')
            Ms.gen_model.detach()
            Tree.remove_node_and_descendants(node)
            return False
        else:
            print('Cut計画成功')
            obj_pos_dic[FOON.nodes[FU_knife_key[0]]['id']] = [objpose_list[-1][:3, 3], objpose_list[-1][:3, :3]]
            Tree.tree.nodes[node]['available_area'] = copy.deepcopy(available_area)
            Tree.tree.nodes[node]['EG'] = EG
            Tree.tree.nodes[node]['conf_list'] = {hand_name:conf_list, other_hand:[Ms.robot_s.get_jnt_values(other_hand) for i in range(len(conf_list))]}
            Tree.tree.nodes[node]['jawwidth_list'] = {hand_name:jawwidth_list, other_hand:[Ms.robot_s.hnd_dict[other_hand].jawwidth_rng[1] for i in range(len(jawwidth_list))]}
            Tree.tree.nodes[node]['obj_list'] = {FOON.nodes[FU_knife_key[0]]['id']:objpose_list}
            Tree.tree.nodes[node]['obj_pos_dic'] = copy.deepcopy(obj_pos_dic)
            Tree.tree.nodes[node]['grasp_id'] = grasp_info
            # Ms.animation(hand_name, model, conf_list, jawwidth_list, objpose_list, obstacle_list)
            # Ms.animation_dict(conf_list, jawwidth_list, objpose_list, objct_dic)
            return True
        
    def Pour_checker(self, FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic, num_cuts=5, cut_range=0.01):
        ###FOONからIDを検索
        print('Pour')

        out_node = list(FOON.successors(task[0]))
        source_container_key = [node for node in out_node if '_C_' in node and FOON.nodes[node]['ingredients'] == [['', '']]]
        target_container_key = [node for node in out_node if '_C_' in  node and FOON.nodes[node]['ingredients'] != [['', '']]]
        FU_hnd_key = [node for node in out_node if '_H_' in node]
        
        in_node = list(FOON.predecessors(task[0]))
        source_container_in_key = [node for node in in_node if '_C_' in node and FOON.nodes[node]['id'] == FOON.nodes[source_container_key[0]]['id']]
        
        ###ハンドの検索
        if FOON.nodes[FU_hnd_key[0]]['label'] == 'right_hand':
            hand_name = 'rgt_hnd'
            other_hand = 'lft_hnd'
        else:
            hand_name = 'lft_hnd'
            other_hand = 'rgt_hnd'
            
        ###条件分岐で使用可能な配置場所を追加
        parent_node = Tree.get_parent(node)
        grasp_info = Tree.tree.nodes[parent_node]['grasp_id']
        rotmat = Tree.tree.nodes[node]['rotmat']    #knifeのゴールの姿勢
        source_container = obj_model_dic[FOON.nodes[source_container_key[0]]['id']]
        target_container = obj_model_dic[FOON.nodes[target_container_key[0]]['id']]
        obstacle_list = [obj_model_dic[key] for key in obj_model_dic.keys() if FOON.nodes[source_container_key[0]]['id'] != key and '_F_' not in key]
        if FOON.nodes[source_container_in_key[0]]['ingredients'] != [['', '']] and FOON.nodes[source_container_in_key[0]]['ingredients'] != ['', '']:
            model_list = [source_container]
            for ing in FOON.nodes[source_container_in_key[0]]['ingredients']:
                if ing[1] in obj_model_dic.keys():
                    model_list.append(obj_model_dic[ing[1]])
            if len(model_list) == 1:
                conf_list, jawwidth_list, objpose_list = Ms.Pour_motion(hand_name, source_container, target_container, rotmat, Ms.robot_s.get_jnt_values(hand_name), Ms.robot_s.get_jnt_values(hand_name), grasp_info, Tree.tree.nodes[parent_node]['jawwidth_list'][hand_name][-1], obstacle_list=obstacle_list, toggle_gripper=False, toggle_sphere=False, toggle_goal_pos=False)
            else:
                conf_list, jawwidth_list, objpose_list, ingpose_list = Ms.Pour_motion(hand_name, model_list, target_container, rotmat, Ms.robot_s.get_jnt_values(hand_name), Ms.robot_s.get_jnt_values(hand_name), grasp_info, Tree.tree.nodes[parent_node]['jawwidth_list'][hand_name][-1], obstacle_list=obstacle_list, toggle_gripper=False, toggle_sphere=False, toggle_goal_pos=False)
        else:
            conf_list, jawwidth_list, objpose_list = Ms.Pour_motion(hand_name, source_container, target_container, rotmat, Ms.robot_s.get_jnt_values(hand_name), Ms.robot_s.get_jnt_values(hand_name), grasp_info, Tree.tree.nodes[parent_node]['jawwidth_list'][hand_name][-1], obstacle_list=obstacle_list, toggle_gripper=False, toggle_sphere=False, toggle_goal_pos=False)
            obj_list = obstacle_list + [source_container, target_container]
        # Ms.visual_obj(obj_list)
        if conf_list is None:
            print('Pour計画失敗')
            Ms.gen_model.detach()
            Tree.remove_node_and_descendants(node)
            return False
        else:
            print('Pour計画成功')
            obj_pos_dic[FOON.nodes[source_container_key[0]]['id']] = [objpose_list[-1][:3, 3], objpose_list[-1][:3, :3]]
            Tree.tree.nodes[node]['available_area'] = copy.deepcopy(available_area)
            Tree.tree.nodes[node]['EG'] = EG
            Tree.tree.nodes[node]['conf_list'] = {hand_name:conf_list, other_hand:[Ms.robot_s.get_jnt_values(other_hand) for i in range(len(conf_list))]}
            Tree.tree.nodes[node]['jawwidth_list'] = {hand_name:jawwidth_list, other_hand:[Ms.robot_s.hnd_dict[other_hand].jawwidth_rng[1] for i in range(len(jawwidth_list))]}
            Tree.tree.nodes[node]['obj_list'] = {FOON.nodes[source_container_key[0]]['id']:objpose_list}
            if FOON.nodes[source_container_in_key[0]]['ingredients'] != [['', '']] and FOON.nodes[source_container_in_key[0]]['ingredients'] != ['', ''] and len(model_list) > 1:
                for i, ing, pos in zip(range(len(FOON.nodes[source_container_in_key[0]]['ingredients'])), FOON.nodes[source_container_in_key[0]]['ingredients'], ingpose_list):
                    Tree.tree.nodes[node]['obj_list'].update({ing[1]:pos})
                    obj_pos_dic[ing[1]]  = [ingpose_list[i][-1][:3, 3], ingpose_list[i][-1][:3, :3]]
            Tree.tree.nodes[node]['obj_pos_dic'] = copy.deepcopy(obj_pos_dic)
            Tree.tree.nodes[node]['grasp_id'] = grasp_info
            # Ms.animation(hand_name, model, conf_list, jawwidth_list, objpose_list, obstacle_list)
            # Ms.animation_dict(conf_list, jawwidth_list, objpose_list, objct_dic)
            return True
        
    def Mix_checker(self, FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic, num_cuts=5, cut_range=0.01):
        ###FOONからIDを検索
        print('Mix')
        out_node = list(FOON.successors(task[0]))
        spatula_key = [node for node in out_node if FOON.nodes[node]['label'] == 'spatula']
        target_container_key = [node for node in out_node if '_C_' in  node]
        FU_hnd_key = [node for node in out_node if '_H_' in node]
        
        ###ハンドの検索
        if FOON.nodes[FU_hnd_key[0]]['label'] == 'right_hand':
            hand_name = 'rgt_hnd'
            other_hand = 'lft_hnd'
        else:
            hand_name = 'lft_hnd'
            other_hand = 'rgt_hnd'
            
        ###条件分岐で使用可能な配置場所を追加
        parent_node = Tree.get_parent(node)
        grasp_info = Tree.tree.nodes[parent_node]['grasp_id']
        rotmat = Tree.tree.nodes[node]['rotmat']    #spatulaの姿勢
        spatula_model = obj_model_dic[FOON.nodes[spatula_key[0]]['id']]
        target_container = obj_model_dic[FOON.nodes[target_container_key[0]]['id']]
        obstacle_list = [obj_model_dic[key] for key in obj_model_dic.keys() if FOON.nodes[spatula_key[0]]['id'] != key and '_F_' not in key]

        conf_list, jawwidth_list, objpose_list = Ms.Mix_motion(hand_name, spatula_model, target_container, rotmat, Ms.robot_s.get_jnt_values(hand_name), Ms.robot_s.get_jnt_values(hand_name), grasp_info, Tree.tree.nodes[parent_node]['jawwidth_list'][hand_name][-1], obstacle_list=obstacle_list, toggle_gripper=False, toggle_sphere=False, toggle_goal_pos=False)
        obj_list = obstacle_list + [spatula_model, target_container]
        # Ms.visual_obj(obj_list)
        if conf_list is None:
            print('Pour計画失敗')
            Ms.gen_model.detach()
            Tree.remove_node_and_descendants(node)
            return False
        else:
            print('Pour計画成功')
            obj_pos_dic[FOON.nodes[spatula_key[0]]['id']] = [objpose_list[-1][:3, 3], objpose_list[-1][:3, :3]]
            Tree.tree.nodes[node]['available_area'] = copy.deepcopy(available_area)
            Tree.tree.nodes[node]['EG'] = EG
            Tree.tree.nodes[node]['conf_list'] = {hand_name:conf_list, other_hand:[Ms.robot_s.get_jnt_values(other_hand) for i in range(len(conf_list))]}
            Tree.tree.nodes[node]['jawwidth_list'] = {hand_name:jawwidth_list, other_hand:[Ms.robot_s.hnd_dict[other_hand].jawwidth_rng[1] for i in range(len(jawwidth_list))]}
            Tree.tree.nodes[node]['obj_list'] = {FOON.nodes[spatula_key[0]]['id']:objpose_list}
            Tree.tree.nodes[node]['obj_pos_dic'] = copy.deepcopy(obj_pos_dic)
            Tree.tree.nodes[node]['grasp_id'] = grasp_info
            # Ms.animation(hand_name, model, conf_list, jawwidth_list, objpose_list, obstacle_list)
            # Ms.animation_dict(conf_list, jawwidth_list, objpose_list, objct_dic)
            return True
    
    def motion_planning(self, FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic):
        action = task[1]['label']
        print(action)
        if action == 'Pic':
            result = self.Pic_checker(FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic)
        elif action == 'Place':
            result = self.Place_checker(FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic)
        elif action == 'Cook':
            result = self.Cook_checker(FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic)
        elif action == 'Cut':
            result = self.Cut_checker(FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic)
        elif action == 'Pour':
            result = self.Pour_checker(FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic)
        elif action == 'Mix':
            result = self.Mix_checker(FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic)
        else:
            input('未実装です')
            result = False
        return result
        
        
    def main(self, Tree, task_num, task, FOON, save_folder, save_file):
        """ノードから環境を取り出し実行できるか確認する関数です。
        1. treeから実行可否判定するノードを取り出す
        for ノード
            2. 親ノードから環境の取り出し
            3. 環境からnodeの動作計画
            4. 動作実行可能であればノードに追加
            5. 動作実行不可能であればノードを削除
        """
        c=0
        "1. treeから実行可否判定するノードを取り出す"
        target_nodes = self.get_target_node(Tree.tree, task_num)

        random.shuffle(target_nodes)
        for i, node in enumerate(target_nodes):
            print(f'=========={i}/{len(target_nodes)}=============')
            "2. 親ノードから環境の取り出し"
            EG, available_area, obj_model_dic, Ms, obj_pos_dic = self.get_environment_from_parent_node(node, Tree)
            
            "3. 動作計画"
            result = self.motion_planning(FOON, task, EG, available_area, obj_model_dic, node, Ms, Tree, obj_pos_dic)
            
            if result == True:
                return [node]
            Fm.save_pickle_file(save_folder, save_file, Tree.tree)
            del Ms
        del self.OMCM
        return []
            
        
 
if __name__ == '__main__':
    base = wd.World(cam_pos=[5,0,3],lookat_pos=[0,0,1])
    EC = ExecutionChecker(base)