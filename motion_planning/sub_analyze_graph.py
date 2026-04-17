# -*- coding: utf-8 -*-
"""
Created on Sun Dec 29 10:24:10 2024

@author: Shoichi
"""

import File_management as Fm
import networkx as nx

def load_graph(file_path):
    graph = Fm.load_pickle_file(file_path)
    return graph

def get_parent(node, graph):
    """指定したノードの親ノードを返す"""
    parents = list(graph.predecessors(node))
    if parents:
        return parents[0]
    return None

def get_robot_motion_list(node, graph):
    node_list = [node]
    parent = ''
    while True:
        parent = get_parent(node, graph)
        if parent == None:
            break
        else:
            node_list.append(parent)
            node = parent
    node_list.reverse()
    return [[graph.nodes[n]['conf_list'], graph.nodes[n]['jawwidth_list'], graph.nodes[n]['obj_list'], graph.nodes[n]['obj_pos_dic'], change_graph_path(graph.nodes[n]['EG'])] for n in node_list]

def get_robot_motion_list_onlyhand(node, graph):
    node_list = [node]
    parent = ''
    while True:
        parent = get_parent(node, graph)
        if parent == None:
            break
        else:
            node_list.append(parent)
            node = parent
    node_list.reverse()
    return [[graph.nodes[n]['conf_list'], graph.nodes[n]['jawwidth_list']] for n in node_list]


def change_graph_path(graph, old_path='path/to/old', new_path='/path/to/new'):
    """
    `grasp_info_list` および `stl_path` に含まれるパス情報のうち、`old_path` を `new_path` に置き換える関数。

    Parameters:
        graph (nx.Graph or nx.DiGraph): 変更対象のグラフ
        old_path (str): 置換前のパスの基準部分
        new_path (str): 置換後のパスの基準部分

    Returns:
        nx.Graph or nx.DiGraph: 修正後のグラフ
    """
    for key in graph.nodes.keys():
        # grasp_info_list が存在し、かつリストである場合
        if 'grasp_info_list' in graph.nodes[key] and isinstance(graph.nodes[key]['grasp_info_list'], str):
            graph.nodes[key]['grasp_info_list'] = graph.nodes[key]['grasp_info_list'].replace(old_path, new_path)


        # stl_path が存在し、かつ文字列である場合
        if 'stl_path' in graph.nodes[key] and isinstance(graph.nodes[key]['stl_path'], str):
            graph.nodes[key]['stl_path'] = graph.nodes[key]['stl_path'].replace(old_path, new_path)

    return graph


def get_last_motion_node(graph):
    """
    木グラフのすべてのノードを調べて、最も深い `level` を持ち、
    `conf_list` を属性として持つノードのキーを返す関数。
    
    Parameters:
        graph (nx.Graph or nx.DiGraph): 探索対象のグラフ

    Returns:
        node (any or None): 最も深い `level` を持つ `conf_list` 属性を持つノードのキー。
                            該当ノードがない場合は None を返す。
    """
    max_level = float('-inf')
    last_motion_node = None

    for node, attrs in graph.nodes(data=True):
        if 'level' in attrs and 'conf_list' in attrs:
            if attrs['level'] > max_level:
                max_level = attrs['level']
                last_motion_node = node

    return last_motion_node

if __name__ == '__main__':
    file_path = '/path/to/object_placement/完成.pickle'
    graph = load_graph(file_path)
    node = get_last_motion_node(graph)
    motion_list = get_robot_motion_list(node, graph)
    Fm.save_pickle_file('path/to/object_placement', 'motion_list.pickle', motion_list)
    motion_list = get_robot_motion_list_onlyhand(node, graph)
    Fm.save_pickle_file('path/to/object_placement', 'motion_list_exe.pickle', motion_list)

    # motion_list = get_robot_motion_list('4_Place_10_3_Pic_11_2_Place_333_1_Pic_6_root', graph)
    # base = wd.World(cam_pos=[5,0,3],lookat_pos=[0,0,1])
    # Ms = Motion_storage.WRSA_motion_storage(base)
    # Ms.animation_dict(motion_list)