# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 06:02:15 2024

@author: user
"""
from itertools import product

def find_target_node_by_label(G, label):
    target_key = [key for key in G.nodes.keys() if G.nodes[key]['label'] == label]
    return target_key[0]

def ava_area_del(ava_area, place, area_num):
    area_list = ava_area[place]
    ava_area[place] = [area for area in area_list if area[0] != area_num]
    return ava_area

def generate_combinations(list1, list2):
    """
    入力された2つのリストからすべての組み合わせのリストを返す関数
    
    Args:
    list1 (list): 最初のリスト
    list2 (list): 2番目のリスト
    
    Returns:
    list: 全ての組み合わせを含むリスト
    """
    return list(product(list1, list2))