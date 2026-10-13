import ast
import re
import os
import pickle
import networkx as nx
import GPT_manipulation as GPT
import matplotlib.pyplot as plt

from graphviz import Digraph
from networkx.drawing.nx_agraph import graphviz_layout

REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

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
        if isinstance(ans[0]['object'], list):
            for i, obj in enumerate(ans[0]['object']):
                if obj['ingredients'] is None and obj['container'] is None:
                    # The answer is already in the prompt (added by Target_Object_user_input)
                    self.gpt.prompt_role_user_add('ingredientsは必ずcontainerの上にあるようにしてください。つまりingredientsがオブジェクトに含まれる場合は必ず, containerオブジェクトも含めてください')
                    responce = self.gpt.GPT4o_exe()
                    return False, responce
        return True, ans
    
    def estimateTargetState(self, img_list, prompt_path, save_file_path, word_list, save_folder_path):
        pickle_file_path = sorted(os.listdir(save_folder_path))
        if pickle_file_path is not None:
            if "Target_Object_list.pickle" in pickle_file_path:
                with open(os.path.join(save_folder_path, "Target_Object_list.pickle"), 'rb') as file:
                    self.Target_Object_list = pickle.load(file)
                list_num = len(self.Target_Object_list)
            else:
                list_num=0
        else:
            list_num=0

        for i, img_name in enumerate(sorted(img_list, key=self.extract_number)[list_num:]):
            i = i + list_num
            print(f"\n-----------------{i+1}/{len(img_list)}-----------------\n")
            img_path = os.path.join(self.input_folder, img_name)
            ###gptによる目標オブジェクト状態推定 / Estimation of target object state by gpt
            if i == 0:
                self.gpt.text2prompt(prompt_path, save_file_path)

            if i < len(word_list):
                ans = self.gpt.Target_Object_user_input(self.V_title, img_path, word_list, i, temp_file_path=os.path.join(REPO_ROOT, "prompt", "template", "temp.txt"))
            else:
                continue
            ans = self.word2code(ans)

            ###エラー検出 / Error detection
            flag, res = self.Object_Creation_Error_Detector(ans)
            if flag == False:
                print('エラーが出ました。/ Object creation error, using the corrected answer.')
                ans = self.word2code(res)
                self.gpt.prompt_role_assistant_add(res)
            ###文字のコード化処理 / Code processing of characters
            self.Target_Object_list.append([img_name, ans])
            
            os.makedirs(save_folder_path, exist_ok=True)
    
            # Define the file path
            file_path = os.path.join(save_folder_path, 'Target_Object_list.pickle')
    
            # Save the mes object to the file
            with open(file_path, 'wb') as file:
                pickle.dump(self.Target_Object_list, file)
        
            print(f"Data saved to {file_path}")

    def Graph_visualization(self, dot, file_name, ignore_empty=True):
        # NetworkXグラフからGraphvizのグラフに変換 / Convert NetworkX graph to Graphviz graph
        A = nx.nx_agraph.to_agraph(dot)

        # ノードの属性を追加 / Add node attributes
        for node in A.nodes():
            node_attr = A.get_node(node).attr
            attributes = dot.nodes[node]

            # 属性のtypeが'motion'の場合の処理 / Processing when the attribute type is 'motion'
            if attributes.get('type') == 'motion':
                node_attr['shape'] = 'ellipse'
            else:
                node_attr['shape'] = 'rectangle'  # デフォルトの形状 / Default shape

            # ラベルの設定 / Set labels
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

        # エッジの属性を追加 / Add edge attributes
        for u, v, data in dot.edges(data=True):
            if 'weight' in data:
                A.get_edge(u, v).attr['label'] = f"Weight: {data['weight']}"
                A.get_edge(u, v).attr['fontsize'] = '12'  # エッジラベルのフォントサイズ

        # レイアウトを指定（例: dot、neato、fdpなど） / Specify layout (e.g., dot, neato, fdp, etc.)
        A.layout(prog='dot')

        # グラフ画像をJPEG形式で保存 / Save graph image in JPEG format
        A.draw(f"{self.save_folder_path}/{file_name}.eps")

    OBJECT_TYPE_IDS = {'ingredients': 'F', 'container': 'C', 'machine': 'M', 'tool': 'T'}

    def select_ids_by_object_type(self, obj):
        return self.OBJECT_TYPE_IDS.get(obj['type'])

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
        
        # Add object nodes and create edges from motion node to each object node
        for i, obj in enumerate(object_list):
            #オブジェクトの種類よってID別け
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
                # 未対応のオブジェクトタイプ（完成品の 'dish' など）を含む場合はスキップ
                # Skip targets with unsupported object types (e.g. 'dish' for a finished-product shot)
                unsupported = [obj['type'] for obj in Target_Object[1][0]['object'] if obj['type'] not in self.OBJECT_TYPE_IDS]
                if unsupported:
                    print(f'Skipping {Target_Object[0]}: unsupported object type(s) {unsupported}')
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
        self.V_title = V_title
        self.input_folder = input_folder
        file_list = os.listdir(input_folder)
        img_list = [i for i in file_list if 'combined_image' in i]
        word_pickle = [i for i in file_list if 'word_dic' in i]
        with open(os.path.join(input_folder, word_pickle[0]), 'rb') as file:
            word_dic = pickle.load(file)
        word_list = [word_dic[word][0] for word in word_dic.keys()]
        prompt_path = os.path.join(REPO_ROOT, 'prompt', 'setup')
        save_file_path = os.path.join(prompt_path, '../input_target_object.pickle')
        Object_list_folder = os.path.join(input_folder, '../Object_folder')
        os.makedirs(Object_list_folder, exist_ok=True)

        ###ChatGPTから目標オブジェクト状態の推定 / Estimation of target object state from ChatGPT
        self.estimateTargetState(img_list, prompt_path, save_file_path, word_list, Object_list_folder)
        
        ###ChatGPTから目標オブジェクトノードの作成 / Creation of target object nodes from ChatGPT
        exec(f'self.Target_Object_list = {self.Target_Object_list}')
        self.Target_Object_node(self.Target_Object_list, Object_list_folder)
        
        # オブジェクトノードの並べ替え / Sorting object nodes
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
    V_title = 'Pondzu_Beef_Bowl' # 'ポン酢牛丼'
    MG.main(input_folder, V_title)
    Target_Object_list = MG.Target_Object_list
    G_list = MG.G_list