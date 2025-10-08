# -*- coding: utf-8 -*-
"""
Created on Wed Aug  7 17:52:25 2024

@author: user
"""
import File_management as Fm
from graphviz import Digraph
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import random


class EnvObjectNode:
    def __init__(self):
        self.enviroment_node = nx.DiGraph()
        self.ingredients_node = []
        self.liquid_ingredients_node = []
        self.powder_ingredients_node = []
        self.container_node = []
        self.tool_node = []
        self.machine_node = []
        self.tray_node = []
        self.pinch_bowl_node = []
        self.cup_node = []
    
    def node_dyeing(self, node):
        ###１つのノードを入力し、分割する
        if node['type'] == 'ingredients':
            if 'liquid' in node['physical_state']:
                self.liquid_ingredients_node.append(node['label'])
            elif 'powder' in node['physical_state']:
                self.powder_ingredients_node.append(node['label'])
            else:
                self.ingredients_node.append(node['label'])
        elif node['type'] == 'container':
            self.container_node.append(node['label'])
        elif node['type'] == 'tool':
            self.tool_node.append(node['label'])
        elif node['type'] == 'machine':
            self.machine_node.append(node['label'])

    def get_object_from_turget_G(self, G):
        ###グラフリスト内のグラフを取り出す
        for i, G_i in enumerate(G):
            for j, key in enumerate(G_i.nodes.keys()):
                if 'A' not in key:
        ###ノード別け
                    self.node_dyeing(G_i.nodes[key])
        ###リストの整理
        self.liquid_ingredients_node = list(set(self.liquid_ingredients_node))
        self.powder_ingredients_node = list(set(self.powder_ingredients_node))
        self.ingredients_node = list(set(self.ingredients_node))
        self.ingredients_node = [item for item in self.ingredients_node if item not in (self.liquid_ingredients_node + self.powder_ingredients_node)]
        self.container_node = list(set(self.container_node))
        self.tool_node = list(set(self.tool_node))
        self.machine_node = list(set(self.machine_node))
        # input(self.ingredients_node)
        # input(self.liquid_ingredients_node)
        # input(self.powder_ingredients_node)
        # input(self.container_node)
        # input(self.tool_node)
        # input(self.machine_node)
        
    def generate_Container_Name(self):
        for i, name in enumerate(self.ingredients_node):
            tray_name = 'tray_' + str(i).zfill(3)
            self.tray_node.append(tray_name)
        for i, name in enumerate(self.powder_ingredients_node):
            pinch_bowl_name = 'pinch_bowl_' + str(i).zfill(3)
            self.pinch_bowl_node.append(pinch_bowl_name)
        for i, name in enumerate(self.liquid_ingredients_node):
            cup_name = 'cup_' + str(i).zfill(3)
            self.cup_node.append(cup_name)
            
        # input(self.tray_node)
        # input(self.pinch_bowl_node)
        # input(self.cup_node)
        
    def set_Attributes(self, Container, ID, Ingredients, Label, Machine, Place, equipment_status, cooking_method, cutting_style, physical_state, Type, temp, area, tool=["", ""]):
        self.enviroment_node.add_node(ID, **temp)
        self.enviroment_node.nodes[ID]['label'] = Label
        self.enviroment_node.nodes[ID]['container'] = Container
        self.enviroment_node.nodes[ID]['id'] = ID
        self.enviroment_node.nodes[ID]['ingredients'] = Ingredients
        self.enviroment_node.nodes[ID]['machine'] = Machine
        self.enviroment_node.nodes[ID]['tool'] = tool
        self.enviroment_node.nodes[ID]['place'] = Place
        self.enviroment_node.nodes[ID]['equipment_status'] = equipment_status
        self.enviroment_node.nodes[ID]['cooking_method'] = cooking_method
        self.enviroment_node.nodes[ID]['cutting_style'] = cutting_style
        self.enviroment_node.nodes[ID]['physical_state'] = physical_state
        self.enviroment_node.nodes[ID]['type'] = Type
        self.enviroment_node.nodes[ID]['step'] = 0
        self.enviroment_node.nodes[ID]['node_state'] = 'latest'
        self.enviroment_node.nodes[ID]['area'] = area
        
    def get_available_area(self, path):
        points = Fm.load_csv_file(path)
        self.r_area = []
        self.l_area = []
        self.b_area = []
        for i, p in enumerate(points):
            if p[3] == 0:
                self.b_area.append(i)
            elif p[3] == 1:
                self.r_area.append(i)
            elif p[3] == 2:
                self.l_area.append(i)
        # input(f'b:{self.b_area}')
        # input(f'r:{self.r_area}')
        # input(f'l:{self.l_area}')
                
    def get_random_value(self, list_i, num, seed=1):
        """
        リスト内からランダムで指定された数の値を取り出し、取り出した値をリストから消す関数。
    
        Parameters:
        list_i (list): 元のリスト
        num (int): 取り出す値の数
        seed (int, optional): ランダムシード値
    
        Returns:
        list: 取り出された値のリスト
        """
        # シード値を設定
        if seed is not None:
            random.seed(seed)
        
        # 取り出す数がリストの長さを超えないようにする
        if num > len(list_i):
            raise ValueError("num is larger than the number of elements in the list")
        
        # ランダムに値を取り出す
        selected_values = random.sample(list_i, num)
        
        # 取り出した値を元のリストから削除
        for value in selected_values:
            list_i.remove(value)
        
        return selected_values
        
    def set_Object_Location(self):
        ###nodeのテンプレートを呼び出し
        current_path = Fm.get_current_path()
        temp_folder = Fm.join_path_and_filename(current_path, 'prompt/template/node.pickle')
        temp = Fm.load_pickle_file(temp_folder)
        obj_num = 0
        
        self.get_available_area(r'C:/Users/ryuka/research/new_research/wrs_reachability/ave_point2.csv')
        
        ###ingredientsノードをセット
            ###液体の材料
        liq_area = self.get_random_value(self.l_area, len(self.liquid_ingredients_node))
        for name, cup, area in zip(self.liquid_ingredients_node, self.cup_node, liq_area):
            ###設定
            ID_I = 'EO_'+str(0).zfill(3)+'_' + 'F'+'_' +str(obj_num).zfill(3)
            obj_num += 1
            ID_C = 'EO_'+str(0).zfill(3)+'_' + 'C'+'_' +str(obj_num).zfill(3)
            obj_num += 1
            # self.set_Attributes(Container, ID, Ingredients, Label, Machine, Place, equipment_status, cooking_method, cutting_style, physical_state, Type, temp, area):
            self.set_Attributes([cup, ID_C], ID_I, ['', ''], name, ['', ''], 'left_storage', '', '', '', 'liquid', 'ingredients', temp, area)
            self.set_Attributes(['', ''], ID_C, [[name, ID_I]], cup, ['', ''], 'left_storage', 'dirty', '', '', '', 'container', temp, area)
            
            ###パウダーの材料
        powder_area = self.get_random_value(self.l_area, len(self.powder_ingredients_node))
        for name, cup, area in zip(self.powder_ingredients_node, self.pinch_bowl_node, powder_area):
            ###設定
            ID_I = 'EO_'+str(0).zfill(3)+'_' + 'F'+'_' +str(obj_num).zfill(3)
            obj_num += 1
            ID_C = 'EO_'+str(0).zfill(3)+'_' + 'C'+'_' +str(obj_num).zfill(3)
            obj_num += 1
            self.set_Attributes([cup, ID_C], ID_I, ['', ''], name, ['', ''], 'left_storage', '', '', '', 'powder', 'ingredients', temp, area)
            self.set_Attributes(['', ''], ID_C, [[name, ID_I]], cup, ['', ''], 'left_storage', 'dirty', '', '', '', 'container', temp, area)
            
            ###それ以外の材料
        other_area = self.get_random_value(self.l_area, len(self.ingredients_node))
        for name, cup, area in zip(self.ingredients_node, self.tray_node, other_area):
            ###設定
            ID_I = 'EO_'+str(0).zfill(3)+'_' + 'F'+'_' +str(obj_num).zfill(3)
            obj_num += 1
            ID_C = 'EO_'+str(0).zfill(3)+'_' + 'C'+'_' +str(obj_num).zfill(3)
            obj_num += 1
            self.set_Attributes([cup, ID_C], ID_I, ['', ''], name, ['', ''], 'left_storage', '', '', 'whole', 'solid', 'ingredients', temp, area)
            self.set_Attributes(['', ''], ID_C, [[name, ID_I]], cup, ['', ''], 'left_storage', 'dirty', '', '', '', 'container', temp, area)
    
        ###containerノードをセット
        ###一般的なものも追加
        general_container = ['cutting board', 'bowl0', 'bowl1', 'frying pan']
        for gc in general_container:
            if gc not in self.container_node:
                self.container_node.append(gc)
        right_area = {'cutting board':[1, 2, 3, 5, 6, 7], 'bowl0':[10, 11, 15, 16], 'bowl1':[13, 14, 18, 19], 'frying pan':[12, 13, 17, 18]}
        for con in self.container_node:
            ###設定
            # input(con)
            ID = 'EO_'+str(0).zfill(3)+'_' + 'C' +'_' +str(obj_num).zfill(3)
            if con in right_area.keys():
                self.set_Attributes(['', ''], ID, [['', '']], con, ['', ''], 'right_storage', 'clean', '', '', '', 'container', temp, right_area[con])
            else:
                # self.set_Attributes(None, ID, None, con, None, 'right_storage', 'empty', 'container', temp, None)         
                self.set_Attributes(['', ''], ID, [['', '']], con, ['', ''], 'right_storage', 'clean', '', '', '', 'container', temp, None)
            obj_num += 1
        
        ###toolノードをセット
        tool_list = ['knife', 'spatula']
        for tl in tool_list:
            if tl not in self.tool_node:
                self.tool_node.append(tl)
        
        if self.tool_node is not []:
            right_area = [[21, 22], [26, 27]]
            for tool, area in zip(self.tool_node, right_area):
                ###設定
                ID = 'EO_'+str(0).zfill(3)+'_' + 'T'+'_'  +str(obj_num).zfill(3)
                self.set_Attributes(['', ''], ID, [['', '']], tool, ['', ''], 'right_storage', 'clean', '', '', '', 'tool', temp, area)
                # self.set_Attributes(None, ID, None, tool, None, 'right_storage', '', 'tool', temp, area)
                obj_num += 1
        
        ###マシンノードをセット
        if self.machine_node is not []:
            for machine in self.machine_node:
                ###設定
                ID = 'EO_'+str(0).zfill(3)+'_' + 'M'+'_' +str(obj_num).zfill(3)
                self.set_Attributes(['', ''], ID, [['', '']], machine, ['', ''], 'workspace', 'off', '', '', '', 'machine', temp, [])
                obj_num += 1
                
        ###ハンドノードをセット
        hand_list = ['right_hand', 'left_hand']
        for hand in hand_list:
            ###設定
            ID = 'EO_'+str(0).zfill(3)+'_' + 'H' +'_' +str(obj_num).zfill(3)
            self.set_Attributes(['', ''], ID, [['', '']], hand, ['', ''], '', 'empty', '', '', '', 'hand', temp, ['', ''])
            obj_num += 1

            
    def Graph_visualization(self, dot, file_name, save_folder):
        # NetworkXグラフからGraphvizのグラフに変換
        A = nx.nx_agraph.to_agraph(dot)


        # ノードの属性を追加
        for node in A.nodes():
            node_attr = A.get_node(node).attr
            attributes = dot.nodes[node]

            # 属性のtypeが'motion'の場合の処理
            if attributes.get('type') == 'motion':
                node_attr['shape'] = 'ellipse'
            else:
                node_attr['shape'] = 'rectangle'  # デフォルトの形状

            # ラベルの設定
            label_str = "\n".join([f"{key}: {value}" for key, value in attributes.items() if key in ['Label', 'States', 'Place', 'Ingredients', 'Container']])
            node_attr['label'] = label_str
            node_attr['style'] = 'filled'
            node_attr['fillcolor'] = 'lightblue'
            node_attr['fontcolor'] = 'black'
            node_attr['fontsize'] = '14'


        # エッジの属性を追加
        for u, v, data in dot.edges(data=True):
            if 'weight' in data:
                A.get_edge(u, v).attr['label'] = f"Weight: {data['weight']}"
                A.get_edge(u, v).attr['fontsize'] = '12'  # エッジラベルのフォントサイズ

        # レイアウトを指定（例: dot、neato、fdpなど）
        A.layout(prog='dot')

        # グラフ画像をJPEG形式で保存
        A.draw(f"{save_folder}/{file_name}.jpg")
        
    def main(self, G, Object_folder):
        ###環境オブジェクトノードから必要とする材料や調理器具の名前を取得
        self.get_object_from_turget_G(G)
        
        ###食材に関してcontainerノードの名前を定義
        self.generate_Container_Name()
        
        ###オブジェクトの配置場所を定義
        self.set_Object_Location()
        
        ###環境オブジェクトノードを保存
        Enviroment_folder = Fm.join_path_and_filename(Object_folder, '../Environmental_Object_Node')
        Fm.save_json_file(Enviroment_folder, 'EO000.json', self.enviroment_node)
        # self.Graph_visualization(self.enviroment_node, 'graph.jpg', r'C:\Users\user\new_research\images\Few_shot_sample\Environmental_Object_Node')
        
        return Fm.join_path_and_filename(Enviroment_folder, 'EO000.json')
        
if __name__ == '__main__':
    G = Fm.load_pickle_file(Fm.join_path_and_filename(r'C:/Users/ryuka/research/new_research/images/FOON評価実験用/images_2025_01_21_02_38_47_908151/Object_folder', 'G_list.pickle'))
    EO = EnvObjectNode()
    Object_folder = r'C:/Users/ryuka/research/new_research/images/FOON評価実験用/images_2025_01_21_02_38_47_908151/Object_folder'
    EO_json_path = EO.main(G, Object_folder)
    graph = EO.enviroment_node
    