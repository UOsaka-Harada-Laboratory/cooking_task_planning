# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 21:09:14 2024

@author: user
"""
import re


class TaskPreprocessor():
    def __init__(self, data):
        self.task_str = ''
        self.task_list = []
        self.data = data
        
        
        
    def get_task(self, task_txt):
        """この関数は入力された指定の形式のテキストから指定された部分を取り出しリスト形式で取得します
        ###入力形式:<質問>
        1. 鶏肉を切る際の具体的な切り方（例：一口大、細切りなど）を教えてください。
        </質問>
    
        <area選定理由>
        1. cutting boardが 1, 2, 3, 5, 6, 7 に配置されているため
        2. cutting boardはメインの切る動作に関連するためworkspaceに配置。areaは隣接する6マスが必要なので59, 60, 65, 66, 71, 72を選定。まな板は使いやすいように横向に配置
        3. chickenが 127 に配置されているため
        4. chickenはcutting boardに配置するため、areaは59, 60, 65, 66, 71, 72を選定
        5. knifeが 21, 22 に配置されているため
        6. cut動作はareaの指定なし
        7. knifeは初期配置が 21, 22 だったため、再度同じ場所に戻す
        8. bowlが 10, 11, 15, 16 に配置されているため
        9. Pourも両手での操作が必要なためbowlをworkspaceに置く。bowlは隣接した４マスが必要なので61, 62, 67,68を選択
        10. sakeが 89 に配置されているため
        11. bowlにsakeを注ぐためareaは61, 62, 67,68
        12. chickenが  59, 60, 65, 66, 71, 72  に配置されているため
        13. bowlにchickenを入れるためareaは61, 62, 67,68
        </area選定理由>
    
        <タスク>
        1. Pic | cutting board | right_Storage | 1, 2, 3, 5, 6, 7 | right-hand
        2. Place | cutting board | workspace | 59, 60, 65, 66, 71, 72 | right-hand
        3. Pic | chicken | tray_001 | 127 | left-hand
        4. Place | chicken | cutting board | 59, 60, 65, 66, 71, 72 | left-hand
        5. Pic | knife | shelf | 21, 22 | right-hand
        6. Cut | chicken | 一口大 | both-hands
        7. Place | knife | shelf | 21, 22 | right-hand
        8. Pic | bowl | right_Storage | 10, 11, 15, 16 | right-hand
        9. Place | bowl | workspace | 61, 62, 67,68 | right-hand
        10. Pic | sake | cup_005 | 89 | left-hand
        11. Pour | sake | bowl | 61, 62, 67,68 | left-hand
        12. Pic | chicken | cutting board | 59, 60, 65, 66, 71, 72 | both-hands
        13. Pour | chicken | bowl | 61, 62, 67,68 | both-hands
        </タスク>
    
        出力：[task1, task2, task3, ...]
        """
    
        # パターンマッチングで<タスク>～</タスク>を抜き出し改行ごとにリスト化
        task_text = re.findall(r"<Task>(.*?)</Task>", task_txt, re.DOTALL)
        if 'None' in task_text[0]:
            return [], 'No error'
        task_text = task_text[0].strip().split('\n') if task_text else []
    
        task_dic = {}
        task_list = []
    
        for task in task_text:
            # .と|を基準にリストに分割
            task_i_list1 = re.split(r'\s*\.\s*', task.strip())
            task_i_list2 = re.split(r'\s*\|\s*', task_i_list1[1].strip())
            task_i_list = task_i_list1[:1] + task_i_list2
    
            # 最初の要素はタスク番号なので、それをキーとして辞書を作成
            task_number = task_i_list[0].split('.')[0].strip()
            task_dic[task_number] = {}
    
            if task_i_list[1] in ["Pic", "Place"]:
                attribute = ['action', 'object', 'space', 'hand']
            elif task_i_list[1] == "Cut":
                attribute = ['action', 'object', 'cutting method', 'hand']
            elif task_i_list[1] == "Pour":
                attribute = ['action', 'object', 'targetContainer', 'hand']
            elif task_i_list[1] == "Mix":
                attribute = ['action', 'object', 'tool', 'container' , 'hand']
            elif task_i_list[1] == "Cook":
                attribute = ['action', 'object', 'container', 'heat_level', 'machine', 'hand']
            else:
                print(f"{task_i_list[1]} is not a configured action. Please select the action from [Pic, Place, Pour, Cut, Cook, Mix]")
                return [], f"{task_i_list[1]} is not a configured action. Please select the action from [Pic, Place, Pour, Cut, Cook, Mix]"
            
            if len(attribute) == len(task_i_list)-1:
                for i, att in enumerate(attribute):
                    task_dic[task_number][att] = task_i_list[i + 1]
            else:
                return [], f'Wrong output format for {task}, expected {len} elements, please correct it.'
    
            task_list.append(task_dic[task_number])
            task_dic = {}
    
        return task_list, 'No error'
    
    
    def check_output_format(self, task_list):
    
        """
        LLMからの出力が正しいかどうかをチェックする関数です
        入力:task_list
        出力:error
        """
        #チェック項目の定義
        allow_action = ['Pic', 'Place', 'Pour', 'Mix', 'Cut', 'Cook']
        object_name = [self.data.Env_Grapf.nodes[key]['label'] for key in self.data.Env_Grapf.nodes.keys() ]
        allow_place = ['left_storage', 'workspace', 'right_storage']
        hand = ['right_hand', 'left_hand', 'both_hands']
        
        """チェック開始"""
        for task in task_list:
            if 'object' in task.keys():
                if '[' in task['object'] and task['action'] in ['Mix', 'Cook']:
                    task['object'] = task['object'].replace('[', '').replace(']', '').split(', ')
                elif '[' in task['object']:
                    error_state = f'''<Wrong task>\n{str(task)}\n</Wrong task>\n<The reason>\nFor actions other than ['Mix', 'Cook'], please answer with a single object.\n</The reason>'''
                    input(error_state)
                    return error_state
                #actionが定義道理か確認
                if task['action'] not in allow_action:
                    error_state = f'''<Wrong task>\n{str(task)}\n</Wrong task>\n<The reason>\n{task["action"]} is an action that cannot be used by the robot. Available actions are {allow_action}. Please create the work plan again.\n</The reason>'''
                    input(error_state)
                    return error_state
                elif isinstance(task['object'], list):
                    for obj in task['object']:
                        if obj not in object_name:
                            error_state = f'''<Wrong task>\n{str(task)}\n</Wrong task>\n<The reason>\nThe object {obj} does not exist in the environment. The objects in the environment are {object_name}, so please select the object from the list.\n</The reason>'''
                            input(error_state)
                            return error_state
                elif task['object'] not in object_name:
                    error_state = f'''<Wrong task>\n{str(task)}\n</Wrong task>\n<The reason>\nThe object {task["object"]} does not exist in the environment. The objects in the environment are {object_name}, so please select the object from the list.\n</The reason>'''
                    input(error_state)
                    return error_state
                elif 'space' in task.keys() and (task['space'] not in object_name and task['space'] not in allow_place):
                    error_state = f'''<Wrong task>\n{str(task)}\n</Wrong task>\n<The reason>\nThere is no available location named {task["space"]}. Please select a location from {object_name+allow_place}.\n</The reason>'''
                    input(error_state)
                    return error_state
                elif task['hand'] not in hand:
                    error_state = f'''<Wrong task>\n{str(task)}\n</Wrong task>\n<The reason>\nThere is no hand named {task["hand"]}. Please select a hand from {hand}.\n</The reason>'''
                    input(error_state)
                    return error_state
        error_state = 'No error'
        input(error_state)
        return error_state
    
    def main(self, task):
        self.task_str = task
        task_list, error_state = self.get_task(task)
        self.task_list = task_list
        if error_state !=  'No error':
            return error_state, 0
        elif task_list == []:
            return 'No error', 0
        
        ###タスク計画の形式確認(必要があれば追加予定)
        error_state = self.check_output_format(task_list)
        if error_state !=  'No error':
            return error_state, 0
        
        return 'No error', 0
    
    