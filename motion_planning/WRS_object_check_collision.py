# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 03:22:09 2024

@author: user
"""
import sys
import File_management as Fm
import visualization.panda.world as wd
import modeling.geometric_model as gm
import modeling.collision_model as cm
import grasping.planning.antipodal as gpa
import robot_sim.end_effectors.gripper.robotiq85.robotiq85 as robotiq
import basis.robot_math as rm
import math
import numpy as np
import robot_sim.robots.ur3_dual.ur3_dual as ur
import wrs.manipulation.pick_place_planner as ppp
from panda3d.core import KeyboardButton
import time

class Collision_Checker:
    def __init__(self, base, EG, ur):
        self.base = base
        self.gripper_s = robotiq.Robotiq85()
        self.ground = cm.gen_box(extent=[5, 5, 1], rgba =[.57, .57, .5, .7])
        self.ground.set_pos(np.array ([0,0,-.5]))
        self.ground.attach_to(self.base)
        self.robot = ur
        # mesh = self.robot.gen_meshmodel()
        # mesh.attach_to(self.base)
        self.EG = EG
        self.obj_model_list = []
        self.PPP = ppp.PickPlacePlanner(self.robot, base)
        
    def set_object(self, obj_area):
        """stlファイルを入力するとオブジェクトを追加する"""
        keys = [o[0][1] for o in obj_area]
        obj_model_dic = {}
        for i, key in enumerate(keys):
            stl_path = self.EG.nodes[key]['stl_path']
            object_ = cm.CollisionModel(stl_path)
            object_.set_rgba([0.7, 0.7, 0.0, 1])
            object_.show_localframe()
            rotmat = rm.rotmat_from_axangle([1, 0, 0], 0)
            object_.set_rotmat(rotmat)
            object_.show_cdprimit()
            # object_.attach_to(self.base)
            self.obj_model_list.append(object_)
            program = f"obj_model_dic.update({key}=object_)"
            exec(program)
            # input(obj_model_dic)
        return obj_model_dic
    
    def set_obj_first_pos(self, obj_area, obj_model_dic, rotmat=np.eye(3)):
        area = [o[1][1][:-1] for o in obj_area]
        # input(obj_model_dic)
        obj_pos_dic = {}
        for i, key in enumerate(obj_model_dic.keys()):
            obj_model_dic[key].set_pos(area[i]+np.array([0, 0, 0.01]))
            obj_model_dic[key].set_rotmat(rotmat)
            obj_pos_dic[key] = [area[i]+np.array([0, 0, 0.01]), rotmat]
            # obj_model_dic[key].attach_to(self.base)
            # self.base.run()
        return obj_model_dic, obj_pos_dic
    
    def set_obj_pos(self, obj_model, pos, rotmat):
        obj_model.set_pos(pos+np.array([0, 0, 0.01]))
        obj_model.set_rotmat(rotmat)
    
    def check_object_collision(self, obj, obstacle_model_dic):
        obstacle_list = [obstacle_model_dic[key] for key in obstacle_model_dic.keys() if obstacle_model_dic[key] != obj]
        # self.visual_obj(obstacle_list)
        check = obj.is_mcdwith(obstacle_list)
        return check
    
    def visual_obj(self, model_list):
        for model in model_list:
            model.set_rgba([0, 0, 1, 1])
            model.attach_to(self.base)
        self.base.run()
        for model in model_list:
            model.set_rgba([1, 1, 1, 1])
    
    def setup_check_object_collision(self, object_dic):
        for key in object_dic.keys():
            obstacle_list = [object_dic[item] for item in object_dic.keys() if object_dic[item] != object_dic[key]]
            check = object_dic[key].is_mcdwith(obstacle_list)
            if check:
                break
        # check, contact_point = self.robot.is_collided(obstacle_list=self.obj_model_list, toggle_contact_points=True)
        if check:
            # self.base.run()
            for obj in obstacle_list:
                obj.detach()
            # self.base.run()
            return check
        return check

    # def robot_ik(self, area, grasp_info_path, arm, obj_model_dic, rotmat=np.eye(3)):
    #     self.set_obj_first_pos(area, obj_model_dic, rotmat)
    #     model_list = []
    #     for i, key in enumerate(obj_model_dic.keys()):
    #         print(f"========================{i}=======================")
    #         obj = obj_model_dic[key]
    #         togle = False
    #         obstacle_list = [obj_model_dic[item] for item in obj_model_dic.keys() if item != key]
    #         grasp_info_list = Fm.load_pickle_file(grasp_info_path[i])
    #         for grasp_info in grasp_info_list:
    #             jaw_width , jaw_center_pos , jaw_center_rotmat , hnd_pos , hnd_rotmat = grasp_info
    #             gl_jaw_center_pos = obj.get_pos()+obj.get_rotmat().dot(jaw_center_pos)
    #             gl_jaw_center_rotmat = obj.get_rotmat().dot(jaw_center_rotmat)
    #             gl_hnd_pos = obj.get_pos() + obj.get_rotmat().dot(hnd_pos) # グ リッ パ の 位 置 姿 勢 の 変換
    #             gl_hnd_rotmat = obj.get_rotmat().dot(hnd_rotmat)
    #             self.gripper_s.fix_to(gl_hnd_pos, gl_hnd_rotmat)
    #             if not self.gripper_s.is_mesh_collided(obstacle_list):
    #                 jnt_values = self.robot.ik(arm, # 逆 運 動 学 の 計 算
    #                                         tgt_pos=gl_jaw_center_pos ,
    #                                         tgt_rotmat=gl_jaw_center_rotmat)
    #                 if jnt_values is None: # 逆 運 動 学 が 解 け な け れ ば
    #                     # print('IKが解けませんでした')
    #                     togle = False
    #                 else: # 逆 運 動 学 が 解 け ば
    #                     self.robot.fk(arm, jnt_values=jnt_values)
    #                     if self.robot.is_collided(obstacle_list):
    #                         # print('ロボット自身で衝突があります')
    #                         togle = False
    #                     else:
    #                         # model_list.append([self.gripper_s.gen_meshmodel(), self.robot.gen_meshmodel()])
    #                         # model_list[-1][0].attach_to(self.base)
    #                         # model_list[-1][1].attach_to(self.base)
    #                         togle = True
    #                         print("*******成功********")
    #                         break
    #             else: # 地 面 と の 干 渉 が あ れ ば
    #                 # print('オブジェクトと干渉があります')
    #                 togle = False
                    
    #         if togle == False:
    #             # for model in model_list:
    #             #     model[0].detach()
    #             #     model[1].detach()
    #             #     model_list.clear()0
    #             return togle
    #     return togle
    
    def robot_ik(self, area, grasp_info_path, arm, obj_model_dic, rotmat=np.eye(3)):
        obj_model_dic, obj_pos_dic = self.set_obj_first_pos(area, obj_model_dic, rotmat)
        model_list = []
        jnt_bk = self.robot.get_jnt_values(arm)
        for i, key in enumerate(obj_model_dic.keys()):
            print(f"========================{i}=======================")
            obj = obj_model_dic[key]
            togle = False
            obstacle_list = [obj_model_dic[item] for item in obj_model_dic.keys() if item != key]
            grasp_info_list = Fm.load_pickle_file(grasp_info_path[i])
            goal_homomat_list = [obj.get_homomat()]
            # self.visual_obj(obstacle_list)
            conf_list, jaw_list, obj_list = self.Pic_motion(arm, obj, self.robot.get_jnt_values(arm), self.robot.get_jnt_values(arm), grasp_info_list, goal_homomat_list, obstacle_list)    
            self.robot.fk(arm, jnt_bk)
            if conf_list is None:
                print('Picモーションを生成できませんでした')
                return False
            else:
                print('Picモーションを生成できました')
                # self.animation(arm, obj, conf_list, jaw_list, obj_list, obstacle_list)
        print('成功')
        return True
    
       
    def check_graspability(self, ave_object_area, save_folder, arm, file_path, obj_model_dic, rotmat=np.eye(3)):
        num = 0
        result = []
        for area in ave_object_area:
            if num%10 == 0 and num != 0:
                print(f'{Fm.get_current_time()}-------------------{num}/{len(ave_object_area)}---------------------------')
                # self.base.run()
            keys = [o[0][1] for o in area]
            grasp_info_list = [self.EG.nodes[key]['grasp_info_list'] for key in keys]
            print(num)
            # self.visual_obj([obj_model_dic[key] for key in obj_model_dic.keys()])
            togle = self.robot_ik(area, grasp_info_list, arm, obj_model_dic, rotmat)
            print(f'=============================================成功配置{len(result)}:探索回数{num}/500=======================================')
            if togle:
                result.append(area)
                # for key in obj_model_dic.keys():
                #     obj_model_dic[key].attach_to(self.base)
                # self.base.run()
                # for key in obj_model_dic.keys():
                #     obj_model_dic[key].detach()
                print(f'=============================================成功配置{len(result)}=======================================')
                if len(result) == 10:
                    break
            num += 1
            Fm.save_pickle_file(save_folder, file_path, result)
        return result
    
    def Pic_motion(self, 
                   hnd_name, 
                   objcm, 
                   start_conf, 
                   end_conf, 
                   grasp_info_list, 
                   goal_homomat_list,
                   obstacle_list,
                   grasp_id = 0):
        ###パラメータ設定
        approach_direction_list=[np.array([0, 0, -1])] * len(goal_homomat_list)
        approach_distance_list=[.05] * len(goal_homomat_list)
        depart_direction_list=[np.array([0, 0, 1])] * len(goal_homomat_list)
        depart_distance_list=[.05] * len(goal_homomat_list)
        approach_jawwidth=None
        depart_jawwidth=None
        ad_granularity=.007
        use_rrt=True
        use_incremental=False
        ###パラメータ設定
        
        
        ###把持位置まで持ってくるモーション
        if approach_jawwidth is None:
            approach_jawwidth = self.robot.hnd_dict[hnd_name].jawwidth_rng[1]
        if depart_jawwidth is None:
            depart_jawwidth = self.robot.hnd_dict[hnd_name].jawwidth_rng[1]
        first_goal_pos = goal_homomat_list[0][:3, 3]
        first_goal_rotmat = goal_homomat_list[0][:3, :3]
        
        for grasp_num, grasp_info in enumerate(grasp_info_list[grasp_id:]):
            jaw_width, jaw_center_pos, jaw_center_rotmat, hnd_pos, hnd_rotmat = grasp_info
            # approach
            first_jaw_center_pos = first_goal_rotmat.dot(jaw_center_pos) + first_goal_pos
            first_jaw_center_rotmat = first_goal_rotmat.dot(jaw_center_rotmat)
            # objcm as an obstacle
            objcm_copy = objcm.copy()
            objcm_copy.set_pos(first_goal_pos)
            objcm_copy.set_rotmat(first_goal_rotmat)
            conf_list_approach, jawwidthlist_approach = \
                self.PPP.gen_approach_motion(component_name=hnd_name,
                                         goal_tcp_pos=first_jaw_center_pos,
                                         goal_tcp_rotmat=first_jaw_center_rotmat,
                                         start_conf=start_conf,
                                         approach_direction=approach_direction_list[0],
                                         approach_distance=approach_distance_list[0],
                                         approach_jawwidth=approach_jawwidth,
                                         granularity=ad_granularity,
                                         obstacle_list=obstacle_list,
                                         object_list=[objcm_copy],
                                         seed_jnt_values=start_conf,
                                         toggle_sphere=False)
            if conf_list_approach is None:
                print("Cannot generate the pick motion!")
                continue
            ###把持位置まで持ってくるモーション
            
            ###把持して持ち上げるモーション
            conf_list_middle, jawwidthlist_middle, objpose_list_middle = \
                self.hold_motion(jawwidthlist_approach[-1],
                                conf_list_approach[-1],
                                hand_name=hnd_name,
                                objcm=objcm,
                                grasp_info=grasp_info,
                                obj_pose_list=goal_homomat_list,
                                depart_direction_list=depart_direction_list,
                                approach_direction_list=approach_direction_list,
                                depart_distance_list=depart_distance_list,
                                approach_distance_list=approach_distance_list,
                                ad_granularity=.003,
                                use_rrt=use_rrt,
                                obstacle_list=obstacle_list,
                                seed_jnt_values=conf_list_approach[-1])
            if conf_list_middle is None:
                print("Cannot generate the middle motion!")
                continue
            ###把持して持ち上げるモーション
            
            objpose_list_approach = self.PPP.gen_object_motion(component_name=hnd_name,
                                                           conf_list=jawwidthlist_approach,
                                                           obj_pos=first_goal_pos,
                                                           obj_rotmat=first_goal_rotmat,
                                                           type='absolute')
            return conf_list_approach+conf_list_middle, jawwidthlist_approach+jawwidthlist_middle, objpose_list_approach+objpose_list_middle
        return None, None, None
        
    def hold_motion(self,
                    jawwidth_bk,
                    jnt_values_bk,
                    hand_name,
                    objcm,
                    grasp_info,
                    obj_pose_list,
                    depart_direction_list,
                    depart_distance_list,
                    approach_direction_list,
                    approach_distance_list,
                    ad_granularity=.007,
                    use_rrt=True,
                    obstacle_list=[],
                    seed_jnt_values=None):
        jnt_values_bk = jnt_values_bk
        jawwidth_bk = jawwidth_bk
        # final
        conf_list = []
        jawwidthlist = []
        objpose_list = []
        # hold object
        jaw_width, jaw_center_pos, jaw_center_rotmat, hnd_pos, hnd_rotmat = grasp_info
        first_obj_pos = obj_pose_list[0][:3, 3]
        first_obj_rotmat = obj_pose_list[0][:3, :3]
        first_jaw_center_pos = first_obj_rotmat.dot(jaw_center_pos) + first_obj_pos
        first_jaw_center_rotmat = first_obj_rotmat.dot(jaw_center_rotmat)
        first_conf = self.robot.ik(hand_name,
                                     first_jaw_center_pos,
                                     first_jaw_center_rotmat,
                                     seed_jnt_values=seed_jnt_values)
        if first_conf is None:
            print("Cannot solve the ik at the first grasping pose!")
            return None, None, None
        self.robot.fk(component_name=hand_name, jnt_values=first_conf)
        # set a copy of the object to the start pose, hold the object, and move it to goal object pose
        objcm_copy = objcm.copy()
        objcm_copy.set_pos(first_obj_pos)
        objcm_copy.set_rotmat(first_obj_rotmat)
        rel_obj_pos, rel_obj_rotmat = self.robot.hold(objcm_copy, jaw_width,  hand_name)
        seed_conf = first_conf

        # get start and goal object poses
        start_obj_pos = obj_pose_list[0][:3, 3]
        start_obj_rotmat = obj_pose_list[0][:3, :3]
        
        # transform grasps
        start_jaw_center_pos = start_obj_rotmat.dot(jaw_center_pos) + start_obj_pos
        start_jaw_center_rotmat = start_obj_rotmat.dot(jaw_center_rotmat)
        
        depart_direction = depart_direction_list[0]
        if depart_direction is None:
            depart_direction = -start_jaw_center_rotmat[:, 2]
        depart_distance = depart_distance_list[0]
        if depart_distance is None:
            depart_distance = 0

        # depart linear
        conf_list_depart = self.PPP.inik_slvr.gen_rel_linear_motion(component_name=hand_name,
                                                                goal_tcp_pos=start_jaw_center_pos,
                                                                goal_tcp_rotmat=start_jaw_center_rotmat,
                                                                direction=depart_direction,
                                                                distance=depart_distance,
                                                                obstacle_list=obstacle_list,
                                                                granularity=ad_granularity,
                                                                seed_jnt_values=seed_conf,
                                                                type='source')
        if conf_list_depart is None:
            print(f"Cannot generate the linear part of the holding depart motion!")
            self.robot.release(hand_name, objcm_copy, jawwidth_bk)
            self.robot.fk(component_name=hand_name, jnt_values=jnt_values_bk)
            return None, None, None
        jawwidthlist_depart = self.PPP.gen_jawwidth_motion(conf_list_depart, jaw_width)
        objpose_list_depart = self.PPP.gen_object_motion(component_name=hand_name,
                                                     conf_list=conf_list_depart,
                                                     obj_pos=rel_obj_pos,
                                                     obj_rotmat=rel_obj_rotmat,
                                                     type='relative')
        self.robot.release(hand_name, objcm_copy, jawwidth_bk)
        self.robot.fk(component_name=hand_name, jnt_values=jnt_values_bk)
        
        # input(f'{len(conf_list_depart)}, {len(jawwidthlist_depart)}, {len(objpose_list_depart)}')
        
        return conf_list_depart, jawwidthlist_depart, objpose_list_depart
    
    def animation(self, hand_name, objcm, conf_list, jawwidth_list, objpose_list, obstacle_list):
        
        robot_attached_list = []
        object_attached_list = []
        obstacle_attache_list = []
        counter = [0]
        task_name = "update"  # タスク名を変数に格納
    
        def detach_all_objects():
            # すべてのオブジェクトをデタッチする
            for robot_attached in robot_attached_list:
                robot_attached.detach()
            for object_attached in object_attached_list:
                object_attached.detach()
            for obstacle_attache in obstacle_attache_list:
                obstacle_attache.detach()
            robot_attached_list.clear()
            object_attached_list.clear()
            obstacle_attache_list.clear()

    
        def update(robot_s,
                   hand_name,
                   objcm,
                   robot_path,
                   jawwidth_path,
                   obj_path,
                   robot_attached_list,
                   object_attached_list,
                   obstacle_list,
                   obstacle_attache_list,
                   counter,
                   task):
            
            if counter[0] >= len(robot_path):
                counter[0] = 0
            if len(robot_attached_list) != 0:
                detach_all_objects()
            pose = robot_path[counter[0]]
            robot_s.fk(hand_name, pose)
            robot_s.jaw_to(hand_name, jawwidth_path[counter[0]])
            robot_meshmodel = robot_s.gen_meshmodel()
            robot_meshmodel.attach_to(self.base)
            robot_attached_list.append(robot_meshmodel)
            obj_pose = obj_path[counter[0]]
            objb_copy = objcm.copy()
            objb_copy.set_homomat(obj_pose)
            objb_copy.attach_to(self.base)
            object_attached_list.append(objb_copy)
            for obs in obstacle_list:
                obs_copy = obs.copy()
                # obs_copy.attach_to(base)
                obstacle_attache_list.append(obs_copy)
            counter[0] += 1
    
            # Enterキーが押されたかチェック
            if self.base.mouseWatcherNode.is_button_down(KeyboardButton.control()):
                detach_all_objects()
                print("You pressed ctrl!")
                while True:
                    time.sleep(0.1)
                
            return task.again
    
        # タスクをスケジュール
        taskMgr.doMethodLater(0.01, update, task_name,
                              extraArgs=[self.robot,
                                         hand_name,
                                         objcm,
                                         conf_list,
                                         jawwidth_list,
                                         objpose_list,
                                         robot_attached_list,
                                         object_attached_list,
                                         obstacle_list,
                                         obstacle_attache_list,
                                         counter],
                              appendTask=True)
    
        # アニメーションを実行
        self.base.run()
        
        def stop_animation():
            taskMgr.remove(task_name)  # タスクを停止
            print("Animation stopped")
        
        stop_animation()
        
        
        
        