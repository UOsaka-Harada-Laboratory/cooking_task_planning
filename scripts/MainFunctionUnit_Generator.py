import ast
import re
import os
import pickle
import networkx as nx
import GPT_manipulation as GPT
import matplotlib.pyplot as plt

from graphviz import Digraph
from networkx.drawing.nx_agraph import graphviz_layout

class MainFunctionUnit_Generator():
    def __init__(self):
        self.G_list = []
        self.gpt = GPT.GPT_manipulation()
        self.Target_Object_list = []
        self.save_folder_path = ''

    def extract_number(self, filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else None
    
    def word2code(self, ans):
        data = ast.literal_eval(ans)
        return data
        
    def Object_Creation_Error_Detector(self, ans):
        # input(type(ans[0]['object']))
        if type(ans[0]['object']) == 'list':
            for i, obj in enumerate(ans[0]['object']):
                if obj['ingredients'] is None and obj['container'] is None:
                    self.gpt.prompt_role_assistant_add(ans)
                    self.gpt.prompt_role_user_add('ingredientsは必ずcontainerの上にあるようにしてください。つまりingredientsがオブジェクトに含まれる場合は必ず, containerオブジェクトも含めてください')
                    responce = self.gpt.GPT4o_exe()
                    return False, responce
        return True, ans
    
    def estimateTargetState(self, img_list, prompt_path, save_file_path, word_list, save_folder_path):
        pickle_file_path = sorted(os.listdir(save_folder_path))
        if pickle_file_path is not None:
            if "Target_Object_list.pickle" in pickle_file_path:
                with open(os.path.join(save_folder_path, "Target_Object_list.pickle")) as file:
                    self.Target_Object_list = pickle.load(file)
                list_num = len(self.Target_Object_list)
            else:
                list_num=0
        else:
            list_num=0

        for i, img_name in enumerate(sorted(img_list, key=self.extract_number)[list_num:]):
            i = i + list_num
            print(f"\n-----------------{i+1}/{len(img_list)}-----------------\n")
            img_path = os.path.join(input_folder, img_name)
            ###gptによる目標オブジェクト状態推定
            if i == 0:
                self.gpt.text2prompt(prompt_path, save_file_path)
            # input(len(word_list))
            # input(self.gpt.prompt)
            if i < len(word_list):
                ans = self.gpt.Target_Object_user_input(V_title, img_path, word_list, i, temp_file_path=r"C:/Users/ryuka/research/new_research/prompt/template\temp.txt" )
            else:
                continue
            ans = self.word2code(ans)
            # input(f'ans:{ans}')
            # input(f'ans : {ans}, thpe : {type(ans)}')
            ###エラー検出
            flag, res = self.Object_Creation_Error_Detector(ans)
            if flag == False:
                ans = res
                input(f'エラーが出ました。')
                input(ans)
            ###文字のコード化処理
            self.Target_Object_list.append([img_name, ans])
            
            os.makedirs(save_folder_path, exist_ok=True)
    
            # Define the file path
            file_path = os.path.join(save_folder_path, 'Target_Object_list.pickle')
    
            # Save the mes object to the file
            with open(file_path, 'wb') as file:
                pickle.dump(self.Target_Object_list, file)
        
            print(f"Data saved to {file_path}")

    def Graph_visualization(self, dot, file_name, ignore_empty=True):
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
            valid_labels = [
                f"{key}: {value}" for key, value in attributes.items()
                if key in ['label', 'ingredients', 'physical_state', 'cutting_style', 
                            'cooking_method', 'container', 'place', 'machine', 'equipment_status']
                and (not ignore_empty or value not in ([], ''))  # ignore_empty=Trueなら空リストや空文字を除外
            ]
            if valid_labels:
                node_attr['label'] = "\n".join(valid_labels)

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
        A.draw(f"{self.save_folder_path}/{file_name}.eps")

    def select_ids_by_object_type(self, obj):
        if obj['type'] == 'ingredients':
            return 'F'
        elif obj['type'] == 'container':
            return 'C'
        elif obj['type'] == 'machine':
            return 'M'
        elif obj['type'] == 'tool':
            return 'T'

    def Generate_Target_Object_node(self, object_list, object_ID, motion):
        """
        This function creates object nodes for a FOON using NetworkX.
        The object_list contains objects and their attributes as shown below.
        This function generates respective object nodes from this object list using NetworkX and creates directed edges from the motion node to each object node.
        
        Example object_list:
        [
            {
             "label": "cucumber",            
             "type": "ingredients",            
             "states": ["sliced"],            
             "ingredients": None,            
             "container": ["cutting board"],        
             "place": "workspace",            
             "machine": None            
            },
            {
             "label": "cutting board",
             "type": "container",
             "states": ["filled"],
             "ingredients": ["cucumber"],
             "container": None,
             "place": "workspace",
             "machine": None
            }
        ]
        """
        dot = nx.DiGraph()
        
        # Motion node
        object_ID_num = object_ID + '_' + 'A' + '_' + str(0).zfill(3)
        label = motion
        type_ = 'motion'
        node_attributes = {
            "id": object_ID_num,
            "label": label,
            "type": type_
        }
        dot.add_node(object_ID_num, **node_attributes)
        
        input(object_list)
        input(object_ID)
        
        # Add object nodes and create edges from motion node to each object node
        for i, obj in enumerate(object_list):
            #オブジェクトの種類よってID別け
            input(obj)
            sub_id = self.select_ids_by_object_type(obj)
            obj_ID_num = object_ID + '_' + sub_id + '_' + str(i).zfill(3)
            # input(f"obj:{obj}, i:{i}")
            label = obj['label']
            type_ = obj['type']
            # ingredients = ', '.join(obj['ingredients'])
            ingredients = obj['ingredients']
            physical_state = obj['physical_state']
            cutting_style = obj['cutting_style']
            cooking_method = obj['cooking_method']
            # container = ', '.join(obj['container'])
            container = obj['container']
            place = obj['place']
            machine = obj['machine']
            equipment_status = obj['equipment_status']
            node_attributes = {
                "id": obj_ID_num,
                "label": label,
                "type": type_,
                "ingredients": ingredients,
                "physical_state": physical_state,
                "cutting_style": cutting_style,
                "cooking_method": cooking_method,
                "container": container,
                "place" : place,
                "machine" : machine,
                "equipment_status" : equipment_status
            }
            dot.add_node(obj_ID_num, **node_attributes)
            
            # Create directed edge from motion node to object node
            dot.add_edge(object_ID_num, obj_ID_num)
            
        return dot
    
##    
    def Target_Object_node(self, Target_Object_list, save_folder_path):
        self.save_folder_path = save_folder_path
        for i, Target_Object in enumerate(Target_Object_list):
            # input(Target_Object)
            object_ID = f'TO_{str(i).zfill(3)}'
            # input(Target_Object[1])
            # input(Target_Object[1][0]['object'])
            if Target_Object[1][0]['object'] != None and Target_Object[1][0]['object'] != 'None':
                print(f'---------------{i}/{len(Target_Object_list)-1}-------------------------')
                if i == 23 or i == 24:
                    continue
                self.G_list.append(self.Generate_Target_Object_node(Target_Object[1][0]['object'], object_ID, Target_Object[1][0]['motion']))
            else:
                continue

        os.makedirs(save_folder_path, exist_ok=True)
    
        # Define the file path
        file_path = os.path.join(save_folder_path, 'G_list.pickle')

        # Save the mes object to the file
        with open(file_path, 'wb') as file:
            pickle.dump(self.G_list, file)
    
        print(f"Data saved to {file_path}")
    
    def check_same_graph(self, G, H):
        G_node_list = [[G.nodes[k]['label'], G.nodes[k]['id']] for k in G.nodes.keys()]
        H_node_list = [[H.nodes[k]['label'], H.nodes[k]['id']] for k in H.nodes.keys()]
        G_node_list = sorted(G_node_list, key=lambda x:x[0])
        H_node_list = sorted(H_node_list, key=lambda x:x[0])
        # input(f"====================\n\nG:{G_node_list[:]}, \n\nH:{H_node_list[:]}")
        if [i[0] for i in G_node_list] == [i[0] for i in H_node_list]:
            # input("OK")
            for i, (G_node, H_node) in enumerate(zip(G_node_list, H_node_list)):
                for j, key in enumerate(G.nodes[G_node[1]].keys()):
                    # input(f"G.nodes[G_node]:{G.nodes[G_node[1]]}, H.nodes[H_node]:{H.nodes[H_node[1]]}")
                    if key == 'id':
                        continue
                    elif G.nodes[G_node[1]][key] == H.nodes[H_node[1]][key]:
                        continue
                    else:
                        return False
            return True
        else:
            return False
            
    
    def sort_graph(self, G_list):
        del_num = []
        
        for i, G in enumerate(G_list):
            for j, H in enumerate(G_list[i+1:]):
                if self.check_same_graph(G, H):
                    del_num.append(i)
                    break
        print(del_num)
        for i in reversed(del_num):
            G_list.pop(i)
        for G in G_list:
            key = list(G.nodes.keys())
            # input(key)
            self.Graph_visualization(G, f'graph_{str(key[0][:6])}')
        return G_list
                
            
    def main(self, input_folder, V_title):
        file_list = os.listdir(input_folder)
        img_list = [i for i in file_list if 'combined_image' in i]
        word_pickle = [i for i in file_list if 'word_dic' in i]
        with open(os.path.join(input_folder, word_pickle[0])) as file:
            word_dic = pickle.load(file)
        word_list = [word_dic[word][0] for word in word_dic.keys()]
        prompt_path = os.path.join(input_folder, '../../../prompt/setup')
        save_file_path = os.path.join(prompt_path, '../input_target_object.pickle')
        Object_list_folder = os.path.join(input_folder, '../Object_folder')
        os.makedirs(Object_list_folder, exist_ok=True)
        # input(word_list)
        # input(f'img_list:{len(img_list)}, word_list:{len(word_list)}')

        ###ChatGPTから目標オブジェクト状態の推定
        self.estimateTargetState(img_list, prompt_path, save_file_path, word_list, Object_list_folder)
        
        ###ChatGPTから目標オブジェクトノードの作成
        # self.Target_Object_list = Fm.load_pickle_file(Fm.join_path_and_filename(r'C:/Users/ryuka/research/new_research/images/牛丼_発表用2/Object_folder', 'Target_Object_list.pickle'))
        exec(f'self.Target_Object_list = {self.Target_Object_list}')
        self.Target_Object_node(self.Target_Object_list, Object_list_folder)
        
        # オブジェクトノードの並べ替え
        self.G_list = self.sort_graph(self.G_list)

        os.makedirs(Object_list_folder, exist_ok=True)
    
        # Define the file path
        file_path = os.path.join(Object_list_folder, 'G_list.pickle')
    
        # Save the mes object to the file
        with open(file_path, 'wb') as file:
            pickle.dump(self.G_list, file)
    
        print(f"Data saved to {file_path}")

        os.makedirs(Object_list_folder, exist_ok=True)
    
        # Define the file path
        file_path = os.path.join(Object_list_folder, 'prompt.pickle')
    
        # Save the mes object to the file
        with open(file_path, 'wb') as file:
            pickle.dump(self.gpt.prompt, file)
    
        print(f"Data saved to {file_path}")
        
        return self.G_list, Object_list_folder
        

if __name__ == '__main__':
    MG = MainFunctionUnit_Generator()
    input_folder = './images/GPT4o_input_img'
    V_title = 'ポン酢牛丼'
    MG.main(input_folder, V_title)
    Target_Object_list = MG.Target_Object_list
    G_list = MG.G_list