# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 18:15:27 2024

@author: Shoichi
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
import robot_sim.robots.ur3e_dual.ur3e_dual as ur
import wrs.manipulation.pick_place_planner as ppp
import keyboard
import time
import Motion_storage
import copy


class ObjectModelConfigManager:
    def __init__(self, base):
        self.base=base
        self.gripper_s = robotiq.Robotiq85()
        self.ground = cm.gen_box(extent=[5, 5, 1], rgba =[.57, .57, .5, .7])
        self.ground.set_pos(np.array ([0,0,-.5]))
        self.ground.attach_to(self.base)
        self.robot_s = ur.UR3EDual()
        
    
    def set_object(self, obj_area, EG):
        """stlファイルを入力するとオブジェクトを追加する"""
        keys = [o[0][1] for o in obj_area]
        obj_model_dic = {}
        for i, key in enumerate(keys):
            print(key)
            stl_path = EG.nodes[key]['stl_path']
            object_ = cm.CollisionModel(stl_path)
            object_.set_rgba([0.7, 0.7, 0.0, 1])
            object_.show_localframe()
            rotmat = rm.rotmat_from_axangle([1, 0, 0], 0)
            object_.set_rotmat(rotmat)
            object_.show_cdprimit()
            # object_.attach_to(self.base)
            program = f"obj_model_dic.update({key}=object_)"
            exec(program)
        return obj_model_dic
    
    def set_object_model(self, obj_pose_dic, EG):
        """stlファイルを入力するとオブジェクトを追加する"""
        obj_model_dic = {}
        for i, key in enumerate(obj_pose_dic.keys()):
            stl_path = EG.nodes[key]['stl_path']
            object_ = cm.CollisionModel(stl_path)
            object_.set_rgba([0.7, 0.7, 0.0, 1])
            # object_.show_localframe()
            # object_.show_cdprimit()
            object_.set_pos(obj_pose_dic[key][0])
            object_.set_rotmat(obj_pose_dic[key][1])
            # object_.attach_to(self.base)
            program = f"obj_model_dic.update({key}=object_)"
            exec(program)
        return obj_model_dic
    
    def set_objdic_pos(self, obj_area, obj_model_dic, rotmat=np.eye(3)):
        area = [o[1][1][:-1] for o in obj_area]
        # input(obj_model_dic)
        obj_pos_dic = {}
        for i, key in enumerate(obj_model_dic.keys()):
            self.set_obj_pos(obj_model_dic[key], area[i]+np.array([0, 0, 0.005]), rotmat)
            obj_pos_dic[key] = [area[i]+np.array([0, 0, 0.005]), rotmat]
        #     obj_model_dic[key].attach_to(self.base)
        # self.base.run()
        return obj_model_dic, obj_pos_dic
        
    def set_obj_pos(self, obj_model, pos, rotmat):
        obj_model.set_pos(pos+np.array([0, 0, 0.005]))
        obj_model.set_rotmat(rotmat)
        
    def setup_check_object_collision(self, object_dic):
        for key in object_dic.keys():
            obstacle_list = [object_dic[item] for item in object_dic.keys() if object_dic[item] != object_dic[key]]
            check = object_dic[key].is_mcdwith(obstacle_list)
            if check:
                break
        return check
    
    def object_pic_motion(self, area, grasp_info_path, arm, obj_model_dic, rotmat=np.eye(3)):
        obj_model_dic, obj_pos_dic = self.set_objdic_pos(area, obj_model_dic, rotmat)
        model_list = []
        for i, key in enumerate(obj_model_dic.keys()):
            print(f"========================{i}=======================")
            obj = obj_model_dic[key]
            obstacle_list = [obj_model_dic[item] for item in obj_model_dic.keys() if item != key]
            grasp_info_list = Fm.load_pickle_file(grasp_info_path[i])
            goal_homomat_list = [obj.get_homomat()]
            Ms = Motion_storage.WRSA_motion_storage(self.base)
            for count, grasp_info in enumerate(grasp_info_list):
                print(f"====grasp_num:{count}")
                conf_list, jaw_list, obj_list = Ms.Pic_motion(arm, obj, self.robot_s.get_jnt_values(arm), self.robot_s.get_jnt_values(arm), grasp_info, goal_homomat_list, obstacle_list)
                if conf_list != None:
                    # Ms.animation(arm, obj, conf_list, jaw_list, obj_list, obstacle_list)
                    break
            if conf_list is None:
                print('Picモーションを生成できませんでした')
                return False
            else:
                print('Picモーションを生成できました')

        print('成功')
        del Ms
        return True

    def visual_obj(self, model_list):
        for model in model_list:
            model.set_rgba([0, 0, 1, 1])
            model.attach_to(self.base)
        self.base.run()
        for model in model_list:
            model.set_rgba([1, 1, 1, 1])
            model.detach()

    def check_graspability(self, ave_object_area, save_folder, arm, file_path, obj_model_dic, EG, rotmat=np.eye(3)):
        num = 0
        result = []
        for area in ave_object_area:
            if num%10 == 0 and num != 0:
                print(f'{Fm.get_current_time()}-------------------{num}/{len(ave_object_area)}---------------------------')
                # self.base.run()
            keys = [o[0][1] for o in area]
            grasp_info_list = [EG.nodes[key]['grasp_info_list'] for key in keys]
            print(num)
            # self.visual_obj([obj_model_dic[key] for key in obj_model_dic.keys()])
            togle = self.object_pic_motion(area, grasp_info_list, arm, obj_model_dic, rotmat)
            print(f'=============================================成功配置{len(result)}:探索回数{num}/500=======================================')
            if togle:
                result.append(area)
                # for key in obj_model_dic.keys():
                #     obj_model_dic[key].attach_to(self.base)
                # self.base.run()
                # for key in obj_model_dic.keys():
                #     obj_model_dic[key].detach()
                print(f'=============================================成功配置{len(result)}=======================================')
                if len(result) == 5:
                    break
            num += 1
            Fm.save_pickle_file(save_folder, file_path, result)
        return result
    