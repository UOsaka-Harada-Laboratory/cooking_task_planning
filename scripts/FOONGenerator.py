# -*- coding: utf-8 -*-
"""
Created on Wed Aug 28 16:47:57 2024

@author: user
"""

import File_management as Fm
import GPT_manipulation as Gm
import networkx as nx
import json

class FOONGenerator():
    def __init__(self, prompt=[]):
        self.gpt = Gm.GPT_manipulation()
        self.gpt.prompt = prompt
        
    def error(self, error_state, togle, save_file_path=fr'C:/Users/ryuka/research/new_research/images/FOON評価実験用/images_2025_01_21_02_38_47_908151\FOON\prompt_{Fm.get_current_time()}', system_prompt=r'C:/Users/ryuka/research\new_research\prompt\error_recovery'):
        if togle == False:
            error_prompt = self.gpt.prompt[-2:]
            # system_prompt = Fm.load_txt_file(system_prompt)
            self.gpt.text2prompt(system_prompt, save_file_path)
            self.gpt.prompt += error_prompt
            # self.gpt.prompt_role_system_add(system_prompt)
        self.gpt.prompt_role_user_add(error_state)
        # Fm.save_pickle_file(save_file_path, f'{Fm.get_current_time()}.pickle', self.gpt.prompt)
        ans = self.gpt.GPT4o_exe()
        print(ans)
        self.gpt.prompt_role_assistant_add(ans)
        Fm.save_text_file(Fm.join_path_and_filename(save_file_path, '..'), f'{Fm.get_current_time()}.txt', ans)
        return ans
        
    def main(self, EG, graph, Fewshot_folder_path=r'C:/Users/ryuka/research/new_research/prompt\taskplanning_without_Area', save_file_path=fr'C:\Users\user\new_research\images\Few_shot_sample\FOON\prompt_{Fm.get_current_time()}'):
        ###タスク計画
        # system = Fm.load_txt_file(r'C:\Users\user\new_research\prompt\foon\system.txt')
        # self.gpt.prompt_role_system_add(system)
        # user = Fm.load_txt_file(r'C:\Users\user\new_research\prompt\foon\user1.txt')
        # self.gpt.prompt_role_user_add(user)
        # ans = self.gpt.GPT4o_exe()
        # self.gpt.prompt_role_assistant_add(ans)
        # Fm.save_json_file(r'C:\Users\user\new_research\prompt\foon', 'kekka.json', self.gpt.prompt)
        ###FOON作成
        if self.gpt.prompt == []:
            self.gpt.load_prompt_from_pickle(f'{Fewshot_folder_path}/taskplan_setup.pickle')
        # self.gpt.prompt_role_system_add(Fm.load_txt_file(Fm.join_path_and_filename(Fewshot_folder_path, 'system.txt')))
        user_input = f'<Initial state of object node>\n{EG}\n</Initial state of object node>\n\n<Target state of object node>\n{graph}\n</Target state of object node>'
        # self.gpt.prompt_role_user_add(user_input, r'C:/Users/ryuka/research/new_research/prompt\taskplanning2\スクリーンショット (16).png')
        self.gpt.prompt_role_user_add(user_input)
        ans = self.gpt.GPT4o_exe()
        self.gpt.prompt_role_assistant_add(ans)
        print(ans)
        Fm.save_text_file(save_file_path, f'{Fm.get_current_time()}.txt', ans)
        Fm.save_text_file(Fewshot_folder_path, f'{Fm.get_current_time()}.txt', user_input)
        
        # system = Fm.load_txt_file(r'C:\Users\user\new_research\prompt\taskplanning2\system.txt')
        # self.gpt.prompt_role_system_add(system)
        # user = Fm.load_txt_file(r'C:\Users\user\new_research\prompt\taskplanning2\user1.txt')
        # self.gpt.prompt_role_user_add(user, r'C:\Users\user\new_research\prompt\taskplanning2\スクリーンショット (16).png')
        # ans = self.gpt.GPT4o_exe()
        # self.gpt.prompt_role_assistant_add(ans)
        # print(ans)
        # Fm.save_text_file(r'C:\Users\user\new_research\prompt\taskplanning2', f'{Fm.get_current_time()}.txt', ans)
        # Fm.save_text_file(r'C:\Users\user\new_research\prompt\taskplanning2', f'{Fm.get_current_time()}.json', self.gpt.prompt)
        
        
        return ans, user_input
        
def graph_to_json_str(G):
    """
    NetworkXのグラフをJSON形式の文字列に変換する関数

    Parameters:
    G (networkx.Graph): 変換するNetworkXグラフ

    Returns:
    str: JSON形式の文字列
    """
    # グラフをJSON形式の辞書に変換
    graph_data = nx.node_link_data(G)
    
    # 辞書をJSON形式の文字列に変換
    json_str = json.dumps(graph_data, indent=4)
    
    return json_str
        
if __name__ == '__main__':
    save_file_path = fr'C:\Users\user\new_research\images\Few_shot_sample\FOON\prompt_{Fm.get_current_time()}.pickle'
    EG = Fm.load_json_as_txt(r'C:\Users\user\new_research\images\Few_shot_sample\Object_folder\../Environmental_Object_Node\EO000.json')
    Fewshot_folder_path = r'C:\Users\user\new_research\prompt\taskplanning_without_Area - コピー'
    turget = Fm.load_pickle_file(r'C:\Users\user\new_research\images\Few_shot_sample\Object_folder\G_list.pickle')    
    graph = graph_to_json_str(turget[0])
    input(graph)
    FG = FOONGenerator()
    ans = FG.main(EG, graph, Fewshot_folder_path, save_file_path)
    prompt = FG.gpt.prompt