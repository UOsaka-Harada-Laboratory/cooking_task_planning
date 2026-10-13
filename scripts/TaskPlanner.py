# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 18:22:03 2024

@author: user
"""
# import Video_Analysis
import EnvObjectNode
import FOONGenerator
import TaskExecutionValidator
import copy
import networkx as nx
import json
import os
import datetime
import pickle

class TaskPlanner:
    def __init__(self):
        self.EO = EnvObjectNode.EnvObjectNode()
        self.FOON = FOONGenerator.FOONGenerator()
        self.FOON_graph = nx.DiGraph()
        
    def main(self, G, Object_folder, save_folder):
        print('start')
        """環境オブジェクトノードの初期設定"""
        EO_json_path = self.EO.main(G, Object_folder)
        Graph_enviroment_node = copy.deepcopy(self.EO.enviroment_node)
        FOON_graph = copy.deepcopy(self.FOON_graph)
        action_num = 0
        save_data = []
        error_log = []
        togle = False
        save_prompt = []
        error_num = 0
        
        """タスクプランニングの実行"""
        #目標オブジェクトノード１つ１つにタスク計画をかけていく
        for i, t in enumerate(G):
            error_state = f"{i}番目のタスク計画start"
            print(error_state)
            target = json.dumps(nx.node_link_data(t), indent=4)
            # input(target)
            self.task_plan, user_input = self.FOON.main(json.dumps(nx.node_link_data(Graph_enviroment_node), indent=4), target, save_file_path=fr'{save_folder}/prompt_{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")}')
            while error_state != "No error":
                self.prompt = self.FOON.gpt.prompt
                self.TE = TaskExecutionValidator.TaskExecutionValidator(Graph_enviroment_node, user_input, FOON_graph)
                os.makedirs(save_folder, exist_ok=True)
                with open(os.path.join(save_folder, 'error_log_instancego.pickle'), 'wb') as file:
                    pickle.dump(error_log, file)


                error_state, action_num = self.TE.main(self.task_plan, action_num)
                self.task_list = self.TE.task_list
                print(error_state)
                if error_state != "No error":
                    self.task_plan = self.FOON.error(error_state, togle, save_file_path=fr'{save_folder}/prompt_{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")}')
                    error_log.append([self.TE.Env_Grapf, self.TE.FOON, self.task_list, self.task_plan, self.TE.Functional_unit_list, error_state, self.prompt])
                    os.makedirs(save_folder, exist_ok=True)
                    # Define the file path
                    file_path = os.path.join(save_folder, 'error_log.pickle')
                    # Save the mes object to the file
                    with open(file_path, 'wb') as file:
                        pickle.dump(error_log, file)
                    Graph_enviroment_node = copy.deepcopy(self.EO.enviroment_node)
                    FOON_graph = copy.deepcopy(self.FOON_graph)
                    togle = True
                    error_num += 1
                else:
                    Graph_enviroment_node = copy.deepcopy(self.TE.Env_Grapf)
                    save_prompt.append(self.prompt)
                    if togle == True:
                        first_two = self.prompt[:-(8+2*error_num)]
                        last_one = self.prompt[-1:]
                    else:
                        first_two = self.prompt
                        last_one = []
                    self.prompt = first_two + last_one
                    self.FOON.gpt.prompt = self.prompt
                    self.EO.enviroment_node = copy.deepcopy(self.TE.Env_Grapf)
                    error_state = "No error"
                    FOON_graph = copy.deepcopy(self.TE.FOON)
                    self.FOON_graph = copy.deepcopy(FOON_graph)
                    save_data.append([self.TE.FOON, self.TE.Env_Grapf, self.task_list, self.TE.Functional_unit_list])

                    os.makedirs(save_folder, exist_ok=True)
                    # Define the file path
                    file_path = os.path.join(save_folder, 'result.pickle')
                    # Save the mes object to the file
                    with open(file_path, 'wb') as file:
                        pickle.dump(save_data, file)
                    togle = False
                    error_num = 0
                
                os.makedirs(save_folder, exist_ok=True)
                # Define the file path
                file_path = os.path.join(save_folder, 'prompt_list.pickle')
                # Save the mes object to the file
                with open(file_path, 'wb') as file:
                    pickle.dump(save_prompt, file)
    
if __name__ == '__main__':
    with open(os.path.join('./images/Object_folder', 'G_list.pickle'), 'rb') as file:
        G = pickle.load(file)
    TP = TaskPlanner()
    Object_folder = './images/Object_folder'
    save_folder   = './images/FOON'
    first_two = TP.main(G, Object_folder, save_folder)
    task_plan = TP.task_plan
    prompt = TP.prompt
    task_list = TP.task_list