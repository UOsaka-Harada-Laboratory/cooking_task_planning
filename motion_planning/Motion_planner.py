# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 17:47:42 2024

@author: Shoichi
"""
import File_management as Fm
import random
import ObjectModelConfigManager
import basis.robot_math as rm
import itertools
import visualization.panda.world as wd
import Task_tree as Tt
import copy
import numpy as np
import math
import sys
import Execution_Checker
import Motion_storage
import sub_analyze_graph
import tracemalloc
import winsound

class MotionPrep():
    def __init__(self, base):
        print('start')
        self.base = base
        
    def set_stl(self, EG):
        """
        それぞれのオブジェクトノードにstl_pathの属性を追加
        入力
        EG:環境オブジェクトノード
        出力
        EG:環境オブジェクトノードにstl_pathの属性を追加
        """
        input('set')
        stl_object_key = [key for key in EG.nodes.keys() if '_C_' in key or '_T_' in key or '_M_' in key or '_F_' in key]
        path = Fm.get_current_path()
        for key in stl_object_key:
            if 'pinch_bowl' in EG.nodes[key]['label'] or 'cup' in EG.nodes[key]['label']:
                EG.nodes[key]['stl_path'] = fr'{path}\stl\mini_bowl_bowl.stl'
                EG.nodes[key]['grasp_info_list'] = fr'{path}\stl\grasp\mini_bowl_bowl2.pickle'
            elif 'tray' in EG.nodes[key]['label']:
                EG.nodes[key]['stl_path'] = fr'{path}\stl\bat.stl'
                EG.nodes[key]['grasp_info_list'] = fr'{path}\stl\grasp\bat2.pickle'
            elif 'bowl' in EG.nodes[key]['label']:
                EG.nodes[key]['stl_path'] = fr'{path}\stl\bowl.stl'
                EG.nodes[key]['grasp_info_list'] = fr'{path}\stl\grasp\bowl2.pickle'
            elif 'pan' in EG.nodes[key]['label']:
                EG.nodes[key]['stl_path'] = fr'{path}\stl\pan.stl'
                EG.nodes[key]['grasp_info_list'] = fr'{path}\stl\grasp\pan2.pickle'
            elif 'cutting board' in EG.nodes[key]['label']:
                EG.nodes[key]['stl_path'] = fr'{path}\stl\cutting_board.stl'
                EG.nodes[key]['grasp_info_list'] = fr'{path}\stl\grasp\cutting_board2.pickle'
            elif 'stove' in EG.nodes[key]['label']:
                EG.nodes[key]['stl_path'] = fr'{path}\stl\stove.stl'
                EG.nodes[key]['grasp_info_list'] = fr'{path}\stl\grasp\stove.pickle'
            elif 'knife' in EG.nodes[key]['label']:
                EG.nodes[key]['stl_path'] = fr'{path}\stl\knife.stl'
                EG.nodes[key]['grasp_info_list'] = fr'{path}\stl\grasp\knife2.pickle'
            elif 'spatula' in EG.nodes[key]['label']:
                EG.nodes[key]['stl_path'] = fr'{path}\stl\spatula.stl'
                EG.nodes[key]['grasp_info_list'] = fr'{path}\stl\grasp\spatula2.pickle'
            elif 'ingredients' in EG.nodes[key]['type'] and 'whole' in EG.nodes[key]['cutting_style']:
                if EG.nodes[key]['label'] == 'pork':
                    EG.nodes[key]['stl_path'] = fr'{path}\stl\pork.stl'
                elif EG.nodes[key]['label'] == 'onion':
                    EG.nodes[key]['stl_path'] = fr'{path}\stl\onion.stl'
                else:
                    EG.nodes[key]['stl_path'] = fr'{path}\stl\food.stl'
                EG.nodes[key]['grasp_info_list'] = fr'{path}\stl\grasp\food3.pickle'
            else:
                print(key)
                print(EG.nodes[key]['label'])
               
    def extract_placement_regions(self, placements, object_list, area_list, EG, rot, machine_area):
        num = 0
        object_area = []
        ave_object_area = []
        OMCM = ObjectModelConfigManager.ObjectModelConfigManager(self.base)
        for place in placements[::-1]:
            place = list(place)
            place.append(machine_area)
            print(f'{num}/{len(placements)}===残り:{len(placements)-num}')
            print(f'placement:{place}')
            num += 1
            for i, obj in enumerate(object_list):
                object_area.append([obj, area_list[place[i]]])
                
            if num == 1:
                set_obj_dic=OMCM.set_object(object_area, EG)
            set_obj_dic, obj_pos_dic = OMCM.set_objdic_pos(object_area, set_obj_dic, rot)
            
            if OMCM.setup_check_object_collision(set_obj_dic):
                print('衝突が発生')
                object_area = []
            else:
                print(f'配置可能:{object_area}')
                ave_object_area.append(object_area[:-1])
                object_area = []
                if len(ave_object_area) == 100:
                    break
                continue
            print(f'=============================配置可能エリア数：{len(ave_object_area)}=============================================')
            
        return ave_object_area
    
    def explore_all_placements(self, num_objects, num_cells):
        """
        num_objects個のオブジェクトをnum_cells個のマスに全て配置する方法を全探索する関数。
    
        :param num_objects: 配置するオブジェクトの数（例：8）
        :param num_cells: 配置するマスの数（例：20）
        :return: 配置方法のリスト（各配置方法は、オブジェクトを配置するマスのインデックスのリスト）
        """
        # オブジェクトを置くマスの組み合わせを全探索
        num = [cell[0] for cell in num_cells]
        return list(itertools.combinations(num, num_objects))
    
    def set_enviroment_object(self, EG, ave_area, save_folder, initial_placement_toggle = False):
        """
        環境オブジェクトの初期配置を決定する関数
        入力:
        EG:環境オブジェクト
        出力：
        EG_list:配置場所を追加したEGのリスト
        """
        
        "stlファイルのパスの設定"
        self.set_stl(EG)
        machine_num = len(ave_area)-1
        
        if initial_placement_toggle:
            all_area = [ [i, point] for i, point in enumerate(ave_area)]
            machine_object = [['None', key] for key in EG.nodes.keys() if EG.nodes[key]['place'] == 'workspace' and '_M_' in key]
            "left_storageの配置位置の決定"
            ###set_up
            left_object = [[key, EG.nodes[key]['container'][1]] for key in EG.nodes.keys() if '_F_' in key ]
            left_area = [ [i, point] for i, point in enumerate(ave_area) if point[3] == 2]
            placements = self.explore_all_placements(len(left_object), left_area)
            random.shuffle(placements)
            
            ###オブジェクト同士の衝突判定から配置可能領域の抽出
            ave_object_area = self.extract_placement_regions(placements, left_object+machine_object, all_area, EG, rm.rotmat_from_axangle([0, 0, 1], 0), machine_area=machine_num)            
            Fm.save_pickle_file(save_folder, 'left_storage_placement_rot_005_20240201.pickle', ave_object_area)
            
            # ###把持可能かどうかの確認
            random.shuffle(ave_object_area)
            OMCM = ObjectModelConfigManager.ObjectModelConfigManager(self.base)
            set_obj_dic = OMCM.set_object(ave_object_area[0], EG)
            result = OMCM.check_graspability(ave_object_area, save_folder, 'lft_arm', 'left_storage_placement_fin_rot_005.pickle', set_obj_dic, EG, rotmat=rm.rotmat_from_axangle([0, 0, 1], 0))
            Fm.save_pickle_file(save_folder, 'left_storage_placement_fin_rot_005_20240201.pickle', result)
            left_area_placement = result
            
            "right_storageの配置場所の決定"
            ###set_up
            right_object = [['None', key] for key in EG.nodes.keys() if EG.nodes[key]['place'] == 'right_storage' and EG.nodes[key]['label'] not in ['bowl0', 'bowl1', 'frying pan']]
            right_area = [ [i, point] for i, point in enumerate(ave_area) if point[3] == 1]
            placements = self.explore_all_placements(len(right_object), right_area)
            random.shuffle(placements)
            
            ###オブジェクト同士の衝突判定から配置可能領域の抽出
            ave_object_area = self.extract_placement_regions(placements, right_object+machine_object, all_area, EG, rm.rotmat_from_axangle([0, 0, 1], math.pi), machine_area=machine_num)            
            Fm.save_pickle_file(save_folder, 'right_storage_placement_rot_005_20240201.pickle', ave_object_area)
            
            # ###把持可能かどうかの確認
            random.shuffle(ave_object_area)
            OMCM = ObjectModelConfigManager.ObjectModelConfigManager(self.base)
            set_obj_dic = OMCM.set_object(ave_object_area[0], EG)
            result = OMCM.check_graspability(ave_object_area, save_folder, 'rgt_arm', 'right_storage_placement_fin_rot_005.pickle', set_obj_dic, EG, rotmat=rm.rotmat_from_axangle([0, 0, 1], math.pi))
            Fm.save_pickle_file(save_folder, 'right_storage_placement_fin_rot_005_20240201.pickle', result)
            right_area_placement = result
            
            "machineの配置場所の決定"
            machine_object = [['None', key] for key in EG.nodes.keys() if EG.nodes[key]['place'] == 'workspace' and '_M_' in key]
            machine_area = [ [i, point] for i, point in enumerate(ave_area) if point[3] == 0 and i == machine_num]
            object_area = []
            object_area.append([machine_object[0], machine_area[0]])
            OMCM = ObjectModelConfigManager.ObjectModelConfigManager(self.base)
            OMCM.set_object(object_area[-1:])
            OMCM.set_obj_pos(object_area[-1:])
            Fm.save_pickle_file(self.save_folder, 'stove_storage_placement_fin.pickle', object_area)
            
            input("計算終了しました！！！")
        else:
            right_area_placement = Fm.load_pickle_file(Fm.join_path_and_filename('path/to/motion_planning/save', 'right_storage_placement_fin_rot_005_20240201.pickle'))
            left_area_placement = Fm.load_pickle_file(Fm.join_path_and_filename('path/to/motion_planning/save', 'left_storage_placement_fin_rot_005_20240201.pickle'))
            "machineの配置場所の決定"
            machine_object = [['None', key] for key in EG.nodes.keys() if EG.nodes[key]['place'] == 'workspace' and '_M_' in key]
            machine_area = [ [i, point] for i, point in enumerate(ave_area) if point[3] == 0 and i == machine_num]
            object_area = []
            object_area.append([machine_object[0], machine_area[0]])
            OMCM = ObjectModelConfigManager.ObjectModelConfigManager(self.base)
            OMCM.set_object(object_area, EG)
            Fm.save_pickle_file(save_folder, 'stove_storage_placement_fin.pickle', object_area)
        
        return EG, right_area_placement, left_area_placement, object_area
        

class Motion_planner():
    def __init__(self):
        print('start')
        self.ave_area = Fm.load_csv_file(fr'{Fm.get_current_path()}\UR3dual\ave_point_rot_005_main.csv')
        self.ave_area.append([0.90, 0.025, 0.7825, 0])
        self.base = wd.World(cam_pos=[5,0,3],lookat_pos=[0,0,1])
        self.ans = None
    
    def get_available_area(self, place, area):
        copy_area = self.available_area[place]
        reset_area = [area_i for area_i in copy_area if area_i[0] != area]
        self.available_area[place] = reset_area
            
    def set_available_area(self, areas):
        for area in areas:
            if area[1][1][3] == 0:
                place = 'workspace'
            elif area[1][1][3] == 1:
                place = 'right_storage'
            elif area[1][1][3] == 2:
                place = 'left_storage'
            self.get_available_area(place, area[1][0])
    
    def set_EG_area(self, area, EG):
        ing_list = []
        for area_i in area:
            EG.nodes[area_i[0][1]]['area'] = area_i[1][0]
            EG.nodes[area_i[0][1]]['pos'] = area_i[1][1][:3]
            # if area_i[0][1] in 
            if EG.nodes[area_i[0][1]]['ingredients'] != [['', '']]:
                ing_keys = [item[1] for item in EG.nodes[area_i[0][1]]['ingredients'] if 'whole' in EG.nodes[item[1]]['cutting_style']]
                for ing_key in ing_keys:
                    EG.nodes[ing_key]['area'] = area_i[1][0]
                    EG.nodes[ing_key]['pos'] = np.array(area_i[1][1][:3]) + np.array([0, 0, 0.01])
                    ing_list.append([['None', ing_key], [area_i[1][0], np.array(area_i[1][1]) + np.array([0, 0, 0.03, 0])]])
        return ing_list

    def set_obj_pos_dic(self, obj_area, rotmat=np.eye(3)):
        area = [o[1][1][:-1] for o in obj_area]
        keys = [area[0][1] for area in obj_area]
        obj_pos_dic = {}
        for i, key in enumerate(keys):
            obj_pos_dic[key] = [area[i]+np.array([0, 0, 0.01]), rotmat]
        return obj_pos_dic

    def main(self, EG, FOON, plan_tree_file='', start_tree_level=0, toggle_tree_cut=False, toggle_change_node_pos=False):
        '''動作計画をするクラスです
        0. 初期配置が可能な場所の探索
        
        for 
            １. FOONから1つ目のタスクを読みだす
            ２．タスクごとに実行可能か比較する為の木グラフを作成する
            for
                ３．木グラフの状態に従い動作の実行可否判定
                ４．実行可能な場合は木にその動作と状態を保存
                ５．実行不可能な場合は枝刈りを実行
        '''
        
        "0. 初期配置が可能な場所の探索"
        
        
        Mpre = MotionPrep(self.base)
        EG, right_area_placement, left_area_placement, object_area = Mpre.set_enviroment_object(EG, self.ave_area, '/path/to/motion_planning/save', initial_placement_toggle = False)
        right_area_placement[3][2][1][0]= 48
        right_area_placement[3][2][1][1]= [0.65, -0.3, 0.7825, 1]
        right_area_placement[3][0][1][0] = 20
        right_area_placement[3][0][1][1] = [0.9, -0.45, 0.7825, 1]
        right_area_placement[3][1][1][0] = 13
        right_area_placement[3][1][1][1] = [0.5, -0.45, 0.7825, 1]
        right_area_placement[3][3][1][0] = 70
        right_area_placement[3][3][1][1] = [0.55, -0.2, 0.7825, 1]
        
        
        
        for right_area, left_area in zip(right_area_placement[3:], left_area_placement):
            all_area = {'right_storage':[[i, area[:3]] for i, area in enumerate(self.ave_area) if area[3] == 1], 'workspace':[[i, area[:3]] for i, area in enumerate(self.ave_area) if area[3] == 0], 'left_storage':[[i, area[:3]] for i, area in enumerate(self.ave_area) if area[3] == 2]}
            available_area = copy.deepcopy(all_area)
            ing_list_r = self.set_EG_area(right_area, EG)
            ing_list_l = self.set_EG_area(left_area, EG)
            ing_list_m = self.set_EG_area(object_area, EG)
            obj_pos_dic_r = self.set_obj_pos_dic(right_area+ing_list_r, rm.rotmat_from_axangle([0, 0, 1], math.pi))
            obj_pos_dic_l = self.set_obj_pos_dic(left_area+ing_list_l)
            obj_pos_dic_m = self.set_obj_pos_dic(object_area, rm.rotmat_from_axangle([0, 0, 1], math.pi))
            obj_pos_dic = obj_pos_dic_r | obj_pos_dic_l | obj_pos_dic_m
            
            
            "１. FOONから1つ目のタスクを読みだす"
            T_tree = Tt.TreeGraph()
            
            if plan_tree_file == '':
                T_tree.add_node('root', ['available_area', 'EG', 'obj_pos_dic', 'level', 'conf_list', 'jawwidth_list', 'obj_list'], [copy.deepcopy(available_area), copy.deepcopy(EG), copy.deepcopy(obj_pos_dic), 0, {}, {}, []])
                parent_id = ['root']
                task_num = 0
            else:
                T_tree.tree = Fm.load_pickle_file(plan_tree_file)
                if toggle_change_node_pos:
                    T_tree.Change_node_obj_pos('EO_000_C_003', 167, [0.7,0.25,0.7825+0.02])
                if start_tree_level == 0:
                    leaf_id, task_num = T_tree.get_leaf_nodes()
                else:
                    leaf_id = T_tree.get_nodes_from_level(start_tree_level)
                    task_num = start_tree_level-1
                    if toggle_tree_cut:
                        T_tree.trim_tree_from_level(start_tree_level+1)
                parent_id = [T_tree.get_parent(leaf_id[0])]
            FOON_i = FOON[-1]
            
            "２．タスクごとに実行可能か比較する為の木グラフを作成する"
            task_list = T_tree.extract_tasks_from_graph(FOON_i)
            save_file = 'FOON0.pickle'
            while True:
                task = task_list[task_num]
                task_num += 1
                if T_tree.get_children(parent_id[0]) == []:
                    id_list = T_tree.assign_tasks_to_tree_nodes(task, EG, available_area, parent_id, FOON_i, task_num)
                self.ans = T_tree.tree
                # T_tree.visualize()
                input(task)
                Fm.save_pickle_file('/path/to/object_placement', save_file, T_tree.tree)
            
                
                "３．木グラフの状態に従い動作の実行可否判定"
                EC = Execution_Checker.ExecutionChecker(self.base)
                ex_id = EC.main(T_tree, task_num, task, FOON_i, save_file)
                
                if ex_id != []:
                    winsound.Beep(1000, 1000)  # 周波数1000Hzの音を0.5秒鳴らす
                    parent_id = ex_id
                    Ms = Motion_storage.WRSA_motion_storage(self.base)
                    motion_list =  sub_analyze_graph.get_robot_motion_list(parent_id[0], T_tree.tree)
                    Ms.animation_dict(motion_list, toggle_image=False)
                else:
                    winsound.Beep(1000, 1000)  # 周波数1000Hzの音を0.5秒鳴らす
                    winsound.Beep(1000, 1000)  # 周波数1000Hzの音を0.5秒鳴らす
                    grand_parent_id = T_tree.get_parent(parent_id[0])
                    T_tree.remove_node_and_descendants(parent_id[0])
                    parent_id = [grand_parent_id]
                    task_num -= 2
    
                del EC
                
                                
                
            

if __name__ == '__main__':
    resulet_pickle = Fm.load_pickle_file('path/to/result.pickle')
    EG = Fm.load_json_as_graph('/path/to/Environmental_Object_Node/EO000.json')
    FOON = [result[0] for result in resulet_pickle]
    save_folder = 'path/to/object_placement'
    tree_file = 'path/to/object_placement/FOON0.pickle'
    FOON[7].nodes['FO_020_C_011']['place'] = 'workspace'
    MP = Motion_planner()
    right_area_placement = MP.main(EG, FOON, tree_file, start_tree_level=32, toggle_tree_cut=False, toggle_change_node_pos=False)
    # right_area_placement=MP.main(EG, FOON)
    # ans = MP.ans