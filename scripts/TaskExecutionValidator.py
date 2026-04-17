# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 22:59:11 2024

@author: user
"""
import File_management as Fm
import re
import numpy as np
import networkx as nx
import GraphManager as GM
import TaskPreprocessor as TPr
import FunctionUnitBuilder as FUB


class TaskExecutionValidator:
    def __init__(self, G, user_input, FOON, reachability_file_path=r'C:/Users/ryuka/research/new_research/wrs_reachability'):
        # self.reachability = Fm.load_json_as_graph(reachability_file_path)
        self.Env_Grapf = G
        self.First_Env = G
        self.FOON = FOON
        # input(self.reachability)
        self.Functional_unit_list = []
        self.user_input = user_input
        self.task = []
    
    
    def main(self, task, action_num):
        print("start")

        
        """タスクの前処理
        入力:taskの文字列
        出力:taskのリストと間違いがあった場合はerror_state"""
        self.TPr = TPr.TaskPreprocessor(self)
        error_state, i = self.TPr.main(task)
        self.task_str = self.TPr.task_str
        self.task_list = self.TPr.task_list
        
        if error_state !=  'No error':
            return error_state, action_num
        elif self.task_list == []:
            return error_state, action_num
        
        
        """タスクプランニングから機能ユニットに変換
        入力:task_plan, action_num
        出力:error_state, action_num"""
        self.FUB = FUB.FunctionUnitBuilder(self)
        error_state, i = self.FUB.Functional_unit_with_variables(self.task_list, action_num)
        
        ###機能ユニット用い実行可否判定
        # self.evaluate_unit_feasibility()
        
        if error_state !=  'No error':
            return error_state, action_num
        
        ###FOONをグラフ化
        GM.visualize_graph_with_graphviz(self.FOON, ['label', 'ingredients', 'container', 'place'])
        
        return error_state, i
    
            
if __name__ == "__main__":
    ###FOONジェネレータの出力はタスク計画のpath
    task_plan_path = "/path/to/FOON/2024_11_12_10_52_52_305705.txt"
    task = Fm.load_txt_file(task_plan_path)
    input(task)
    pickle = Fm.load_pickle_file('/path/to/FOON/result.pickle')
    action_num = [key for key in pickle[0].nodes.keys() if 'A' in key]
    foon = pickle[0]
    EG = pickle[1]
    user_input = Fm.load_txt_file('/path/to/prompt/taskplanning_without_Area/2024_11_12_10_52_52_306713.txt')
    TEV = TaskExecutionValidator(G=EG, user_input=user_input, FOON=foon)
    error_state, i = TEV.main(task, len(action_num)+1)
    G = TEV.Env_Grapf
    Functional_unit_list = TEV.Functional_unit_list
    FOON = TEV.FOON
    
    
    
    