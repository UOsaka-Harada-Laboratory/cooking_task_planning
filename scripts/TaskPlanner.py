# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 18:22:03 2024

@author: user
"""
# import Video_Analysis
import MainFunctionUnit_Generator
import EnvObjectNode
import GenerateFoon
import FOONGenerator
import TaskExecutionValidator
import File_management as Fm
import copy
import networkx as nx

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
            turget = Fm.graph_to_json_str(t)
            # input(turget)
            self.task_plan, user_input = self.FOON.main(Fm.graph_to_json_str(Graph_enviroment_node), turget, save_file_path=fr'{save_folder}\prompt_{Fm.get_current_time()}')
            while error_state != "No error":
                self.prompt = self.FOON.gpt.prompt
                self.TE = TaskExecutionValidator.TaskExecutionValidator(Graph_enviroment_node, user_input, FOON_graph)
                Fm.save_pickle_file(save_folder, 'error_log_instancego.pickle', error_log)
                error_state, action_num = self.TE.main(self.task_plan, action_num)
                self.task_list = self.TE.task_list
                print(error_state)
                if error_state != "No error":
                    self.task_plan = self.FOON.error(error_state, togle, save_file_path=fr'{save_folder}\prompt_{Fm.get_current_time()}')
                    error_log.append([self.TE.Env_Grapf, self.TE.FOON, self.task_list, self.task_plan, self.TE.Functional_unit_list, error_state, self.prompt])
                    Fm.save_pickle_file(save_folder, 'error_log.pickle', error_log)
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
                    Fm.save_pickle_file(save_folder, 'result.pickle', save_data)
                    togle = False
                    error_num = 0
                Fm.save_pickle_file(save_folder, 'prompt_list.pickle', save_prompt)
            
                    
        
            
        
    
if __name__ == '__main__':
    G = Fm.load_pickle_file(Fm.join_path_and_filename(r'C:/Users/ryuka/research/new_research/images/牛丼_発表用2/Object_folder', 'G_list_R.pickle'))
    TP = TaskPlanner()
    Object_folder = r'C:/Users/ryuka/research/new_research/images/牛丼_発表用2/Object_folder'
    save_folder = r'C:/Users/ryuka/research/new_research/images/牛丼_発表用2\FOON'
    first_two = TP.main(G, Object_folder, save_folder)
    task_plan = TP.task_plan
    prompt = TP.prompt
    task_list = TP.task_list