# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 02:26:18 2024

@author: user
"""

import networkx as nx
import math
import matplotlib.pyplot as plt
import File_management as Fm
import graph_key_search as gks
from itertools import product
import copy
import basis.robot_math as rm
import numpy as np
import random

class TreeGraph:
    def __init__(self):
        self.tree = nx.DiGraph()

    def add_node(self, node, attributes_name_list, attribute_list):
        """ノードを追加し、属性も設定する"""
        self.tree.add_node(node)
        if attributes_name_list != []:
            for i, name in enumerate(attributes_name_list):
                self.tree.nodes[node][name] = attribute_list[i]

    def add_edge(self, parent, child):
        """エッジを追加する（親子関係を定義する）"""
        self.tree.add_edge(parent, child)

    def get_tree_levels(self):
        """ツリーの各ノードの層（深さ）を計算する"""
        levels = {}
        for node in self.tree.nodes:
            level = self.get_node_level(node)
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
        return levels

    def get_node_level(self, node):
        """ノードの層（深さ）を再帰的に取得"""
        if self.tree.in_degree(node) == 0:  # 根ノードの場合
            return 0
        parent = list(self.tree.predecessors(node))[0]
        return self.get_node_level(parent) + 1
    
    def Change_node_obj_pos(self, obj_id, area, pos):
        for key in self.tree.nodes.keys():
            if 'obj_pos_dic' in self.tree.nodes[key].keys():
                self.tree.nodes[key]['obj_pos_dic'][obj_id][0] = pos

    
    def get_nodes_from_level(self, level):
        """この関数は入力されたlevelのノードのidをリスト形式で返す関数です"""
        return [node for node in self.tree.nodes if self.get_node_level(node) == level]
    
    def trim_tree_from_level(self, level):
        """この関数は入力されたレベル以下の木グラフのノードを削除します。
        
        tree: self.tree (networkx.Graph または DiGraph)
        各ノードは "level" という属性を持っていると仮定します。
    
        Args:
            level (int): 残したい最大レベル（このレベル以下のノードを削除）
    
        Returns:
            None: self.tree を直接変更する
        """
        # level 以下のノードを取得
        nodes_to_remove = [node for node, data in self.tree.nodes(data=True) if data.get("level", float("inf")) >= level]
    
        # ノードを削除
        self.tree.remove_nodes_from(nodes_to_remove)
    
    def visualize(self):
        """ツリーグラフを層ごとに可視化する"""
        
        # ツリーの深さを計算して層ごとにノードを配置
        levels = self.get_tree_levels()

        # 各層のノードの配置位置を決める
        pos = {}
        for level, nodes in levels.items():
            x_position = level  # x位置（層ごとに位置を変える）
            y_lenght = len(nodes)/2
            for i, node in enumerate(nodes):
                # x位置をノード番号で均等に分ける
                pos[node] = (x_position, i-y_lenght)
                print(i)

        # グラフを描画
        nx.draw(self.tree, pos, with_labels=False, arrows=True, node_size=50, node_color="lightblue", font_size=10)
        plt.show()

    def get_root(self):
        """ルートノードを返す（入次数がゼロのノード）"""
        for node in self.tree.nodes:
            if self.tree.in_degree(node) == 0:
                return node
        return None

    def get_children(self, node):
        """指定したノードの子ノードを返す"""
        return list(self.tree.successors(node))

    def get_parent(self, node):
        """指定したノードの親ノードを返す"""
        parents = list(self.tree.predecessors(node))
        if parents:
            return parents[0]
        return None
    
    def get_leaf_nodes(self, max_level=1000):
        "ツリーの中から最下層のノードを探す関数"
        # リーフノードを格納するリスト
        leaf_nodes = []
        level = 0
    
        # グラフの各ノードをチェック
        for node in self.tree.nodes:
            # ノードの子ノードが存在しない場合、リーフノードとして追加
            if self.tree.out_degree(node) == 0:  # 有向グラフの場合
                leaf_nodes.append(node)
                num = self.tree.nodes[node]['level']
                if level < num:
                    leaf_nodes = []
                    level = self.tree.nodes[node]['level']
                    
            elif self.tree.degree(node) == 1 and self.tree.in_degree(node) == 1:  # 無向グラフの場合
                leaf_nodes.append(node)
    
        return leaf_nodes, level-1
    
    

    
    def extract_tasks_from_graph(self, FOON):
        """グラフからタスクを読み取る関数
        入力:FOON
        出力:taskリスト
        """
        actions_key = [key for key in FOON.nodes.keys() if '_A' in key]
        task_list = [[key, FOON.nodes[key]] for key in actions_key]
        return task_list
    
    def remove_node_and_descendants(self, node):
        """
        Remove a node and all its descendants from a tree.
        
        Parameters:
        - tree: A networkx DiGraph representing the tree.
        - node: The node to be removed along with its descendants.
        """
        # Get all descendants of the node
        descendants = nx.descendants(self.tree, node)
        # Add the node itself to the set of nodes to be removed
        nodes_to_remove = descendants.union({node})
        # Remove the nodes from the tree
        self.tree.remove_nodes_from(nodes_to_remove)
    
    def add_multiple_children_to_node(self, id_list, attribute_name, attribute_list, root_id):
        prier_id_list = [] 
        r_id = random.choice(root_id)
        for i, id_ in enumerate(id_list):
            id_+= '_'+r_id
            self.add_node(id_, attribute_name, attribute_list[i])
            self.add_edge(r_id, id_)
            prier_id_list.append(id_)
        return prier_id_list
            
    
    def create_pic_motion_tree(self, task, EG, ava_area, parent_id, task_num):
        """Pic_motionのツリーを作成する関数
        """
        target_object_key = gks.find_target_node_by_label(EG, task['object'])
        target_node = EG.nodes[target_object_key]
        grasp_info_list = Fm.load_pickle_file(target_node['grasp_info_list'])
        id_list = [f'{task_num}_Pic_{i}' for i in range(len(grasp_info_list))]
        attribute_name = ['grasp_id', 'level']
        attribute_list = [[grasp_info_list[i], task_num] for i in range(len(grasp_info_list))]
        prier_id_list = self.add_multiple_children_to_node(id_list, attribute_name, attribute_list, root_id=parent_id)
        return prier_id_list
        
    def create_place_motion_tree(self, task, EG, ava_area, parent_id, FOON, task_num):
        out_object_key = list(FOON.successors(task[0]))
        target_object_key = [key for key in out_object_key if FOON.nodes[key]['label'] == task[1]['object']]
        target_EG_key = gks.find_target_node_by_label(EG, task[1]['object'])
        place = FOON.nodes[target_object_key[0]]['place']
        input(place)
        if FOON.nodes[target_object_key[0]]['type'] == 'ingredients':
            turget_container_key = FOON.nodes[target_object_key[0]]['container'][1]
            target_area = [[EG.nodes[turget_container_key]['area'], EG.nodes[turget_container_key]['pos']]]
            rotmat = [math.pi/8*i for i in range(16)]
        elif FOON.nodes[target_object_key[0]]['machine'] != ['', '']:
            turget_machine_key = FOON.nodes[target_object_key[0]]['machine'][1]
            target_area = [[EG.nodes[turget_machine_key]['area'], EG.nodes[turget_machine_key]['pos']+np.array([0, 0, 0.055])]]
            rotmat = [math.pi/8*i for i in range(16)]
        else:
            target_area = ava_area[place]
            rotmat = [math.pi/8*i for i in range(16)]
        comb = gks.generate_combinations(target_area, rotmat)
        id_list = [f'{task_num}_Place_{i}' for i in range(len(comb))]   
        attribute_name = ['area', 'rotmat', 'level']
        attribute_list = [[[i[0][0], i[0][1]+np.array([0, 0, 0.01])], rm.rotmat_from_axangle([0, 0, 1], i[1]), task_num] for i in comb]
        prier_id_list = self.add_multiple_children_to_node(id_list, attribute_name, attribute_list, root_id=parent_id)
        return prier_id_list
    
    def create_cook_motion_tree(self, task, EG, ava_area, parent_id, task_num):
        """Pic_motionのツリーを作成する関数
        """
        target_object_key = gks.find_target_node_by_label(EG, 'stove')
        target_node = EG.nodes[target_object_key]
        grasp_info_list = Fm.load_pickle_file(target_node['grasp_info_list'])
        id_list = [f'{task_num}_Cook_{i}' for i in range(len(grasp_info_list))]
        attribute_name = ['grasp_id', 'level']
        attribute_list = [[grasp_info_list[i], task_num] for i in range(len(grasp_info_list))]
        prier_id_list = self.add_multiple_children_to_node(id_list, attribute_name, attribute_list, root_id=parent_id)
        return prier_id_list
    
    def create_cut_motion_tree(self, task, EG, ava_area, parent_id, task_num):
        """Pic_motionのツリーを作成する関数
        """
        target_object_key = gks.find_target_node_by_label(EG, 'stove')
        target_node = EG.nodes[target_object_key]
        attribute_name = ['rotmat', 'level']
        rotmat = [math.pi/8*i for i in range(16)]
        id_list = [f'{task_num}_Cut_{i}' for i in range(len(rotmat))]
        attribute_list = [[rotmat[i], task_num] for i in range(len(rotmat))]
        prier_id_list = self.add_multiple_children_to_node(id_list, attribute_name, attribute_list, root_id=parent_id)
        return prier_id_list
    
    def create_pour_motion_tree(self, task, EG, ava_area, parent_id, task_num):
        """Pic_motionのツリーを作成する関数
        """
        target_object_key = gks.find_target_node_by_label(EG, 'stove')
        target_node = EG.nodes[target_object_key]
        attribute_name = ['rotmat', 'level']
        rotmat = [math.pi/8*i for i in range(16)]
        id_list = [f'{task_num}_Pour_{i}' for i in range(len(rotmat))]
        attribute_list = [[rotmat[i], task_num] for i in range(len(rotmat))]
        prier_id_list = self.add_multiple_children_to_node(id_list, attribute_name, attribute_list, root_id=parent_id)
        return prier_id_list
        
    def create_mix_motion_tree(self, task, EG, ava_area, parent_id, task_num):
        """Pic_motionのツリーを作成する関数
        """
        target_object_key = gks.find_target_node_by_label(EG, 'stove')
        target_node = EG.nodes[target_object_key]
        attribute_name = ['rotmat', 'level']
        rotmat = [math.pi/20*i - math.pi/4 for i in range(10)]
        id_list = [f'{task_num}_Mix_{i}' for i in range(len(rotmat))]
        attribute_list = [[rotmat[i], task_num] for i in range(len(rotmat))]
        prier_id_list = self.add_multiple_children_to_node(id_list, attribute_name, attribute_list, root_id=parent_id)
        return prier_id_list
    
    def assign_tasks_to_tree_nodes(self, task, EG, ava_area, parent_id, FOON, task_num):
        """taskを入力するとツリーを更新する関数
        """
        action = task[1]['label']
        if action == 'Pic':
            id_list = self.create_pic_motion_tree(task[1], EG, ava_area, parent_id, task_num)
        elif action == 'Place':
            id_list = self.create_place_motion_tree(task, EG, ava_area, parent_id, FOON, task_num)
        elif action == 'Cook':
            id_list = self.create_cook_motion_tree(task[1], EG, ava_area, parent_id, task_num)
        elif action == 'Cut':
            id_list = self.create_cut_motion_tree(task[1], EG, ava_area, parent_id, task_num)
        elif action == 'Pour':
            id_list = self.create_pour_motion_tree(task[1], EG, ava_area, parent_id, task_num)
        elif action == 'Mix':
            id_list = self.create_mix_motion_tree(task[1], EG, ava_area, parent_id, task_num)
        else:
            input('未実装')
        return id_list    
      
            

    def main(self, FOON, EG, ava_area):
        """入力されたFOONに対して木グラフを作成する関数
        入力：FOON, 環境ノード, 配置可能エリア
        """
        input([ava_area, copy.deepcopy(EG)])
        self.add_node('root', ['ava_area', 'EG'], [ava_area, copy.deepcopy(EG)])
        
        "グラフからタスクを呼び出す"
        task_list = self.extract_tasks_from_graph(FOON, EG)
        
        
        "タスクのオブジェクトから木のノードへの振り分け"
        parent_id = ['root']
        for task_num, task in enumerate(task_list[:2]):
            id_list = self.assign_tasks_to_tree_nodes(task, EG, ava_area, parent_id, FOON, task_num)
            parent_id = id_list
            self.visualize()
        
    
if __name__ == '__main__':
    EG = Fm.load_pickle_file(r'C:/Users/Shoichi/ryu/new_research\images\牛丼_資料作成用\motion_tree\EG.pickle')
    ava_area = Fm.load_pickle_file(r'C:/Users/Shoichi/ryu/new_research\images\牛丼_資料作成用\motion_tree\ava_area.pickle')
    resulet_pickle = Fm.load_pickle_file(r'C:/Users/Shoichi/ryu/new_research\images\牛丼_資料作成用/FOON\result.pickle')
    FOON = [result[0] for result in resulet_pickle]
    save_folder = r'C:/Users/Shoichi/ryu/new_research\images\牛丼_資料作成用\object_placement'
    TG = TreeGraph()
    TG.main(FOON[0], EG, ava_area)
    