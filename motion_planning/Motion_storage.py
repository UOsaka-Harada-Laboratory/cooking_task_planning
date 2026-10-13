# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 15:46:21 2024

@author: user
"""

import File_management as Fm
import wrs.manipulation.pick_place_planner as ppp
import numpy as np
import math
import basis.robot_math as rm
import modeling.geometric_model as gm
import signal
from collections import defaultdict
import time
import robot_sim.end_effectors.gripper.robotiqhe.robotiqhe as rtq
import robot_sim.robots.ur3e_dual.ur3e_dual as ur
import ObjectModelConfigManager
import motion.probabilistic.rrt_connect as rrtc
from panda3d.core import KeyboardButton

        
class WRSA_motion_storage():
    def __init__(self, base):
        """
        :param object:
        :param robot_helper:
        author: weiwei, hao
        date: 20191122, 20210113
        """
        self.robot_s = ur.UR3EDual()
        self.first_jnt_values = {'rgt_hnd':self.robot_s.get_jnt_values('rgt_hnd'), 'lft_hnd':self.robot_s.get_jnt_values('lft_hnd')}
        self.gen_model = self.robot_s.gen_meshmodel()
        # self.gen_model.attach_to(base)
        self.PPP = ppp.PickPlacePlanner(self.robot_s, base)
        self.base = base
        self.gripper_s = rtq.RobotiqHE()
        self.rrtc_planner = rrtc.RRTConnect(self.robot_s, base)
        
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
                    seed_jnt_values=None,
                    toggle_sphere=False,
                    ing_list=[]):
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
        first_conf = self.robot_s.ik(hand_name,
                                     first_jaw_center_pos,
                                     first_jaw_center_rotmat,
                                     seed_jnt_values=seed_jnt_values)
        if first_conf is None:
            print("Cannot solve the ik at the first grasping pose!")
            if ing_list != []:
                return None, None, None, None
            else:
                return None, None, None
        self.robot_s.fk(component_name=hand_name, jnt_values=first_conf)
        if self.robot_s.is_collided():
            input('初期姿勢で衝突しています')
            self.robot_s.fk(component_name=hand_name, jnt_values=jnt_values_bk)
            if ing_list != []:
                return None, None, None, None
            else:
                return None, None, None
        # set a copy of the object to the start pose, hold the object, and move it to goal object pose
        objcm_copy = objcm.copy()
        # self.visual_obj(obstacle_list)
        objcm_copy.set_pos(first_obj_pos)
        objcm_copy.set_rotmat(first_obj_rotmat)
        rel_obj_pos, rel_obj_rotmat = self.robot_s.hold(objcm_copy, jaw_width,  hand_name)
        if ing_list != []:
            ing_objcm_copy_list = []
            ing_rel_list =[]
            for ing in ing_list:
                ing_objcm_copy_list.append(ing.copy())
                ing_rel_obj_pos, ing_rel_obj_rotmat = self.robot_s.hold(ing_objcm_copy_list[-1], jaw_width,  hand_name)
                ing_rel_list.append([ing_rel_obj_pos, ing_rel_obj_rotmat])
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
        # self.visual_obj(obstacle_list)
        conf_list_depart = self.PPP.inik_slvr.gen_rel_linear_motion(component_name=hand_name,
                                                                goal_tcp_pos=start_jaw_center_pos,
                                                                goal_tcp_rotmat=start_jaw_center_rotmat,
                                                                direction=depart_direction,
                                                                distance=depart_distance,
                                                                obstacle_list=obstacle_list,
                                                                granularity=ad_granularity,
                                                                seed_jnt_values=seed_conf,
                                                                type='source',
                                                                toggle_sphere=toggle_sphere)
        if conf_list_depart is None:
            print(f"Cannot generate the linear part of the holding depart motion!")
            self.robot_s.release(hand_name, objcm_copy, jawwidth_bk)
            self.robot_s.fk(component_name=hand_name, jnt_values=jnt_values_bk)
            del objcm_copy
            if ing_list != []:
                return None, None, None, None
            else:
                return None, None, None
        jawwidthlist_depart = self.PPP.gen_jawwidth_motion(conf_list_depart, jaw_width)
        objpose_list_depart = self.PPP.gen_object_motion(component_name=hand_name,
                                                     conf_list=conf_list_depart,
                                                     obj_pos=rel_obj_pos,
                                                     obj_rotmat=rel_obj_rotmat,
                                                     type='relative')
        if ing_list != []:
            ingpose_list = []
            for i, rel in enumerate(ing_rel_list):
                ingpose_list.append(self.PPP.gen_object_motion(component_name=hand_name,
                                                             conf_list=conf_list_depart,
                                                             obj_pos=rel[0],
                                                             obj_rotmat=rel[1],
                                                             type='relative'))
                self.robot_s.release(hand_name, ing_objcm_copy_list[i], jawwidth_bk)
            self.robot_s.release(hand_name, objcm_copy, jawwidth_bk)
            self.robot_s.fk(component_name=hand_name, jnt_values=jnt_values_bk)
            
            # input(f'{len(conf_list_depart)}, {len(jawwidthlist_depart)}, {len(objpose_list_depart)}')
            del objcm_copy
            return conf_list_depart, jawwidthlist_depart, objpose_list_depart, ingpose_list
        
        self.robot_s.release(hand_name, objcm_copy, jawwidth_bk)
        self.robot_s.fk(component_name=hand_name, jnt_values=jnt_values_bk)
        
        # input(f'{len(conf_list_depart)}, {len(jawwidthlist_depart)}, {len(objpose_list_depart)}')
        del objcm_copy
        return conf_list_depart, jawwidthlist_depart, objpose_list_depart
        
    
    
    def Pic_motion(self, 
                   hnd_name, 
                   objcm, 
                   start_conf, 
                   end_conf, 
                   grasp_info, 
                   goal_homomat_list,
                   obstacle_list,
                   grasp_id=0,
                   toggle_sphere=False,
                   toggle_grasp=False,
                   toggle_obj=False):
        ###パラメータ設定
        approach_direction_list=[np.array([0, 0, -1])] * len(goal_homomat_list)
        approach_distance_list=[.04] * len(goal_homomat_list)
        depart_direction_list=[np.array([0, 0, 1])] * len(goal_homomat_list)
        depart_distance_list=[.04] * len(goal_homomat_list)
        approach_jawwidth=None
        depart_jawwidth=None
        ad_granularity=.007
        use_rrt=True
        use_incremental=False
        ###パラメータ設定
        
        joint_bk = self.robot_s.get_jnt_values(hnd_name)
        ing_list = []
        if isinstance(objcm, list):
            ing_list = objcm[1:]
            objcm = objcm[0]
            ing_objcm_copy_list = []
            for ing in ing_list:
                ing_objcm_copy_list.append(ing.copy())
        
        ###把持位置まで持ってくるモーション
        if approach_jawwidth is None:
            approach_jawwidth = self.robot_s.hnd_dict[hnd_name].jawwidth_rng[1]
        if depart_jawwidth is None:
            depart_jawwidth = self.robot_s.hnd_dict[hnd_name].jawwidth_rng[1]
        first_goal_pos = goal_homomat_list[0][:3, 3]
        first_goal_rotmat = goal_homomat_list[0][:3, :3]
        
        if toggle_obj:
            objcm_vis = objcm.copy()
            objcm_vis.set_pos(first_goal_pos-approach_direction_list[0]*approach_distance_list[0])
            objcm_vis.set_rotmat(first_goal_rotmat)
            objcm_vis.set_rgba([1,1,1,1])
            # self.visual_obj([objcm_vis])
            objcm_vis.attach_to(self.base)
            # del objcm_vis
        
        jaw_width, jaw_center_pos, jaw_center_rotmat, hnd_pos, hnd_rotmat = grasp_info
        # approach
        first_jaw_center_pos = first_goal_rotmat.dot(jaw_center_pos) + first_goal_pos
        first_jaw_center_rotmat = first_goal_rotmat.dot(jaw_center_rotmat)
        # objcm as an obstacle
        if toggle_grasp:
            self.gripper_s.fix_to(first_goal_rotmat.dot(hnd_pos) + first_goal_pos, first_goal_rotmat.dot(hnd_rotmat))
            gripper_mesh = self.gripper_s.gen_meshmodel()
            gripper_mesh.attach_to(self.base)
            self.base.run()
            gripper_mesh.detach()
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
                                     toggle_sphere=toggle_sphere)
        if conf_list_approach is None:
            print("Cannot generate the pick motion!")
            if ing_list != []:
                del objcm_copy
                return None, None, None, None
            else:
                del objcm_copy
                return None, None, None
        print('approach成功')
        ###把持位置まで持ってくるモーション
        
        ###把持して持ち上げるモーションobstacle_listを[]に変更
        if ing_list != []:
            conf_list_middle, jawwidthlist_middle, objpose_list_middle, ingpose_list_middle = \
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
                                seed_jnt_values=conf_list_approach[-1],
                                toggle_sphere=toggle_sphere,
                                ing_list=ing_objcm_copy_list)
            if conf_list_middle is None:
                print("Cannot generate the middle motion!")
                del objcm_copy
                return None, None, None, None
        else:
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
                                seed_jnt_values=conf_list_approach[-1],
                                toggle_sphere=toggle_sphere,
                                ing_list=ing_list)
            if conf_list_middle is None:
                print("Cannot generate the middle motion!")
                del objcm_copy
                return None, None, None
        
        ###把持して持ち上げるモーション    
        objpose_list_approach = self.PPP.gen_object_motion(component_name=hnd_name,
                                                       conf_list=jawwidthlist_approach,
                                                       obj_pos=first_goal_pos,
                                                       obj_rotmat=first_goal_rotmat,
                                                       type='absolute')
        if ing_list != []:
            ingpose_list_approach = []
            for i, ing in enumerate(ing_list):
                ingpose_list_middle[i] = self.PPP.gen_object_motion(component_name=hnd_name,
                                                               conf_list=jawwidthlist_approach,
                                                               obj_pos=ing.get_pos(),
                                                               obj_rotmat=ing.get_rotmat(),
                                                               type='absolute') + ingpose_list_middle[i]
            self.robot_s.fk(hnd_name, joint_bk)
            del objcm_copy
            return conf_list_approach+conf_list_middle, jawwidthlist_approach+jawwidthlist_middle, objpose_list_approach+objpose_list_middle, ingpose_list_middle
        self.robot_s.fk(hnd_name, joint_bk)
        del objcm_copy
        return conf_list_approach+conf_list_middle, jawwidthlist_approach+jawwidthlist_middle, objpose_list_approach+objpose_list_middle
   
    def Cook_motion(self, 
                   hnd_name, 
                   objcm, 
                   start_conf, 
                   end_conf, 
                   grasp_info, 
                   goal_homomat_list,
                   obstacle_list,
                   grasp_id=0,
                   toggle_sphere=False,
                   toggle_grasp=False):

        
        joint_bk = self.robot_s.get_jnt_values(hnd_name)
        
        ###把持位置まで持ってくるモーション
        first_goal_pos = goal_homomat_list[0][:3, 3]
        first_goal_rotmat = goal_homomat_list[0][:3, :3]
        
        
        jaw_width, jaw_center_pos, jaw_center_rotmat, hnd_pos, hnd_rotmat = grasp_info
        # approach
        first_jaw_center_pos = first_goal_rotmat.dot(jaw_center_pos) + first_goal_pos
        first_jaw_center_rotmat = first_goal_rotmat.dot(jaw_center_rotmat)
        # objcm as an obstacle

        objcm_copy = objcm.copy()
        
        ###パラメータ設定
        hand_direction=rm.get_rotated_z_axis(first_goal_rotmat.dot(hnd_rotmat))
        approach_direction_list=[hand_direction] * len(goal_homomat_list)
        approach_distance_list=[.04] * len(goal_homomat_list)
        depart_direction_list=[hand_direction] * len(goal_homomat_list)
        depart_distance_list=[.04] * len(goal_homomat_list)
        approach_jawwidth=None
        depart_jawwidth=None
        ad_granularity=.007
        use_rrt=True
        use_incremental=False
        ###パラメータ設定
        
        if toggle_grasp:
            self.gripper_s.fix_to(first_goal_rotmat.dot(hnd_pos) + first_goal_pos, first_goal_rotmat.dot(hnd_rotmat))
            gripper_mesh = self.gripper_s.gen_meshmodel()
            gripper_mesh.attach_to(self.base)
            frame = gm.gen_frame(pos=first_goal_rotmat.dot(hnd_pos) + first_goal_pos, rotmat=first_goal_rotmat.dot(hnd_rotmat))
            frame.attach_to(self.base)
            sphere_mesh = []
            for i in range(5):
                sphere_pos = first_goal_rotmat.dot(hnd_pos) + first_goal_pos - hand_direction*0.02*i
                sphere_mesh.append(gm.gen_sphere(sphere_pos))
                sphere_mesh[-1].attach_to(self.base)
            self.base.run()
            gripper_mesh.detach()
            frame.detach()
            for mesh in sphere_mesh:
                mesh.detach()
           
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
                                     object_list=[],
                                     seed_jnt_values=start_conf,
                                     toggle_sphere=toggle_sphere)
        if conf_list_approach is None:
            print("Cannot generate the pick motion!")
            del objcm_copy
            return None, None, None
        
        print('approach成功')
        ###把持位置まで持ってくるモーション
        
        jawwidthlist_approach = self.PPP.gen_jawwidth_motion(conf_list_approach, jaw_width)
        objpose_list_approach = self.PPP.gen_object_motion(component_name=hnd_name,
                                                       conf_list=jawwidthlist_approach,
                                                       obj_pos=first_goal_pos,
                                                       obj_rotmat=first_goal_rotmat,
                                                       type='absolute')
        self.robot_s.fk(hnd_name, joint_bk)
        del objcm_copy
        return conf_list_approach+conf_list_approach[::-1], jawwidthlist_approach+jawwidthlist_approach[::-1], objpose_list_approach+objpose_list_approach[::-1]

    def Cut_motion(self, 
                   hnd_name, 
                   board_obj,
                   knife_obj,
                   rotmat,
                   start_conf,
                   end_conf,
                   grasp_info,
                   jawwidth_bk,
                   obstacle_list=[],
                   num_cuts=5,
                   cut_range=0.05,
                   seed_jnt_values=None,
                   toggle_sphere=False,
                   toggle_gripper=False,
                   toggle_goal_pos=False):
        """
        hand_name：使用するハンド
        board_obj:まな板のメッシュモデル
        knife_obj:包丁のメッシュモデル
        rotmat:knifeの姿勢
        start_conf:ロボットの初期姿勢
        end_conf:ロボットの最終姿勢
        grasp_info:包丁の把持姿勢
        num_cuts:オブジェクトを切る回数
        cut_range:オブジェクトを切る範囲
        """
        
        #knifeの目標位置を決定
        cut_high = np.array([0, 0, 0.01]) #knifeの高さ
        knife_base_pos = board_obj.get_pos() + cut_high #包丁のベースの位置
        rotmat = rm.rotmat_from_axangle([0,0,1], rotmat)
        cut_vec = rotmat[:, 1]  #包丁で切って行く方向
        cut_width = cut_range/num_cuts #切る幅
        knife_start_pos = knife_base_pos - cut_vec*cut_range/2
        knife_goal_pos = [knife_start_pos + i*cut_width*cut_vec  for i in range(num_cuts)]
        board_copy = board_obj.copy()
        board_copy.set_rgba([1,1,1,1])
        knife_copy = knife_obj.copy()
        
        if toggle_goal_pos:
            knife_mesh = []
            for i in range(num_cuts):
                knife_mesh.append(knife_obj.copy())
                knife_mesh[-1].set_pos(knife_goal_pos[i])
                knife_mesh[-1].set_rotmat(rotmat)
                if i != num_cuts-1:
                    knife_mesh[-1].set_rgba([0, 0, 1, 0.2])
                else:
                    knife_mesh[-1].set_rgba([0.75, 0.75, 0.75, 1])
                knife_mesh[-1].attach_to(self.base)
            board_copy.attach_to(self.base)
            self.base.run()
            # for i in range(num_cuts):
            #     knife_mesh[i].detach()
            del knife_mesh[i]
            board_copy.detach()
            
        knife_copy.set_rotmat(rotmat)
        for pos in knife_goal_pos:
            knife_copy.set_pos(pos)
            if knife_copy.is_mcdwith(obstacle_list):
                del knife_copy
                del board_copy
                print('配置位置でオブジェクト同士が衝突しています')
                return None, None, None
        print('配置位置でのオブジェクト同士の衝突なし')
        joint_bk = self.robot_s.get_jnt_values(hnd_name)
        
        "for文でゴール位置までのPlaceモーションを作成"
        ###パラメータ設定
        approach_dis = 0.05
        approach_direction_list=[np.array([0, 0, -1])]
        approach_distance_list=[approach_dis]
        depart_direction_list=[np.array([0, 0, 1])]
        depart_distance_list=[approach_dis]
        approach_jawwidth=None
        depart_jawwidth=None
        ad_granularity=.007
        use_rrt=True
        use_incremental=False
        ###パラメータ設定
        
        conf_list = []
        jawwidthlist = []
        objpose_list = []
        
        first_knife_pos = knife_obj.get_pos()
        first_knife_rot = knife_obj.get_rotmat()
        objcm_copy = knife_obj.copy()
        objcm_copy.set_pos(first_knife_pos)
        objcm_copy.set_rotmat(first_knife_rot)
        jaw_width, jaw_center_pos, jaw_center_rotmat, hnd_pos, hnd_rotmat = grasp_info
        rel_obj_pos, rel_obj_rotmat = self.robot_s.hold(objcm_copy, jaw_width, hnd_name)
        
        for goal_pos in knife_goal_pos:
            jnt_values_bk = joint_bk
            jawwidth_bk = jawwidth_bk
            # hold object
            first_jaw_center_pos = first_knife_rot.dot(jaw_center_pos) + first_knife_pos
            first_jaw_center_rotmat = first_knife_rot.dot(jaw_center_rotmat)
            first_conf = self.robot_s.ik(hnd_name,
                                         first_jaw_center_pos,
                                         first_jaw_center_rotmat,
                                         seed_jnt_values=seed_jnt_values)
            if first_conf is None :
                print("Cannot solve the ik at the first grasping pose!")
                if toggle_gripper:
                    self.gripper_s.fix_to(rotmat.dot(hnd_pos) + goal_pos, rotmat.dot(hnd_rotmat))
                    gripper_mesh = self.gripper_s.gen_meshmodel()
                    gripper_mesh.attach_to(self.base)
                    self.base.run()
                    gripper_mesh.detach()
                del board_copy
                del knife_copy
                del objcm_copy
                return None, None, None
            
            self.robot_s.fk(component_name=hnd_name, jnt_values=first_conf)
            # set a copy of the object to the start pose, hold the object, and move it to goal object pose
            
            seed_conf = first_conf
            
            goal_jaw_center_pos = rotmat.dot(jaw_center_pos) + goal_pos
            goal_jaw_center_rotmat = rotmat.dot(jaw_center_rotmat)
            
            approach_direction = approach_direction_list[0]
            if approach_direction is None:
                approach_direction = goal_jaw_center_rotmat[:, 2]
            approach_distance = approach_distance_list[0]
            if approach_distance is None:
                approach_distance = 0
            
            if toggle_gripper:
                self.gripper_s.fix_to(rotmat.dot(hnd_pos) + goal_pos, rotmat.dot(hnd_rotmat))
                gripper_mesh = self.gripper_s.gen_meshmodel()
                gripper_mesh.attach_to(self.base)
                self.base.run()
                gripper_mesh.detach()
            
            if use_rrt:  # if use rrt, we shall find start and goal conf first and then perform rrt
                # approach linear
                seed_conf = jnt_values_bk
                conf_list_approach = self.PPP.inik_slvr.gen_rel_linear_motion(component_name=hnd_name,
                                                                          goal_tcp_pos=goal_jaw_center_pos,
                                                                          goal_tcp_rotmat=goal_jaw_center_rotmat,
                                                                          direction=approach_direction,
                                                                          distance=approach_distance,
                                                                          obstacle_list=[],
                                                                          granularity=ad_granularity,
                                                                          seed_jnt_values=seed_conf,
                                                                          type='sink',
                                                                          toggle_sphere=toggle_sphere)
                if conf_list_approach is None:
                    print(f"Cannot generate the linear part of the holding approach motion!")
                    self.robot_s.release(hnd_name, objcm_copy, jawwidth_bk)
                    self.robot_s.fk(component_name=hnd_name, jnt_values=jnt_values_bk)
                    del board_copy
                    del knife_copy
                    del objcm_copy
                    return None, None, None
                
                conf_list_middle = self.PPP.rrtc_planner.plan(component_name=hnd_name,
                                                          start_conf=first_conf,
                                                          goal_conf=conf_list_approach[0],
                                                          obstacle_list=obstacle_list,
                                                          otherrobot_list=[],
                                                          ext_dist=.07,
                                                          max_iter=300)
                if conf_list_middle is None:
                    print(f"Cannot generate the rrtc part of the holding approach motion!")
                    self.robot_s.release(hnd_name, objcm_copy, jawwidth_bk)
                    self.robot_s.fk(component_name=hnd_name, jnt_values=jnt_values_bk)
                    del board_copy
                    del knife_copy
                    del objcm_copy
                    return None, None, None

            else:  # if do not use rrt, we start from depart end to mid end and then approach from mid end to goal
                seed_conf = jnt_values_bk
                self.robot_s.fk(component_name=hnd_name, jnt_values=seed_conf)
                mid_start_tcp_pos, mid_start_tcp_rotmat = self.robot_s.get_gl_tcp(hnd_name)
                mid_goal_tcp_pos = goal_jaw_center_pos - approach_direction * approach_distance
                mid_goal_tcp_rotmat = goal_jaw_center_rotmat
                conf_list_middle = self.PPP.inik_slvr.gen_linear_motion(component_name=hnd_name,
                                                                    start_tcp_pos=mid_start_tcp_pos,
                                                                    start_tcp_rotmat=mid_start_tcp_rotmat,
                                                                    goal_tcp_pos=mid_goal_tcp_pos,
                                                                    goal_tcp_rotmat=mid_goal_tcp_rotmat,
                                                                    obstacle_list=obstacle_list,
                                                                    granularity=ad_granularity,
                                                                    seed_jnt_values=seed_conf,
                                                                    toggle_sphere=toggle_sphere
                                                                    )
                if conf_list_middle is None:
                    print(f"Cannot generate the rrtc part of the holding approach motion!")
                    self.robot_s.release(hnd_name, objcm_copy, jawwidth_bk)
                    self.robot_s.fk(component_name=hnd_name, jnt_values=jnt_values_bk)
                    del board_copy
                    del knife_copy
                    del objcm_copy
                    return None, None, None
                # approach linear
                seed_conf = conf_list_middle[-1]
                conf_list_approach = self.PPP.inik_slvr.gen_rel_linear_motion(component_name=hnd_name,
                                                                          goal_tcp_pos=goal_jaw_center_pos,
                                                                          goal_tcp_rotmat=goal_jaw_center_rotmat,
                                                                          direction=approach_direction,
                                                                          distance=approach_distance,
                                                                          obstacle_list=obstacle_list,
                                                                          granularity=ad_granularity,
                                                                          seed_jnt_values=seed_conf,
                                                                          type='sink',
                                                                          toggle_sphere=toggle_sphere)
                if conf_list_approach is None:
                    print(f"Cannot generate the linear part of the holding approach motion!")
                    self.robot_s.release(hnd_name, objcm_copy, jawwidth_bk)
                    self.robot_s.fk(component_name=hnd_name, jnt_values=jnt_values_bk)
                    del board_copy
                    del knife_copy
                    del objcm_copy
                    return None, None, None
            
            
            jawwidthlist_approach = self.PPP.gen_jawwidth_motion(conf_list_approach, jaw_width)
            objpose_list_approach = self.PPP.gen_object_motion(component_name=hnd_name,
                                                           conf_list=conf_list_approach,
                                                           obj_pos=rel_obj_pos,
                                                           obj_rotmat=rel_obj_rotmat,
                                                           type='relative')
            jawwidthlist_middle = self.PPP.gen_jawwidth_motion(conf_list_middle, jaw_width)
            objpose_list_middle = self.PPP.gen_object_motion(component_name=hnd_name,
                                                         conf_list=conf_list_middle,
                                                         obj_pos=rel_obj_pos,
                                                         obj_rotmat=rel_obj_rotmat,
                                                         type='relative')
            
            conf_list = conf_list + conf_list_middle + conf_list_approach + conf_list_approach[::-1]
            jawwidthlist = jawwidthlist + jawwidthlist_middle + jawwidthlist_approach + jawwidthlist_approach[::-1]
            objpose_list = objpose_list + objpose_list_middle + objpose_list_approach + objpose_list_approach[::-1]
            seed_conf = conf_list[-1]
            
            ###knifeの姿勢の更新
            first_knife_pos = objpose_list[-1][:3, 3]
            first_knife_rot = objpose_list[-1][:3, :3]
            
        self.robot_s.release(hnd_name, objcm_copy, jawwidth_bk)
        self.robot_s.fk(component_name=hnd_name, jnt_values=jnt_values_bk)
        del board_copy
        del knife_copy
        del objcm_copy
        return conf_list, jawwidthlist, objpose_list
        
    def Pour_motion(self, 
                   hnd_name, 
                   source_container,
                   target_container,
                   rotmat,
                   start_conf,
                   end_conf,
                   grasp_info,
                   jawwidth_bk,
                   obstacle_list=[],
                   center_distance=0.09,
                   pour_angle=math.pi/8*4,
                   container_height=0.1,
                   seed_jnt_values=None,
                   toggle_sphere=False,
                   toggle_gripper=False,
                   toggle_goal_pos=False,
                   toggle_rrt=True):
        ###パラメータ設定
        approach_dis = 0.0
        approach_direction=np.array([0, 0, -1])
        approach_distance=approach_dis
        approach_jawwidth=None
        depart_jawwidth=None
        ad_granularity=.007
        use_rrt=True
        use_incremental=False
        ###パラメータ設定
        
        jaw_width, jaw_center_pos, jaw_center_rotmat, hnd_pos, hnd_rotmat = grasp_info
        ing_list = []
        if isinstance(source_container, list):
            ing_list = source_container[1:]
            source_container = source_container[0]
        
        "目標オブジェクトの姿勢"
        target_container_copy = target_container.copy()
        target_container_pos = target_container_copy.get_pos()
        source_container_copy = source_container.copy()
        source_container_pos = target_container_pos + np.array([0, 0, container_height]) + np.array([center_distance*math.sin(rotmat), center_distance*math.cos(rotmat), 0])
        sc_vec = np.array([source_container_pos[0]-target_container_pos[0], source_container_pos[1]-target_container_pos[1], 0])
        source_container_anglel = rm.angle_between_vectors([1, 0, 0], sc_vec, True)
        source_container_rotmat = rm.rotmat_from_axangle([0, 0, 1], source_container_anglel)
        pour_angle_list = [source_container_rotmat.dot(rm.rotmat_from_axangle([0, 1, 0], -pour_angle/10*i)) for i in range(10)]
        pour_pos_list = [source_container_pos+np.dot(source_container_rotmat, np.array([center_distance*(math.cos(pour_angle/10*i)-1), 0, center_distance*math.sin(pour_angle/10*i)])) for i in range(10)]
        
        if toggle_goal_pos:
            source_container_test_list = []
            source_container_test = source_container.copy()
            source_container_test.set_pos(source_container_pos)
            source_container_test.set_rotmat(source_container_rotmat)
            source_container_test.set_rgba([1, 1, 1, 1])
            source_container_test.attach_to(self.base)
            target_container_copy.set_rgba([1,1,1,1])
            target_container_copy.attach_to(self.base)
            self.base.run()
            for i, angle in enumerate(pour_angle_list):
                source_container_test_list.append(source_container.copy())
                source_container_test_list[-1].set_pos(pour_pos_list[i])
                source_container_test_list[-1].set_rotmat(angle)
                if i == len(pour_angle_list)-1:
                    source_container_test_list[-1].set_rgba([1, 1, 1, 1])
                else:
                    source_container_test_list[-1].set_rgba([0, 0, 1, 0.2])
                source_container_test_list[-1].attach_to(self.base)
                # gm.gen_sphere(source_container_pos+np.dot(source_container_rotmat, np.array([center_distance*(math.cos(pour_angle/10*i)-1), 0, center_distance*math.sin(pour_angle/10*i)]))).attach_to(self.base)
            self.base.run()
        
        "オブジェクトのホールド"
        first_source_container_pos = source_container.get_pos()
        first_source_container_rot = source_container.get_rotmat()
        source_container_copy.set_pos(first_source_container_pos)
        source_container_copy.set_rotmat(first_source_container_rot)
    
    
        
        "Pourの前の姿勢をｒｒｔで移動"
        joint_bk = self.robot_s.get_jnt_values(hnd_name)
        #初期姿勢を計算
        jnt_values_bk = joint_bk
        jawwidth_bk = jawwidth_bk
        # hold object
        first_jaw_center_pos = first_source_container_rot.dot(jaw_center_pos) + first_source_container_pos
        first_jaw_center_rotmat = first_source_container_rot.dot(jaw_center_rotmat)
        first_conf = self.robot_s.ik(hnd_name,
                                     first_jaw_center_pos,
                                     first_jaw_center_rotmat,
                                     seed_jnt_values=seed_jnt_values)
        if first_conf is None:
            print('souce containerの初期姿勢生成に失敗')
            del target_container_copy
            del source_container_copy
            if ing_list != []:
                return None, None, None, None
            else:
                return None, None, None
        self.robot_s.fk(hnd_name, first_conf)
        rel_obj_pos, rel_obj_rotmat = self.robot_s.hold(source_container_copy, jaw_width, hnd_name)
        if ing_list != []:
            ing_objcm_copy_list = []
            ing_rel_list = []
            for ing in ing_list:
                ing_objcm_copy_list.append(ing.copy())
                ing_rel_obj_pos, ing_rel_obj_rotmat = self.robot_s.hold(ing_objcm_copy_list[-1], jaw_width,  hnd_name)
                ing_rel_list.append([ing_rel_obj_pos, ing_rel_obj_rotmat])
        
        #目標姿勢を計算
        goal_jaw_center_pos = pour_angle_list[0].dot(jaw_center_pos) + pour_pos_list[0]
        goal_jaw_center_rotmat = pour_angle_list[0].dot(jaw_center_rotmat)
        
        if toggle_gripper:
            self.gripper_s.fix_to(pour_angle_list[0].dot(hnd_pos) + pour_pos_list[0], pour_angle_list[0].dot(hnd_rotmat))
            gripper_mesh = self.gripper_s.gen_meshmodel()
            gripper_mesh.attach_to(self.base)
            source_container_test = source_container.copy()
            source_container_test.set_pos( pour_pos_list[0])
            source_container_test.set_rotmat(pour_angle_list[0])
            source_container_test.attach_to(self.base)
            target_container_copy.attach_to(self.base)
            self.base.run()
            gripper_mesh.detach()
            source_container_test.detach()
            target_container_copy.detach()
        goal_conf = self.robot_s.ik(hnd_name,
                                     goal_jaw_center_pos,
                                     goal_jaw_center_rotmat,
                                     seed_jnt_values=seed_jnt_values)
        if goal_conf is None:
            print('souce containerの目標姿勢生成に失敗')
            del target_container_copy
            del source_container_copy
            if ing_list != []:
                return None, None, None, None
            else:
                return None, None, None
        
        if toggle_gripper:
            self.robot_s.fk(hnd_name, goal_conf)
            mesh = self.robot_s.gen_meshmodel()
            mesh.attach_to(self.base)
            source_container_test.attach_to(self.base)
            target_container_copy.attach_to(self.base)
            self.base.run()
            mesh.detach()
            source_container_test.detach()
            target_container_copy.detach()
            del mesh
        
        if toggle_rrt:
            #RRTで動作計画
            # self.visual_obj(obstacle_list
            conf_list_approach = self.PPP.rrtc_planner.plan(component_name=hnd_name,
                                                      start_conf=first_conf,
                                                      goal_conf=goal_conf,
                                                      obstacle_list=obstacle_list,
                                                      otherrobot_list=[],
                                                      ext_dist=.07,
                                                      max_iter=300
                                                      )
            if conf_list_approach is None:
                print(f"souce containerのrrt動作生成に失敗")
                self.robot_s.release(hnd_name, source_container_copy, jawwidth_bk)
                self.robot_s.fk(component_name=hnd_name, jnt_values=jnt_values_bk)
                del target_container_copy
                del source_container_copy
                if ing_list != []:
                    return None, None, None, None
                else:
                    return None, None, None
        else:
            conf_list_approach = self.PPP.inik_slvr.gen_linear_motion(component_name=hnd_name,
                                                                start_tcp_pos=first_jaw_center_pos,
                                                                start_tcp_rotmat=first_jaw_center_rotmat,
                                                                goal_tcp_pos=goal_jaw_center_pos,
                                                                goal_tcp_rotmat=goal_jaw_center_rotmat,
                                                                obstacle_list=[],
                                                                granularity=ad_granularity,
                                                                seed_jnt_values=joint_bk,
                                                                toggle_sphere=toggle_sphere
                                                                )
            if conf_list_approach is None:
                print(f"souce containerの直線起動による動作生成に失敗")
                self.robot_s.release(hnd_name, source_container_copy, jawwidth_bk)
                self.robot_s.fk(component_name=hnd_name, jnt_values=jnt_values_bk)
                del target_container_copy
                del source_container_copy
                if ing_list != []:
                    return None, None, None, None
                else:
                    return None, None, None
            
        
        """for文を使って傾きを追加していく"""
        conf_middle = []
        count = 0
        seed_conf = conf_list_approach[-1]
        for pos, angle in zip(pour_pos_list, pour_angle_list):
            self.robot_s.fk(component_name=hnd_name, jnt_values=seed_conf)
            mid_start_tcp_pos = goal_jaw_center_pos
            mid_start_tcp_rotmat = goal_jaw_center_rotmat
            goal_jaw_center_pos = angle.dot(jaw_center_pos) + pos
            goal_jaw_center_rotmat = angle.dot(jaw_center_rotmat)
            conf_list_middle = self.PPP.inik_slvr.gen_linear_motion(component_name=hnd_name,
                                                                start_tcp_pos=mid_start_tcp_pos,
                                                                start_tcp_rotmat=mid_start_tcp_rotmat,
                                                                goal_tcp_pos=goal_jaw_center_pos,
                                                                goal_tcp_rotmat=goal_jaw_center_rotmat,
                                                                obstacle_list=[],
                                                                granularity=ad_granularity,
                                                                seed_jnt_values=seed_conf,
                                                                toggle_sphere=toggle_sphere
                                                                )
            if conf_list_middle is None:
                Fm.beep(3)  # 通知音
                if count >= 2:
                    break
                print(f"Cannot generate the rrtc part of the holding approach motion!")
                self.robot_s.release(hnd_name, source_container_copy, jawwidth_bk)
                self.robot_s.fk(component_name=hnd_name, jnt_values=jnt_values_bk)
                del target_container_copy
                del source_container_copy
                if ing_list != []:
                    return None, None, None, None
                else:
                    return None, None, None
            conf_middle += conf_list_middle
            seed_conf = conf_list_middle[-1]
            count += 1
        
        "objectとawwithの設定"
        conf_list = conf_list_approach + conf_middle + conf_middle[::-1]            
        jawwidthlist = self.PPP.gen_jawwidth_motion(conf_list, jaw_width)
        objpose_list = self.PPP.gen_object_motion(component_name=hnd_name,
                                                       conf_list=conf_list,
                                                       obj_pos=rel_obj_pos,
                                                       obj_rotmat=rel_obj_rotmat,
                                                       type='relative')
            
        if ing_list != []:
            ingpose_list = []
            for i, ing in enumerate(ing_list):
                ingpose_list_approach = self.PPP.gen_object_motion(component_name=hnd_name,
                                                               conf_list=conf_list_approach,
                                                               obj_pos=ing_rel_list[i][0],
                                                               obj_rotmat=ing_rel_list[i][1],
                                                               type='relative')
                ingpose_list_middle = self.PPP.gen_object_motion(component_name=hnd_name,
                                                             conf_list=conf_middle,
                                                             obj_pos=ing_rel_list[i][0],
                                                             obj_rotmat=ing_rel_list[i][1],
                                                             type='relative')
                ingpose_list_last = self.PPP.gen_object_motion(component_name=hnd_name,
                                                               conf_list=conf_middle,
                                                               obj_pos=target_container.get_pos()+np.array([0.01]),
                                                               obj_rotmat=target_container.get_rotmat(),
                                                               type='absolute')
                ingpose_list.append(ingpose_list_approach+ingpose_list_middle+ingpose_list_last)
                self.robot_s.release(hnd_name, ing_objcm_copy_list[i], jawwidth_bk)
            self.robot_s.release(hnd_name, source_container_copy, jawwidth_bk)
            self.robot_s.fk(component_name=hnd_name, jnt_values=jnt_values_bk)
            del source_container_copy
            return conf_list, jawwidthlist, objpose_list, ingpose_list
    
        self.robot_s.release(hnd_name, source_container_copy, jawwidth_bk)
        self.robot_s.fk(component_name=hnd_name, jnt_values=jnt_values_bk)
        del target_container_copy
        del source_container_copy
        return conf_list, jawwidthlist, objpose_list
    
    
    def Mix_motion(self, 
                   hnd_name, 
                   spatula_model,
                   target_container,
                   rotmat,
                   start_conf,
                   end_conf,
                   grasp_info,
                   jawwidth_bk,
                   obstacle_list=[],
                   center_distance=0.09,
                   pour_angle=math.pi/8*4,
                   container_height=0.15,
                   seed_jnt_values=None,
                   toggle_sphere=False,
                   toggle_gripper=False,
                   toggle_goal_pos=False):
        ###パラメータ設定
        Mix_dis = 0.09
        approach_dis = 0.1
        approach_direction=np.array([0, 0, -1])
        approach_distance=approach_dis
        approach_jawwidth=None
        depart_jawwidth=None
        ad_granularity=.007
        use_rrt=True
        use_incremental=False
        ###パラメータ設定
        
        
        "目標オブジェクトの姿勢"
        target_container_copy = target_container.copy()
        target_container_pos = target_container_copy.get_pos()
        spatula_model_copy = spatula_model.copy()
        spatula_model_pos = target_container_pos + np.array([0, 0, container_height])
        spatula_model_rotmat = rm.rotmat_from_axangle([0, 1, 0], math.pi/2 + rotmat) #(math.pi/2 + rotmat))
        Mix_pos_list = []
        for mix_direction in [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0]]:
            Mix_pos_list.append([spatula_model_pos+np.array(mix_direction)*Mix_dis/10*j for j in range(10)])
            
        if toggle_goal_pos:
            spatula_model_test = []
            spatula_model_test.append(spatula_model.copy())
            spatula_model_test[-1].set_pos(spatula_model_pos)
            spatula_model_test[-1].set_rotmat(spatula_model_rotmat)
            spatula_model_test[-1].set_rgba([1,1,1,1])
            spatula_model_test[-1].attach_to(self.base)
            target_container_copy.set_rgba([1,1,1,1])
            target_container_copy.attach_to(self.base)
            self.base.run()
            for pos_list in Mix_pos_list:
                for pos in pos_list:
                    spatula_model_test.append(spatula_model.copy())
                    spatula_model_test[-1].set_pos(pos)
                    spatula_model_test[-1].set_rotmat(spatula_model_rotmat)
                    spatula_model_test[-1].set_rgba([0,0,1,0.2])
                    spatula_model_test[-1].attach_to(self.base)
                    self.base.run()
            # for model in spatula_model_test:
            #     model.detach()
            del spatula_model_test
        
        
        "オブジェクトのホールド"
        first_spatula_model_pos = spatula_model.get_pos()
        first_spatula_model_rotmat = spatula_model.get_rotmat()
        spatula_model_copy.set_pos(first_spatula_model_pos)
        spatula_model_copy.set_rotmat(first_spatula_model_rotmat)
        jaw_width, jaw_center_pos, jaw_center_rotmat, hnd_pos, hnd_rotmat = grasp_info
    
        
        "Pourの前の姿勢をｒｒｔで移動"
        joint_bk = self.robot_s.get_jnt_values(hnd_name)
        #初期姿勢を計算
        jnt_values_bk = joint_bk
        jawwidth_bk = jawwidth_bk
        # hold object
        first_jaw_center_pos = first_spatula_model_rotmat.dot(jaw_center_pos) + first_spatula_model_pos
        first_jaw_center_rotmat = first_spatula_model_rotmat.dot(jaw_center_rotmat)
        # first_conf = self.robot_s.ik(hnd_name,
        #                              first_jaw_center_pos,
        #                              first_jaw_center_rotmat,
        #                              seed_jnt_values=seed_jnt_values)
        # if first_conf is None:
        #     print('souce containerの初期姿勢生成に失敗')
        #     del target_container_copy
        #     del source_container_copy
        #     return None, None, None
        first_conf = jnt_values_bk
        self.robot_s.fk(hnd_name, first_conf)
        rel_obj_pos, rel_obj_rotmat = self.robot_s.hold(spatula_model_copy, jaw_width, hnd_name)
        
        #目標姿勢を計算
        for first_angle in range(16):
            spatula_model_rotmat_i = np.dot(rm.rotmat_from_axangle([0, 0, 1], math.pi/8*first_angle), spatula_model_rotmat)
            goal_spatula_pos = spatula_model_pos + np.array([0, 0, approach_dis])
            goal_jaw_center_pos = spatula_model_rotmat_i.dot(jaw_center_pos) + goal_spatula_pos
            goal_jaw_center_rotmat = spatula_model_rotmat_i.dot(jaw_center_rotmat)
            
            if toggle_gripper:
                self.gripper_s.fix_to(spatula_model_rotmat_i.dot(hnd_pos) + goal_spatula_pos, spatula_model_rotmat_i.dot(hnd_rotmat))
                gripper_mesh = self.gripper_s.gen_meshmodel()
                gripper_mesh.attach_to(self.base)
                spatula_model_test_2 = spatula_model.copy()
                spatula_model_test_2.set_pos(goal_spatula_pos)
                spatula_model_test_2.set_rotmat(spatula_model_rotmat_i)
                spatula_model_test_2.attach_to(self.base)
                target_container_copy.attach_to(self.base)
                self.base.run()
                gripper_mesh.detach()
                spatula_model_test_2.detach()
                target_container_copy.detach()
            goal_conf = self.robot_s.ik(hnd_name,
                                         goal_jaw_center_pos,
                                         goal_jaw_center_rotmat,
                                         seed_jnt_values=first_conf)
            if goal_conf is None:
                print(f'souce containerの目標姿勢生成に失敗\n======={first_angle}/15==========')
                if first_angle == 15:
                    del target_container_copy
                    del spatula_model_copy
                    return None, None, None
                continue
            print('spatula_modelの目標姿勢生成に成功')

            #RRTで動作計画
            # self.visual_obj(obstacle_list)
            if toggle_gripper:
                self.robot_s.fk(hnd_name, goal_conf)
                mesh = self.robot_s.gen_meshmodel()
                mesh.attach_to(self.base)
                spatula_model_test_2.attach_to(self.base)
                target_container_copy.attach_to(self.base)
                self.base.run()
                mesh.detach()
                spatula_model_test_2.detach()
                target_container_copy.detach()
                del mesh
                
            conf_list_approach = self.PPP.rrtc_planner.plan(component_name=hnd_name,
                                                      start_conf=first_conf,
                                                      goal_conf=goal_conf,
                                                      obstacle_list=[],
                                                      otherrobot_list=[],
                                                      ext_dist=.07,
                                                      max_iter=300
                                                      )
            if conf_list_approach is None:
                print(f"souce containerのrrt動作生成に失敗")
                self.robot_s.release(hnd_name, spatula_model, jawwidth_bk)
                self.robot_s.fk(component_name=hnd_name, jnt_values=jnt_values_bk)
                # del target_container_copy
                # del source_container_copy
                continue
            
            """for文を使って傾きを追加していく"""
            conf_middle = []
            conf_middle_i = []
            count = 0
            list_count = 0
            seed_conf = conf_list_approach[-1]
            for pos_list in Mix_pos_list:
                for pos in pos_list:
                    self.robot_s.fk(component_name=hnd_name, jnt_values=seed_conf)
                    mid_start_tcp_pos = goal_jaw_center_pos
                    mid_start_tcp_rotmat = goal_jaw_center_rotmat
                    goal_jaw_center_pos = spatula_model_rotmat_i.dot(jaw_center_pos) + pos
                    goal_jaw_center_rotmat = spatula_model_rotmat_i.dot(jaw_center_rotmat)
                    conf_list_middle = self.PPP.inik_slvr.gen_linear_motion(component_name=hnd_name,
                                                                        start_tcp_pos=mid_start_tcp_pos,
                                                                        start_tcp_rotmat=mid_start_tcp_rotmat,
                                                                        goal_tcp_pos=goal_jaw_center_pos,
                                                                        goal_tcp_rotmat=goal_jaw_center_rotmat,
                                                                        obstacle_list=[],
                                                                        granularity=ad_granularity,
                                                                        seed_jnt_values=seed_conf,
                                                                        toggle_sphere=toggle_sphere
                                                                        )
                    if conf_list_middle is None:
                        print(f"Cannot generate the rrtc part of the holding approach motion!")
                        continue
                    else:
                        print(f"移動成功!")
                        count += 1
                        conf_middle_i += conf_list_middle
                        seed_conf = conf_list_middle[-1]
                if conf_middle_i != [] and count > 3:
                    conf_middle += conf_middle_i + conf_middle_i[::-1]
                    seed_conf = conf_middle[-1]
                    conf_middle_i = []
                    count = 0
                    list_count += 1
            if conf_middle != [] and list_count>1:
               break
        
        "objectとawwithの設定"
        conf_list = conf_list_approach + conf_middle + conf_middle[::-1]            
        jawwidthlist = self.PPP.gen_jawwidth_motion(conf_list, jaw_width)
        objpose_list = self.PPP.gen_object_motion(component_name=hnd_name,
                                                       conf_list=conf_list,
                                                       obj_pos=rel_obj_pos,
                                                       obj_rotmat=rel_obj_rotmat,
                                                       type='relative')
            
        self.robot_s.release(hnd_name, spatula_model, jawwidth_bk)
        self.robot_s.fk(component_name=hnd_name, jnt_values=jnt_values_bk)
        del target_container_copy
        del spatula_model
        return conf_list, jawwidthlist, objpose_list
        

    
    def pic_ingredients(self, hnd_name, objcm, start_conf, end_conf, grasp_info, goal_homomat_list, obstacle_list, grasp_id=[0, 0]):
        rotmat_list = [rm.rotmat_from_axangle([0, 0, 1], math.pi*rad/8) for rad in range(3)]
        for i, rot in enumerate(rotmat_list[grasp_id[0]:]):
            objcm.set_rotmat(rot)
            goal_homomat_list = [objcm.get_homomat()]
            # self.base.run()
            conf_list, jawwidth_list, objpose_list, grasp_id_sub = self.Pic_motion(hnd_name, objcm, start_conf, end_conf, grasp_info, goal_homomat_list, [], grasp_id=grasp_id[1], toggle_sphere=False, toggle_grasp=False)
            if conf_list is not None:
                return conf_list, jawwidth_list, objpose_list, [grasp_id[0]+i, grasp_id_sub]
        return None, None, None
    
    def place_motion(self,
                    jawwidth_bk,
                    jnt_values_bk,
                    hand_name,
                    objcm,
                    grasp_info,
                    obj_pose_list,
                    ad_granularity=.007,
                    use_rrt=True,
                    obstacle_list=[],
                    seed_jnt_values=None,
                    toggle_sphere=False,
                    toggle_gripper=False,
                    toggle_obj=False
                    ):
        
        goal_homomat_list=obj_pose_list
        
        ###パラメータ設定
        approach_direction_list=[np.array([0, 0, -1])] * len(goal_homomat_list)
        approach_distance_list=[.04] * len(goal_homomat_list)
        depart_direction_list=[np.array([0, 0, 1])] * len(goal_homomat_list)
        depart_distance_list=[.04] * len(goal_homomat_list)
        approach_jawwidth=None
        depart_jawwidth=None
        ad_granularity=.007
        use_incremental=False
        ###パラメータ設定
        
        ing_list = []
        
        jnt_values_bk = jnt_values_bk
        jawwidth_bk = jawwidth_bk
        # final
        conf_list = []
        jawwidthlist = []
        objpose_list = []
        # hold object
        jaw_width, jaw_center_pos, jaw_center_rotmat, hnd_pos, hnd_rotmat = grasp_info
        if isinstance(objcm, list):
            ing_list = objcm[1:]
            objcm = objcm[0]
            ing_objcm_copy_list = []
            ing_rel_list = []
            for ing in ing_list:
                ing_objcm_copy_list.append(ing.copy())
                ing_rel_obj_pos, ing_rel_obj_rotmat = self.robot_s.hold(ing_objcm_copy_list[-1], jaw_width,  hand_name)
                ing_rel_list.append([ing_rel_obj_pos, ing_rel_obj_rotmat])
        first_obj_pos = objcm.get_pos()
        first_obj_rotmat = objcm.get_rotmat()
        first_jaw_center_pos = first_obj_rotmat.dot(jaw_center_pos) + first_obj_pos
        first_jaw_center_rotmat = first_obj_rotmat.dot(jaw_center_rotmat)
        

        
        ###まな板配置で消した
        # first_conf = self.robot_s.ik(hand_name,
        #                              first_jaw_center_pos,
        #                              first_jaw_center_rotmat,
        #                              seed_jnt_values=seed_jnt_values)
        # if first_conf is None :
        #     print("Cannot solve the ik at the first grasping pose!")
        #     if toggle_gripper:
        #         self.gripper_s.fix_to(first_obj_rotmat.dot(hnd_pos) + first_obj_pos, first_obj_rotmat.dot(hnd_rotmat))
        #         gripper_mesh = self.gripper_s.gen_meshmodel()
        #         gripper_mesh.attach_to(self.base)
        #         self.base.run()
        #         gripper_mesh.detach()
        #     return None, None, None
        first_conf = jnt_values_bk
        self.robot_s.fk(component_name=hand_name, jnt_values=first_conf)
        # set a copy of the object to the start pose, hold the object, and move it to goal object pose
        
        objcm_copy = objcm.copy()
        objcm_copy.set_pos(first_obj_pos)
        objcm_copy.set_rotmat(first_obj_rotmat)
        rel_obj_pos, rel_obj_rotmat = self.robot_s.hold(objcm_copy, jaw_width,  hand_name)
        
        seed_conf = first_conf
        
        
        # get start and goal object poses
        goal_obj_pos = obj_pose_list[0][:3, 3]
        goal_obj_rotmat = obj_pose_list[0][:3, :3]
        # transform grasps
        
        "初期配置で衝突判定"
        objcm_goal = objcm.copy()
        objcm_goal.set_homomat(obj_pose_list[0])
        
        if toggle_obj:
            self.visual_obj(obstacle_list+[objcm_goal])
        if objcm_goal.is_mcdwith(obstacle_list):
            del objcm_goal
            print('配置位置でオブジェクト同士が衝突しています')
            if ing_list != []:
                return None, None, None, None
            else:
                return None, None, None

        goal_jaw_center_pos = goal_obj_rotmat.dot(jaw_center_pos) + goal_obj_pos
        goal_jaw_center_rotmat = goal_obj_rotmat.dot(jaw_center_rotmat)
        
        approach_direction = approach_direction_list[0]
        if approach_direction is None:
            approach_direction = goal_jaw_center_rotmat[:, 2]
        approach_distance = approach_distance_list[0]
        if approach_distance is None:
            approach_distance = 0

        if toggle_gripper:
            self.gripper_s.fix_to(goal_obj_rotmat.dot(hnd_pos) + goal_obj_pos, goal_obj_rotmat.dot(hnd_rotmat))
            gripper_mesh = self.gripper_s.gen_meshmodel()
            gripper_mesh.attach_to(self.base)
            self.base.run()
            gripper_mesh.detach()
        
        if use_rrt:  # if use rrt, we shall find start and goal conf first and then perform rrt
            # approach linear
            seed_conf = jnt_values_bk
            conf_list_approach = self.PPP.inik_slvr.gen_rel_linear_motion(component_name=hand_name,
                                                                      goal_tcp_pos=goal_jaw_center_pos,
                                                                      goal_tcp_rotmat=goal_jaw_center_rotmat,
                                                                      direction=approach_direction,
                                                                      distance=approach_distance,
                                                                      obstacle_list=obstacle_list,
                                                                      granularity=ad_granularity,
                                                                      seed_jnt_values=seed_conf,
                                                                      type='sink',
                                                                      toggle_sphere=toggle_sphere)
            if conf_list_approach is None:
                print(f"Cannot generate the linear part of the holding approach motion!")
                self.robot_s.release(hand_name, objcm_copy, jawwidth_bk)
                self.robot_s.fk(component_name=hand_name, jnt_values=jnt_values_bk)
                if ing_list != []:
                    return None, None, None, None
                else:
                    return None, None, None
            
            # self.CC.visual_obj(obstacle_list)
            conf_list_middle = self.PPP.rrtc_planner.plan(component_name=hand_name,
                                                      start_conf=jnt_values_bk,
                                                      goal_conf=conf_list_approach[0],
                                                      obstacle_list=obstacle_list,
                                                      otherrobot_list=[],
                                                      ext_dist=.07,
                                                      max_iter=300)
            if conf_list_middle is None:
                print(f"Cannot generate the rrtc part of the holding approach motion!")
                self.robot_s.release(hand_name, objcm_copy, jawwidth_bk)
                self.robot_s.fk(component_name=hand_name, jnt_values=jnt_values_bk)
                if ing_list != []:
                    return None, None, None, None
                else:
                    return None, None, None

        else:  # if do not use rrt, we start from depart end to mid end and then approach from mid end to goal
            seed_conf = jnt_values_bk
            self.robot_s.fk(component_name=hand_name, jnt_values=seed_conf)
            mid_start_tcp_pos, mid_start_tcp_rotmat = self.robot_s.get_gl_tcp(hand_name)
            mid_goal_tcp_pos = goal_jaw_center_pos - approach_direction * approach_distance
            mid_goal_tcp_rotmat = goal_jaw_center_rotmat
            conf_list_middle = self.PPP.inik_slvr.gen_linear_motion(component_name=hand_name,
                                                                start_tcp_pos=mid_start_tcp_pos,
                                                                start_tcp_rotmat=mid_start_tcp_rotmat,
                                                                goal_tcp_pos=mid_goal_tcp_pos,
                                                                goal_tcp_rotmat=mid_goal_tcp_rotmat,
                                                                obstacle_list=obstacle_list,
                                                                granularity=ad_granularity,
                                                                seed_jnt_values=seed_conf,
                                                                toggle_sphere=toggle_sphere
                                                                )
            if conf_list_middle is None:
                print(f"Cannot generate the rrtc part of the holding approach motion!")
                self.robot_s.release(hand_name, objcm_copy, jawwidth_bk)
                self.robot_s.fk(component_name=hand_name, jnt_values=jnt_values_bk)
                if ing_list != []:
                    return None, None, None, None
                else:
                    return None, None, None
            # approach linear
            seed_conf = conf_list_middle[-1]
            conf_list_approach = self.PPP.inik_slvr.gen_rel_linear_motion(component_name=hand_name,
                                                                      goal_tcp_pos=goal_jaw_center_pos,
                                                                      goal_tcp_rotmat=goal_jaw_center_rotmat,
                                                                      direction=approach_direction,
                                                                      distance=approach_distance,
                                                                      obstacle_list=obstacle_list,
                                                                      granularity=ad_granularity,
                                                                      seed_jnt_values=seed_conf,
                                                                      type='sink',
                                                                      toggle_sphere=toggle_sphere)
            if conf_list_approach is None:
                print(f"Cannot generate the linear part of the holding approach motion!")
                self.robot_s.release(hand_name, objcm_copy, jawwidth_bk)
                self.robot_s.fk(component_name=hand_name, jnt_values=jnt_values_bk)
                if ing_list != []:
                    return None, None, None, None
                else:
                    return None, None, None
        
        
        jawwidthlist_approach = self.PPP.gen_jawwidth_motion(conf_list_approach, jaw_width)
        objpose_list_approach = self.PPP.gen_object_motion(component_name=hand_name,
                                                       conf_list=conf_list_approach,
                                                       obj_pos=rel_obj_pos,
                                                       obj_rotmat=rel_obj_rotmat,
                                                       type='relative')
        jawwidthlist_middle = self.PPP.gen_jawwidth_motion(conf_list_middle, jaw_width)
        objpose_list_middle = self.PPP.gen_object_motion(component_name=hand_name,
                                                     conf_list=conf_list_middle,
                                                     obj_pos=rel_obj_pos,
                                                     obj_rotmat=rel_obj_rotmat,
                                                     type='relative')
        self.robot_s.release(hand_name, objcm_copy, jawwidth_bk)
        
        #初期姿勢に戻る
        objcm_copy.set_pos(goal_obj_pos)
        objcm_copy.set_rotmat(goal_obj_rotmat)
        obstacle_list.append(objcm_copy)
        for conf_middle_num, conf_middle in enumerate(conf_list_middle[::-1]):
            start2approach_conf_list = self.rrtc_planner.plan(component_name=hand_name,
                                                              start_conf=conf_middle,
                                                              goal_conf=self.first_jnt_values[hand_name],
                                                              obstacle_list=obstacle_list,
                                                              ext_dist=.05,
                                                              max_time=500)
            if start2approach_conf_list is not None:
                reversed_middle = conf_list_middle[::-1]
                reversed_middle = reversed_middle[:conf_middle_num+1]
                break
        if start2approach_conf_list is None:
            print("ADPlanner: Cannot plan approach motion!\n初期姿勢に戻れない")
            if ing_list != []:
                return None, None, None, None
            else:
                return None, None, None
        
        jawwidthlist_last = self.PPP.gen_jawwidth_motion(start2approach_conf_list, jaw_width)
        objpose_list_last = self.PPP.gen_object_motion(component_name=hand_name,
                                                     conf_list=reversed_middle+start2approach_conf_list,
                                                     obj_pos=goal_obj_pos,
                                                     obj_rotmat=goal_obj_rotmat,
                                                     type='absolute')
        
        
        conf_list = conf_list + conf_list_middle + conf_list_approach + reversed_middle + start2approach_conf_list
        jawwidthlist = jawwidthlist + jawwidthlist_middle + jawwidthlist_approach + jawwidthlist_middle[:conf_middle_num+1] + jawwidthlist_last
        objpose_list = objpose_list + objpose_list_middle + objpose_list_approach + objpose_list_last
        seed_conf = conf_list[-1]
        if ing_list != []:
            ingpose_list = []
            for i, ing in enumerate(ing_list):
                ingpose_list_approach = self.PPP.gen_object_motion(component_name=hand_name,
                                                               conf_list=conf_list_approach,
                                                               obj_pos=ing_rel_list[i][0],
                                                               obj_rotmat=ing_rel_list[i][1],
                                                               type='relative')
                ingpose_list_middle = self.PPP.gen_object_motion(component_name=hand_name,
                                                             conf_list=conf_list_middle,
                                                             obj_pos=ing_rel_list[i][0],
                                                             obj_rotmat=ing_rel_list[i][1],
                                                             type='relative')
                ingpose_list_last = self.PPP.gen_object_motion(component_name=hand_name,
                                                               conf_list=reversed_middle+start2approach_conf_list,
                                                               obj_pos=ingpose_list_approach[-1][:3, 3],
                                                               obj_rotmat=ingpose_list_approach[-1][:3, :3],
                                                               type='absolute')
                ingpose_list.append(ingpose_list_middle+ingpose_list_approach+ingpose_list_last)
                self.robot_s.release(hand_name, ing_objcm_copy_list[i], jawwidth_bk)
            self.robot_s.release(hand_name, objcm_copy, jawwidth_bk)
            self.robot_s.fk(component_name=hand_name, jnt_values=jnt_values_bk)
            del objcm_copy
            return conf_list, jawwidthlist, objpose_list, ingpose_list
        self.robot_s.release(hand_name, objcm_copy, jawwidth_bk)
        self.robot_s.fk(component_name=hand_name, jnt_values=jnt_values_bk)
        del objcm_copy
        return conf_list, jawwidthlist, objpose_list
    
    def place_ingredients(self, obj_model, grasp_info, hand_name, area, obj_model_dic, jawwidth_bk, jnt_values_bk, rot_id=0):
        pos = area[1]
        # input(pos)
        area = area[0]
        # input(area)
        rotmat_list = [rm.rotmat_from_axangle([0, 0, 1], math.pi*rad/16) for rad in range(32)]
        for i, rot in enumerate(rotmat_list[rot_id:]):
            rotmat = rot
            self.CC.set_obj_pos(obj_model, pos, rotmat)
            check = self.CC.check_object_collision(obj_model, obj_model_dic)
            if check:
                obj_model.set_rgba([1, 0, 0.0, 1])
                # self.base.run()
                print('配置計画に失敗しました')
            else:
                obj_model.set_rgba([1, 1, 0.0, 1])
                # self.base.run()
                print('配置計画に成功しました')
                goal_homomat_list = [rm.homomat_from_posrot(area, rotmat)]
                obstacle_list = [obj_model_dic[key] for key in obj_model_dic.keys()]
                conf_list, jawwidth_list, objpose_list = self.place_motion(jawwidth_bk, jnt_values_bk, hand_name, obj_model, grasp_info, goal_homomat_list, obstacle_list=[], toggle_sphere=False, toggle_gripper=False)
                if conf_list == None:
                    print('動作計画に失敗しました')
                else:
                    return conf_list, jawwidth_list, objpose_list, i
        return None, None, None, 0
    
    def place_planning(self, place, obj_model, grasp_info, hand_name, available_area, obj_model_dic, jawwidth_bk, jnt_values_bk, area_id, rot_id):
        rotmat_list = [rm.rotmat_from_axangle([0, 0, 1], math.pi*rad/16) for rad in range(32)]
        for i, area in enumerate(available_area[place][area_id:]):
            # for high in range(2):
            #     area[1] += np.array([0, 0, 0.005])
            #     print(f'area:{i+area_id}')
            for j, rotmat in enumerate(rotmat_list):
                if i == 0 and j <= rot_id:
                    print(f'passしました{j}/{rot_id}')
                    continue
                self.CC.set_obj_pos(obj_model, area[1], rotmat)
                check = self.CC.check_object_collision(obj_model, obj_model_dic)
                if check:
                    obj_model.set_rgba([1, 0, 0.0, 1])
                    print('配置計画に失敗しました')
                    # obj_model.set_homomat(obj_pos_bk)
                    continue
                else:
                    obj_model.set_rgba([0, 1, 0.0, 1])
                    print('配置計画に成功しました')
                    # obj_model.set_homomat(obj_pos_bk)
                    goal_homomat_list = [rm.homomat_from_posrot(area[1], rotmat)]
                    obstacle_list = [obj_model_dic[key] for key in obj_model_dic.keys() if obj_model_dic[key] != obj_model]
                    conf_list, jawwidth_list, objpose_list = self.place_motion(jawwidth_bk, jnt_values_bk, hand_name, obj_model, grasp_info, goal_homomat_list, obstacle_list=obstacle_list)
                    if conf_list == None:
                        print('動作計画に失敗しました')
                        continue
                    else:
                        self.robot_s.fk(hand_name, conf_list[-1])
                        return conf_list, jawwidth_list, objpose_list, [area[0], area[1], rotmat], [i+area_id, j]
        print('動作計画が不可能なのでPicモーションに戻ります')
        return None, None, None, None, [0, 0]
    
    def Pic_Place_motion(self, hnd_name, objcm, start_conf, end_conf, grasp_info_list, goal_homomat_list, obstacle_dic):
        obstacle_list = [obstacle_dic[key] for key in obstacle_dic.keys()]
        conf_list, jawwidth_list, objpose_list = self.PPP.gen_pick_and_place_motion(  hnd_name=hnd_name,
                                                                                      objcm=objcm,
                                                                                      start_conf=start_conf,
                                                                                      end_conf=end_conf,
                                                                                      grasp_info_list=grasp_info_list,
                                                                                      goal_homomat_list=goal_homomat_list,
                                                                                      approach_direction_list=[np.array([0, 0, -1])] * len(goal_homomat_list),
                                                                                      approach_distance_list=[.05] * len(goal_homomat_list),
                                                                                      depart_direction_list=[np.array([0, 0, 1])] * len(goal_homomat_list),
                                                                                      depart_distance_list=[.05] * len(goal_homomat_list),
                                                                                      approach_jawwidth=None,
                                                                                      depart_jawwidth=None,
                                                                                      ad_granularity=.007,
                                                                                      use_rrt=True,
                                                                                      obstacle_list=obstacle_list,
                                                                                      use_incremental=False)
        return conf_list, jawwidth_list, objpose_list
    
    
    
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
                obs_copy.attach_to(self.base)
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
                              extraArgs=[self.robot_s,
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
        

    def animation_dict(self, motion_list, toggle_image=False):
        
        OMCM = ObjectModelConfigManager.ObjectModelConfigManager(self.base)
        obj_model_dic = OMCM.set_object_model(motion_list[-1][-2], motion_list[-1][-1])
        # input(motion_list[-1][3])
        
        robot_attached_list = []
        object_attached_list = []
        obstacle_attache_list = []
        counter = [0]
        motion_counter = [1]
        
        # input(obj_model_dic.keys())
        # 元の実験環境用の色。他の環境のオブジェクトはグレーで表示 / objects not listed (other environments) are drawn grey
        color_dic = defaultdict(lambda: [0.75,0.75,0.75,1], {"EO_000_C_010":[0.75,0.75,0.75,1], "EO_000_C_011":[0.75,0.75,0.75,1], 'EO_000_C_012':[0.75,0.75,0.75,1],
                     'EO_000_T_016':[0.75,0.75,0.75,1], 'EO_000_T_015':[0.75,0.75,0.75,1], 'EO_000_C_001':[0.75,0.75,0.75,1],
                     "EO_000_C_003":[0.75,0.75,0.75,1], 'EO_000_C_005':[0.75,0.75,0.75,1], 'EO_000_C_007':[0.75,0.75,0.75,1], 
                     'EO_000_F_002':[0, 0, 0, 0], 'EO_000_F_004':[0, 0, 0, 0], 'EO_000_F_006':[1,1,1,1], 
                     'EO_000_F_008':[1,0,0,1], 'EO_000_M_017':[0.75,0.75,0.75,1], 'EO_000_C_009':[0.75,0.75,0.75,1]})
        
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
        
        if toggle_image:
            while True:
                if counter[0] >= len(motion_list[motion_counter[0]][0]['lft_hnd']):
                    self.base.run()
                    counter[0] = 0
                    motion_counter[0] += 1
                    detach_all_objects()
                if motion_counter[0] >= len(motion_list):
                    motion_counter[0] = 1
        
                rgt_pose = motion_list[motion_counter[0]][0]['rgt_hnd'][counter[0]]
                lft_pose = motion_list[motion_counter[0]][0]['lft_hnd'][counter[0]]
                self.robot_s.fk('rgt_hnd', rgt_pose)
                self.robot_s.fk('lft_hnd', lft_pose)
                self.robot_s.jaw_to('rgt_hnd', motion_list[motion_counter[0]][1]['rgt_hnd'][counter[0]])
                self.robot_s.jaw_to('lft_hnd', motion_list[motion_counter[0]][1]['lft_hnd'][counter[0]])
                if counter[0] == 0 or counter[0] >= len(motion_list[motion_counter[0]][0]['lft_hnd'])-1:
                    robot_meshmodel = self.robot_s.gen_meshmodel()
                else:
                    robot_meshmodel = self.robot_s.gen_meshmodel(rgba=[0,0,1,0.1])
                robot_meshmodel.attach_to(self.base)
                robot_attached_list.append(robot_meshmodel)
                obj_key = list(motion_list[motion_counter[0]][2].keys())
                obj_key = obj_key[0]
                obj_pose = motion_list[motion_counter[0]][2][obj_key][counter[0]]
                obj_copy = obj_model_dic[obj_key].copy()
                obj_copy.set_homomat(obj_pose)
                obj_copy.set_rgba(color_dic[obj_key])
                obj_copy.attach_to(self.base)
                object_attached_list.append(obj_copy)
                obstacle_list = [[key, obj_model_dic[key]] for key in obj_model_dic.keys() if key != obj_key]
                for obs in obstacle_list:
                    obs_copy = obs[1].copy()
                    obs_copy.set_pos(motion_list[motion_counter[0]][3][obs[0]][0])
                    obs_copy.set_rotmat(motion_list[motion_counter[0]][3][obs[0]][1])
                    obs_copy.set_rgba(color_dic[obs[0]])
                    obs_copy.attach_to(self.base)
                    obstacle_attache_list.append(obs_copy)
                counter[0] += 1
                
                
    


    
        def update(robot_s,
                   motion_list,
                   obj_model_dic,
                   robot_attached_list,
                   object_attached_list,
                   obstacle_attache_list,
                   counter,
                   motion_counter,
                   color_dic,
                   task
                   ):
            if counter[0] >= len(motion_list[motion_counter[0]][0]['lft_hnd']):
                counter[0] = 0
                motion_counter[0] += 1
            if motion_counter[0] >= len(motion_list):
                motion_counter[0] = 1
            if len(robot_attached_list) != 0:
                    detach_all_objects()
                
            rgt_pose = motion_list[motion_counter[0]][0]['rgt_hnd'][counter[0]]
            lft_pose = motion_list[motion_counter[0]][0]['lft_hnd'][counter[0]]
            robot_s.fk('rgt_hnd', rgt_pose)
            robot_s.fk('lft_hnd', lft_pose)
            robot_s.jaw_to('rgt_hnd', motion_list[motion_counter[0]][1]['rgt_hnd'][counter[0]])
            robot_s.jaw_to('lft_hnd', motion_list[motion_counter[0]][1]['lft_hnd'][counter[0]])
            robot_meshmodel = robot_s.gen_meshmodel()
            robot_meshmodel.attach_to(self.base)
            robot_attached_list.append(robot_meshmodel)
            obj_key_list = list(motion_list[motion_counter[0]][2].keys())
            for obj_key in obj_key_list:
                obj_pose = motion_list[motion_counter[0]][2][obj_key][counter[0]]
                obj_copy = obj_model_dic[obj_key].copy()
                obj_copy.set_homomat(obj_pose)
                obj_copy.set_rgba(color_dic[obj_key])
                obj_copy.attach_to(self.base)
                object_attached_list.append(obj_copy)
            obstacle_list = [[key, obj_model_dic[key]] for key in obj_model_dic.keys() if key not in obj_key_list]
            for obs in obstacle_list:
                obs_copy = obs[1].copy()
                obs_copy.set_pos(motion_list[motion_counter[0]][3][obs[0]][0])
                obs_copy.set_rotmat(motion_list[motion_counter[0]][3][obs[0]][1])
                obs_copy.set_rgba(color_dic[obs[0]])
                obs_copy.attach_to(self.base)
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
                              extraArgs=[self.robot_s,
                                         motion_list,
                                         obj_model_dic,
                                         robot_attached_list,
                                         object_attached_list,
                                         obstacle_attache_list,
                                         counter,
                                         motion_counter,
                                         color_dic],
                              appendTask=True,)
    
        # アニメーションを実行
        self.base.run()
        
        def stop_animation():
            taskMgr.remove(task_name)  # タスクを停止
            print("Animation stopped")
        
        stop_animation()
        del OMCM
    
    def visual_obj(self, model_list, toggle_detach=False):
        for model in model_list:
            model.set_rgba([0, 0, 1, 1])
            model.attach_to(self.base)
            # model.change_cdprimitive_type(cdprimitive_type="box")
            # model.show_cdmesh()
        self.base.run()
        if toggle_detach is False:
            for model in model_list:
                model.detach()
            
            
    def __del__(self):
        del self.robot_s
        del self.first_jnt_values
        del self.gen_model
        del self.PPP
        del self.base
        del self.gripper_s
        del self.rrtc_planner

    
if __name__ == '__main__':
    import time
    import visualization.panda.world as wd
    import modeling.geometric_model as gm
    import modeling.collision_model as cm
    import grasping.annotation.utils as gutil
    import numpy as np
    import basis.robot_math as rm
    import sys
    import File_management as Fm
    sys.path.append(Fm.join_path_and_filename(Fm.get_current_path(), 'wrs'))
    import visualization.panda.world as wd
    import modeling.geometric_model as gm
    import modeling.collision_model as cm
    import grasping.planning.antipodal as gpa
    import robot_sim.end_effectors.gripper.robotiq85.robotiq85 as robotiq
    import basis.robot_math as rm
    import math
    import numpy as np
    import robot_sim.robots.ur3e_dual.ur3e_dual as ur
    import File_management as Fm
    import WRS_object_check_collision as Wocc

    base = wd.World(cam_pos=[5, 0, 5.0], lookat_pos=[0, 0, .2])
    gm.gen_frame().attach_to(base)
    objcm = cm.CollisionModel('path/to/new_research/stl/pan.stl')
    objcm.set_pos(np.array([0.5, -0.35, 0.8]))
    objcm.set_rotmat(rm.rotmat_from_axangle([0, 0, 1], math.pi))
    objcm.attach_to(base)
    robot_s = ur.UR3EDual()
    robot_s.gen_meshmodel().attach_to(base)
    CC = Wocc.Collision_Checker(base, {}, robot_s)
    manipulator_name = 'rgt_arm'
    hand_name = 'rgt_hnd'
    start_conf = robot_s.get_jnt_values(manipulator_name)
    goal_homomat_list = []
    for i in range(3):
        goal_pos = np.array([0.2, -0.45, 1.1]) + np.array([0, i * .1, 0])
        # goal_rotmat = rm.rotmat_from_axangle([0, 1, 0], math.pi / 2)
        goal_rotmat = np.eye(3)
        goal_homomat_list.append(rm.homomat_from_posrot(goal_pos, goal_rotmat))
        tmp_objcm = objcm.copy()
        tmp_objcm.set_rgba([1, 0, 0, .3])
        tmp_objcm.set_homomat(rm.homomat_from_posrot(goal_pos, goal_rotmat))
        tmp_objcm.attach_to(base)
    grasp_info_list = Fm.load_pickle_file('./stl/grasp/pan.pickle')
    pp_planner = WRSA_motion_storage(base, robot_s, CC)
    conf_list, jawwidth_list, objpose_list, grasp_id = pp_planner.Pic_motion(hand_name, objcm, robot_s.get_jnt_values(hand_name), robot_s.get_jnt_values(hand_name), grasp_info_list, goal_homomat_list, [])
    
    if conf_list is not None:
        pp_planner.animation(hand_name, objcm, conf_list, jawwidth_list, objpose_list, [])
    else:
        input('把持できませんでした')

    for obj_pos in objpose_list:
        tmp_objcm = objcm.copy()
        tmp_objcm.set_rgba([1, 0, 0, .3])
        tmp_objcm.set_homomat(obj_pos)
        tmp_objcm.attach_to(base)
    base.run()


    # animation
    robot_attached_list = []
    object_attached_list = []
    counter = [0]


    def update(robot_s,
                hand_name,
                objcm,
                robot_path,
                jawwidth_path,
                obj_path,
                robot_attached_list,
                object_attached_list,
                counter,
                task):
        if counter[0] >= len(robot_path):
            counter[0] = 0
        if len(robot_attached_list) != 0:
            for robot_attached in robot_attached_list:
                robot_attached.detach()
            for object_attached in object_attached_list:
                object_attached.detach()
            robot_attached_list.clear()
            object_attached_list.clear()
        pose = robot_path[counter[0]]
        robot_s.fk(hand_name, pose)
        robot_s.jaw_to(hand_name, jawwidth_path[counter[0]])
        robot_meshmodel = robot_s.gen_meshmodel()
        robot_meshmodel.attach_to(base)
        robot_attached_list.append(robot_meshmodel)
        obj_pose = obj_path[counter[0]]
        objb_copy = objcm.copy()
        objb_copy.set_homomat(obj_pose)
        objb_copy.attach_to(base)
        object_attached_list.append(objb_copy)
        counter[0] += 1
        return task.again


    taskMgr.doMethodLater(0.01, update, "update",
                          extraArgs=[robot_s,
                                      hand_name,
                                      objcm,
                                      conf_list,
                                      jawwidth_list,
                                      objpose_list,
                                      robot_attached_list,
                                      object_attached_list,
                                      counter],
                          appendTask=True)
    base.run()
    
    
    