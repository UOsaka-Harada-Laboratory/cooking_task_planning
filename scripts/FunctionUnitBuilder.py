# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 21:30:08 2024

@author: user
"""
import GraphManager as GM
import networkx as nx
import re
import File_management as Fm



class FunctionUnitBuilder():
    def __init__(self, data):
        self.data = data
        
    def set_attribute(self, in_object_attribute, out_object_attribute, i, comment):
        """
        この関数は定義された機能ユニットの属性に従い、機能ユニットを作成します
        入力：in_object_attribute = [[label1, label2, ... ], [[label1の属性1, 名前], label1の属性2, ... ], [label2の属性1, label2の属性2, ... ]]
        出力：out_object_attribute = [[label1, label2, ... ], [[label1の属性1, 名前], label1の属性2, ... ], [label2の属性1, label2の属性2, ... ]]
        """
        
        """前準備"""
        #グラフの作成
        G = nx.DiGraph()
        node_num = len(in_object_attribute[0])
        
        """モーションノードの作成"""
        motion_ID = f'FU_{str(i).zfill(3)}_A'
        G.add_node(motion_ID)
        G.nodes[f'FU_{str(i).zfill(3)}_A']['label'] = self.data.task['action']
        G.nodes[f'FU_{str(i).zfill(3)}_A']['object'] = self.data.task['object']
        G.nodes[f'FU_{str(i).zfill(3)}_A']['comment'] = comment
        
        """機能ユニットの入力ノードを定義"""
        for i in range(node_num):
            #ノードIDを登録
            G.add_node(in_object_attribute[0][i])
            for at in in_object_attribute[i+1]:
                G.nodes[in_object_attribute[0][i]][at[0]] = at[1]
            G.add_edge(in_object_attribute[0][i], motion_ID)
            
        
        """機能ユニットの出力ノードを定義"""
        for i in range(node_num):
            #ノードIDを登録
            G.add_node(out_object_attribute[0][i])
            for at in out_object_attribute[i+1]:
                G.nodes[out_object_attribute[0][i]][at[0]] = at[1]
            G.add_edge(motion_ID, out_object_attribute[0][i])
            
        return G
   
    
    def Pic_unit(self, i):
        """
        Picモーションを作成する関数
        """
        
        "タスク情報を取得"
        object_ = self.data.task['object']
        space = self.data.task['space']
        hand = self.data.task['hand']
        
        """対象となるオブジェクトについての情報を取得"""
        object_serch = [[key, self.data.Env_Grapf.nodes[key]['type']] for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == object_]
        if object_serch == []:
            input(f"error:{object_}")
            return None, 'error'
        else:  
            object_type = object_serch[0][1]
            obj_key = object_serch[0][0]
            
        """配置位置が場所か容器か機会なのかを検索"""
        container_serch = [key for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == space and self.data.Env_Grapf.nodes[key]['type'] == 'container']
        
        if container_serch == []:   
            container_serch = [space]
        
        """ハンドの選択のチェック"""
        if self.data.Env_Grapf.nodes[obj_key]['place'].replace('_storage', '') not in hand and self.data.Env_Grapf.nodes[obj_key]['place'] != 'workspace':
            error_state = f'''<Wrong task>\n{str(self.data.task)}\n</Wrong task>\n<The reason>\n{hand} cannot grasp an object placed in {self.data.Env_Grapf.nodes[obj_key]["place"]}\n</The reason>'''
            input(f'error:{error_state}')
            return None, error_state
        
        """機能ユニットの属性定義"""
        #オブジェクトが食材の場合
        if object_type == 'ingredients':
            if self.data.Env_Grapf.nodes[obj_key]['physical_state'] == 'solid' and self.data.Env_Grapf.nodes[obj_key]['cutting_style'] == 'whole':
                #inputノード
                f_in_object = [f'FU_{str(i).zfill(3)}_F_in_000', f'FU_{str(i).zfill(3)}_H_in_001', f'FU_{str(i).zfill(3)}_C_in_002']
                I_attribute = [['label', object_], ['container', [space, container_serch[0]]]]
                H_attribute = [['label', hand], ['equipment_status', 'empty']]
                C_attribute = [['label', space], ['ingredients', [[object_, obj_key]]]]
                in_object_attribute = [f_in_object, I_attribute, H_attribute, C_attribute]
                
                #outputノード
                f_out_object = [f'FU_{str(i).zfill(3)}_F_out_000', f'FU_{str(i).zfill(3)}_H_out_001', f'FU_{str(i).zfill(3)}_C_out_002']
                I_attribute = [['label', object_], ['container', ['', '']], ['place', hand]]
                H_attribute = [['label', hand], ['equipment_status', 'fill'], ['ingredients', [[object_, obj_key]]]]
                C_attribute = [['label', space], ['ingredients', [['', '']]]]
                out_object_attribute = [f_out_object, I_attribute, H_attribute, C_attribute]
                
            
            else:
                error_state = f'''<Wrong task>\n{str(self.data.task)}\n</Wrong task>\n<The reason>\nPic motion on food is limited to solid and uncut food. Grasp the Container and perform the Pour motion.\n</The reason>'''
                input(f'error:{error_state}')
                return None, error_state
             
        #オブジェクト食材以外の場合
        else:
            if object_type == 'container':
                tag = 'C'
                food_obj = self.data.Env_Grapf.nodes[obj_key]['ingredients']
                machine_serch = [[space, key] for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == space and self.data.Env_Grapf.nodes[key]['type'] == 'machine']
                M_in_object_I = []
                M_out_object_I = []
                M_attribute_in = []
                M_attribute_out = []
                if machine_serch == []:
                    machine_serch = [['', '']]
                else:
                    space = self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']
                if food_obj[0] != ['', '']:
                    f_in_object_I = []
                    f_out_object_I = []
                    I_attribute_in = []
                    I_attribute_out = []
                    H_attribute_out = [None for _ in range(len(food_obj))]
                    O_attribute_in = [None for _ in range(len(food_obj))]
                    O_attribute_out = [None for _ in range(len(food_obj))]
                    ing_list_in = []
                    ing_list_out = []
                    for fo_num, fo in enumerate(food_obj):
                        if fo == ['', '']:
                            continue
                        f_in_object_I.append(f'FU_{str(i).zfill(3)}_F_in_{str(fo_num+2).zfill(3)}')
                        I_attribute_in.append( [['label', self.data.Env_Grapf.nodes[fo[1]]['label']], ['place', space], ['container', [ object_ , obj_key]], ['machine', machine_serch[0]]])
                        f_out_object_I.append(f'FU_{str(i).zfill(3)}_F_out_{str(fo_num+2).zfill(3)}')
                        I_attribute_out.append([['label', self.data.Env_Grapf.nodes[fo[1]]['label']], ['place', hand], ['container', [ object_ , obj_key]], ['machine', ['', '']]])
                        ing_list_in.append([self.data.Env_Grapf.nodes[fo[1]]['label'], fo[1]])
                        ing_list_out.append([self.data.Env_Grapf.nodes[fo[1]]['label'], fo[1]])
                    H_attribute_out = [['ingredients', ing_list_out]]
                    O_attribute_in = [['ingredients', ing_list_in], ['machine', machine_serch[0]]]
                    O_attribute_out = [['ingredients', ing_list_out], ['machine', ['', '']]]
                    if machine_serch != [['', '']]:
                        M_in_object_I = [f'FU_{str(i).zfill(3)}_M_in_{str(len(food_obj)+2).zfill(3)}']
                        M_out_object_I = [f'FU_{str(i).zfill(3)}_M_out_{str(len(food_obj)+2).zfill(3)}']
                        M_attribute_in = [[['label', machine_serch[0][0]], ['place', self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']], ['container', [object_, obj_key]], ['ingredients', ing_list_in]]]
                        M_attribute_out = [[['label', machine_serch[0][0]], ['place', self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']], ['container', ['', '']], ['ingredients', [['', '']]]]]
                else:
                    if machine_serch != [['', '']]:
                        M_in_object_I = [f'FU_{str(i).zfill(3)}_M_in_{str(len(food_obj)+2).zfill(3)}']
                        M_out_object_I = [f'FU_{str(i).zfill(3)}_M_out_{str(len(food_obj)+2).zfill(3)}']
                        M_attribute_in = [[['label', machine_serch[0][0]], ['place', self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']], ['container', [object_, obj_key]], ['ingredients', [['', '']]]]]
                        M_attribute_out = [[['label', machine_serch[0][0]], ['place', self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']], ['container', ['', '']], ['ingredients', [['', '']]]]]
            elif object_type == 'tool':
                tag = 'T'
            elif object_type == 'machine':
                tag = 'M'
            else:
                input(f'error:{object_type}')
            
            #inputノード
            f_in_object = [f'FU_{str(i).zfill(3)}_H_in_000', f'FU_{str(i).zfill(3)}_{tag}_in_001']
            H_attribute = [['label', hand], ['equipment_status', 'empty']]
            O_attribute = [['label', object_], ['place', space]]
            in_object_attribute = [f_in_object, H_attribute, O_attribute]
            if object_type == 'container' and food_obj[0] != ['', '']:
                f_in_object = f_in_object + f_in_object_I + M_in_object_I
                O_attribute += O_attribute_in
                in_object_attribute = [f_in_object, H_attribute, O_attribute] + I_attribute_in + M_attribute_in
                
            
            #outputノード
            f_out_object = [f'FU_{str(i).zfill(3)}_H_out_000', f'FU_{str(i).zfill(3)}_{tag}_out_001']
            H_attribute = [['label', hand], ['equipment_status', 'fill'], [object_type, [object_, obj_key]]]
            O_attribute = [['label', object_], ['place', hand]]
            out_object_attribute = [f_out_object, H_attribute, O_attribute]
            if object_type == 'container' and food_obj[0] != ['', '']:
                f_out_object = f_out_object + f_out_object_I + M_out_object_I
                H_attribute += H_attribute_out
                O_attribute += O_attribute_out
                out_object_attribute = [f_out_object, H_attribute, O_attribute] + I_attribute_out + M_attribute_out
            
        """機能ユニット作成"""
        return self.set_attribute(in_object_attribute, out_object_attribute, i, 'None'), 'No error'
            
    
    def Place_unit(self, i):
        """
        Placeモーションを作成する関数
        """
        
        #タスク情報の取得
        object_ = self.data.task['object']
        space = self.data.task['space']
        hand = self.data.task['hand']
        
        """環境ノードからオブジェクトの種類を取得"""
        object_serch = [[key, self.data.Env_Grapf.nodes[key]['type']] for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == object_]
        if object_serch == []:
            input(f"error:{object_}")
            return None, 'error'
        else:  
            object_type = object_serch[0][1]
            obj_key = object_serch[0][0]
            
        container_serch = [key for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == space and self.data.Env_Grapf.nodes[key]['type'] == 'container']
        machine_serch = [key for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == space and self.data.Env_Grapf.nodes[key]['type'] == 'machine']
        
        if container_serch == []:
            container_serch = [space]
        else:
            ingredients_serch = [[self.data.Env_Grapf.nodes[key]['label'], key] for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['container'][1] == container_serch[0]]
            if ingredients_serch == []:
                ingredients_serch = [['', '']]
            
        """機能ユニットの属性定義"""
        #オブジェクトが食材の場合
        if object_type == 'ingredients':
            if space in ['workspace', 'right_storage', 'left_storage']:
                error_state = f'''<Wrong task>\n{str(self.data.task)}\n</Wrong task>\n<The reason>\nFood can only be placed on top of the container. Choose to place it on top of the container.\n</The reason>'''
                input('error:{error_state}')
                return None, error_state
            if self.data.Env_Grapf.nodes[obj_key]['physical_state'] == 'solid' and self.data.Env_Grapf.nodes[obj_key]['cutting_style'] == 'whole':
                #inputノード
                if self.data.Env_Grapf.nodes[container_serch[0]]['machine'] != ['', '']:
                    machine_serch = [self.data.Env_Grapf.nodes[container_serch[0]]['machine']]
                else:
                    machine_serch = [['', '']]   
                f_in_object = [f'FU_{str(i).zfill(3)}_H_in_000', f'FU_{str(i).zfill(3)}_C_in_001', f'FU_{str(i).zfill(3)}_F_in_002']
                I_attribute = [['label', object_], ['physical_state', 'solid'], ['cutting_style', 'whole'], ['container', ['', '']], ['place', hand]]
                H_attribute = [['label', hand], ['equipment_status', 'fill'], ['ingredients', [[object_, obj_key]]]]
                C_attribute = [['label', space], ['ingredients', []+ingredients_serch]]
                in_object_attribute = [f_in_object, H_attribute, C_attribute, I_attribute]
                
                #outputノード
                f_out_object = [f'FU_{str(i).zfill(3)}_H_out_000', f'FU_{str(i).zfill(3)}_C_out_001', f'FU_{str(i).zfill(3)}_F_out_002']
                I_attribute = [['label', object_], ['container', [space, container_serch[0]]], ['place', self.data.Env_Grapf.nodes[container_serch[0]]['place']], ['machine', machine_serch[0]]]
                H_attribute = [['label', hand], ['equipment_status', 'empty'], ['ingredients', [['', '']]]]
                if ingredients_serch == ['', '']:
                    ingredients_serch = []
                C_attribute = [['label', space], ['ingredients', [[object_, obj_key]]+ingredients_serch]]
                out_object_attribute = [f_out_object, H_attribute, C_attribute, I_attribute]             
                if machine_serch != [['', '']]:
                    M_in_object_I = [f'FU_{str(i).zfill(3)}_M_in_{str(len(f_in_object)+2).zfill(3)}']
                    M_out_object_I = [f'FU_{str(i).zfill(3)}_M_out_{str(len(f_in_object)+2).zfill(3)}']
                    M_attribute_in = [[['label', machine_serch[0][0]], ['place', self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']], ['container', ['', '']], ['ingredients', [['', '']]]]]
                    M_attribute_out = [[['label', machine_serch[0][0]], ['place', self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']], ['container', [object_, obj_key]], ['ingredients', self.data.Env_Grapf.nodes[container_serch[0]]['ingredients']+ingredients_serch]]]

            else:
                error_state = f'''<Wrong task>\n{str(self.data.task)}\n</Wrong task>\n<The reason>\nThe Place motion must be performed on solid, uncut ingredients. Grasp the Container and perform the Pour motion.\n</The reason>'''
                input('error:{error_state}')
                return None, error_state
             
        #オブジェクト食材以外の場合
        else:
            if space not in ['workspace', 'right_storage', 'left_storage'] and machine_serch == []:
                error_state = f'''<Wrong task>\n{str(self.data.task)}\n</Wrong task>\n<The reason>\nPlease choose the place of objects other than ingredients from ['workspace', 'right_storage', 'left_storage'].\n</The reason>'''
                input('error:{error_state}')
                return None, error_state
            if object_type == 'container':
                tag = 'C'
                food_obj = self.data.Env_Grapf.nodes[obj_key]['ingredients']
                machine_serch = [[space, key] for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == space and self.data.Env_Grapf.nodes[key]['type'] == 'machine']
                M_in_object_I = []
                M_out_object_I = []
                M_attribute_in = []
                M_attribute_out = []
                if machine_serch == []:
                    machine_serch = [['', '']]
                else:
                    space = self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']
                if food_obj[0] != ['', '']:
                    f_in_object_I = []
                    f_out_object_I = []
                    I_attribute_in = []
                    I_attribute_out = []
                    H_attribute_in = [None for _ in range(len(food_obj))]
                    H_attribute_out = [None for _ in range(len(food_obj))]
                    O_attribute_in = [None for _ in range(len(food_obj))]
                    O_attribute_out = [None for _ in range(len(food_obj))]
                    ing_list_in = []
                    ing_list_out = []
                    for fo_num, fo in enumerate(food_obj):
                        if fo == ['', '']:
                            continue
                        f_in_object_I.append(f'FU_{str(i).zfill(3)}_F_in_{str(fo_num+2).zfill(3)}')
                        I_attribute_in.append([['label', self.data.Env_Grapf.nodes[fo[1]]['label']], ['place', hand], ['container', [ object_ , obj_key]], ['machine', ['', '']]])
                        f_out_object_I.append(f'FU_{str(i).zfill(3)}_F_out_{str(fo_num+2).zfill(3)}')
                        I_attribute_out.append([['label', self.data.Env_Grapf.nodes[fo[1]]['label']], ['place', space], ['container', [ object_ , obj_key]], ['machine', machine_serch[0]]])
                        ing_list_in.append([self.data.Env_Grapf.nodes[fo[1]]['label'], fo[1]])
                        ing_list_out.append([self.data.Env_Grapf.nodes[fo[1]]['label'], fo[1]])
                    H_attribute_in = [['ingredients', ing_list_in]]
                    H_attribute_out = [['ingredients', ['', '']]]
                    O_attribute_in = [['ingredients', ing_list_in], ['machine', ['', '']]]
                    O_attribute_out = [['ingredients', ing_list_out], ['machine', machine_serch[0]]]
                    if machine_serch != [['', '']]:
                        M_in_object_I = [f'FU_{str(i).zfill(3)}_M_in_{str(len(food_obj)+2).zfill(3)}']
                        M_out_object_I = [f'FU_{str(i).zfill(3)}_M_out_{str(len(food_obj)+2).zfill(3)}']
                        M_attribute_in = [[['label', machine_serch[0][0]], ['place', self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']], ['container', ['', '']], ['ingredients', [['', '']]]]]
                        M_attribute_out = [[['label', machine_serch[0][0]], ['place', self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']], ['container', [object_, obj_key]], ['ingredients', ing_list_in]]]
                else:
                    if machine_serch != [['', '']]:
                        M_in_object_I = [f'FU_{str(i).zfill(3)}_M_in_{str(len(food_obj)+2).zfill(3)}']
                        M_out_object_I = [f'FU_{str(i).zfill(3)}_M_out_{str(len(food_obj)+2).zfill(3)}']
                        M_attribute_in = [[['label', machine_serch[0][0]], ['place', self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']], ['container', ['', '']], ['ingredients', [['', '']]]]]
                        M_attribute_out = [[['label', machine_serch[0][0]], ['place', self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']], ['container', [object_, obj_key]], ['ingredients', [['', '']]]]]
                    
            elif object_type == 'tool':
                tag = 'T'
            elif object_type == 'machine':
                tag = 'M'
            else:
                input(f'error:{object_type}')
            
            #inputノード
            f_in_object = [f'FU_{str(i).zfill(3)}_H_in_000', f'FU_{str(i).zfill(3)}_{tag}_in_001']
            H_attribute = [['label', hand], ['equipment_status', 'fill'], [object_type, [object_, obj_key]]]
            O_attribute = [['label', object_], ['place', hand]]
            in_object_attribute = [f_in_object, H_attribute, O_attribute]
            if object_type == 'container' and food_obj[0] != ['', '']:
                f_in_object = f_in_object + f_in_object_I + M_in_object_I
                O_attribute += O_attribute_in
                in_object_attribute = [f_in_object, H_attribute, O_attribute] + I_attribute_in + M_attribute_in
            
            #outputノード
            f_out_object = [f'FU_{str(i).zfill(3)}_H_out_000', f'FU_{str(i).zfill(3)}_{tag}_out_001']
            H_attribute = [['label', hand], ['equipment_status', 'empty'], [object_type, ['', '']]]
            O_attribute = [['label', object_], ['place', space]]
            out_object_attribute = [f_out_object, H_attribute, O_attribute]
            if object_type == 'container' and food_obj[0] != ['', '']:
                f_out_object = f_out_object + f_out_object_I + M_out_object_I
                H_attribute += H_attribute_out
                O_attribute += O_attribute_out
                out_object_attribute = [f_out_object, H_attribute, O_attribute] + I_attribute_out + M_attribute_out
            
        """機能ユニット作成"""
        return self.set_attribute(in_object_attribute, out_object_attribute, i, 'None'), 'No error'
        
      
    def Pour_unit(self, i):
        """
        Pourモーションを作成する関数
        """
        
        #タスク情報の取得
        hand = self.data.task['hand']
        sourceContainer = self.data.task['object']
        targetContainer = self.data.task['targetContainer']
        
        """環境ノードからオブジェクトの種類を取得"""
        # object_serch = [[key, self.data.Env_Grapf.nodes[key]['type']] for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == object_]
        # if object_serch == []:
        #     input(f"error:{object_}")
        # else:  
        #     object_type = object_serch[0][1]
        #     obj_key = object_serch[0][0]
        sourceContainer_ID = [key for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == sourceContainer]
        targetContainer_ID = [key for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == targetContainer]
        source_ingredients_serch = [[self.data.Env_Grapf.nodes[key]['label'], key] for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['container'][1] == sourceContainer_ID[0] and self.data.Env_Grapf.nodes[key]['type'] == 'ingredients']
        target_ingredients_serch = [[self.data.Env_Grapf.nodes[key]['label'], key] for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['container'][1] == targetContainer_ID[0] and self.data.Env_Grapf.nodes[key]['type'] == 'ingredients']
        if source_ingredients_serch == []:
            source_ingredients_serch = [['', '']]
        if target_ingredients_serch == []:
            target_ingredients_serch = [['', '']]
        
        """機能ユニットの属性定義"""
        #オブジェクトが食材の場合
        if source_ingredients_serch[0] != ['', '']:
            
            if self.data.Env_Grapf.nodes[targetContainer_ID[0]]['machine'] != ['', '']:
                machine_serch = [self.data.Env_Grapf.nodes[targetContainer_ID[0]]['machine']]
            else:
                machine_serch = [['', '']]
            
            f_in_object_I = []
            f_out_object_I = []
            I_attribute_in = []
            I_attribute_out = []
            H_attribute_in = [None for _ in range(len(source_ingredients_serch))]
            H_attribute_out = [None for _ in range(len(source_ingredients_serch))]
            C1_attribute_in = [None for _ in range(len(source_ingredients_serch))]
            C1_attribute_out = [None for _ in range(len(source_ingredients_serch))]
            C2_attribute_in = [None for _ in range(len(source_ingredients_serch))]
            C2_attribute_out = [None for _ in range(len(source_ingredients_serch))]
            ing_list_in = []
            ing_list_out = []
            for fo_num, fo in enumerate(source_ingredients_serch):
                if fo == ['', '']:
                    continue
                f_in_object_I.append(f'FU_{str(i).zfill(3)}_F_in_{str(fo_num+3).zfill(3)}')
                I_attribute_in.append([['label', self.data.Env_Grapf.nodes[fo[1]]['label']], ['place', hand], ['container', [ sourceContainer, sourceContainer_ID[0]]], ['machine', ['', '']]])
                f_out_object_I.append(f'FU_{str(i).zfill(3)}_F_out_{str(fo_num+3).zfill(3)}')
                I_attribute_out.append([['label', self.data.Env_Grapf.nodes[fo[1]]['label']], ['place', self.data.Env_Grapf.nodes[targetContainer_ID[0]]['place']], ['container', [ targetContainer, targetContainer_ID[0]]], ['machine', machine_serch[0]]])
                ing_list_in.append([self.data.Env_Grapf.nodes[fo[1]]['label'], fo[1]])
                ing_list_out.append([self.data.Env_Grapf.nodes[fo[1]]['label'], fo[1]])
            # input(f'ing_list_in:{ing_list_in}')
            H_attribute_in = [['ingredients', source_ingredients_serch]]
            H_attribute_out = [['ingredients', [['', '']]]]
            C1_attribute_in = [['ingredients', source_ingredients_serch]]
            C1_attribute_out = [['ingredients', [['', '']]]]
            C2_attribute_in = [['ingredients', target_ingredients_serch]]
            if target_ingredients_serch == [['', '']]:
                target_ingredients_serch = []
            C2_attribute_out = [['ingredients', source_ingredients_serch + target_ingredients_serch]]
            M_in_object_I = []
            M_out_object_I = []
            M_attribute_in = []
            M_attribute_out = []
            if machine_serch != [['', '']]:
                M_in_object_I = [f'FU_{str(i).zfill(3)}_M_in_{str(len(source_ingredients_serch)+3).zfill(3)}']
                M_out_object_I = [f'FU_{str(i).zfill(3)}_M_out_{str(len(source_ingredients_serch)+3).zfill(3)}']
                M_attribute_in = [[['label', machine_serch[0][0]], ['place', self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']], ['container', [self.data.Env_Grapf.nodes[targetContainer_ID[0]]['label'], targetContainer_ID[0]]]]]
                M_attribute_out = [[['label', machine_serch[0][0]], ['place', self.data.Env_Grapf.nodes[machine_serch[0][1]]['place']], ['container', [self.data.Env_Grapf.nodes[targetContainer_ID[0]]['label'], targetContainer_ID[0]]], ['ingredients', self.data.Env_Grapf.nodes[targetContainer_ID[0]]['ingredients']+ing_list_in]]]
       
                
            #inputノード
            f_in_object = [f'FU_{str(i).zfill(3)}_H_in_000', f'FU_{str(i).zfill(3)}_C_in_001', f'FU_{str(i).zfill(3)}_C_in_002'] + f_in_object_I + M_in_object_I
            # I_attribute = [['label', object_], ['container', [sourceContainer, sourceContainer_ID[0]]], ['place', hand]] + I_attribute_in
            H_attribute = [['label', hand], ['equipment_status', 'fill'], ['container', [sourceContainer, sourceContainer_ID[0]]]] + H_attribute_in
            C1_attribute = [['label', sourceContainer], ['place', hand]] + C1_attribute_in
            C2_attribute = [['label', targetContainer]] + C2_attribute_in
            in_object_attribute = [f_in_object, H_attribute, C1_attribute, C2_attribute] + I_attribute_in  + M_attribute_in
            
            #outputノード
            f_out_object = [f'FU_{str(i).zfill(3)}_H_out_000', f'FU_{str(i).zfill(3)}_C_out_001', f'FU_{str(i).zfill(3)}_C_out_002'] + f_out_object_I + M_out_object_I
            # I_attribute = [['label', object_], ['container', [targetContainer, targetContainer_ID[0]]], ['place', self.data.Env_Grapf.nodes[targetContainer_ID[0]]['place']]] + I_attribute_out
            H_attribute = [['label', hand], ['equipment_status', 'fill'], ['container', [sourceContainer, sourceContainer_ID[0]]]] + H_attribute_out
            C1_attribute = [['label', sourceContainer], ['place', hand]] + C1_attribute_out
            C2_attribute = [['label', targetContainer]] + C2_attribute_out
            out_object_attribute = [f_out_object, H_attribute, C1_attribute, C2_attribute] + I_attribute_out  + M_attribute_out
            
            
             
        #オブジェクト食材以外の場合
        else:
            error_state = f'''<Wrong task>\n{str(self.data.task)}\n</Wrong task>\n<The reason>\nYou can't 'Pour' {sourceContainer} because it's not an container.\n</The reason>'''
            input(error_state)
            return None, error_state
        """機能ユニット作成"""
        return self.set_attribute(in_object_attribute, out_object_attribute, i, 'None'), 'No error'
        
    def Cut_unit(self, i):
        """
        Cutモーションを作成する関数
        """
        
        #タスク情報の取得
        object_ = self.data.task['object']
        hand = self.data.task['hand']
        cutting_style = self.data.task['cutting method']
        # targetContainer = self.task['targetContainer']
        
        """環境ノードからオブジェクトの種類を取得"""
        object_serch = [[key, self.data.Env_Grapf.nodes[key]['type']] for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == object_]
        if object_serch == []:
            input(f"error:{object_}")
            return None, 'error'
        else:  
            object_type = object_serch[0][1]
            obj_key = object_serch[0][0]
        cutting_board_ID = [key for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == 'cutting board']
        knife_ID = [key for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == 'knife']
        
        container_ing = [ ing[0] for ing in self.data.Env_Grapf.nodes[cutting_board_ID[0]]['ingredients'] if ing[0] != object_]
        if container_ing != [""]:
            error_state = f'The Cut motion can only be performed when there is only one ingredient on the cutting board. Please move {container_ing} on the cutting board to another container before performing the Cut motion.'
            input(f"error:{error_state}")
            return None, error_state
        
        """機能ユニットの属性定義"""
        #オブジェクトが食材の場合
        if object_type == 'ingredients':
            #inputノード
            f_in_object = [f'FU_{str(i).zfill(3)}_F_in_000', f'FU_{str(i).zfill(3)}_H_in_001', f'FU_{str(i).zfill(3)}_C_in_002', f'FU_{str(i).zfill(3)}_T_in_003']
            I_attribute = [['label', object_], ['container', ['cutting board', cutting_board_ID[0]]], ['place', 'workspace'], ['cutting_style', 'whole'], ['physical_state', 'solid']]
            H_attribute = [['label', hand], ['equipment_status', 'fill'], ['tool', ['knife', knife_ID[0]]]]
            C_attribute = [['label', 'cutting board'], ['ingredients', [[object_, obj_key]]], ['place', 'workspace']]
            T_attribute = [['label', 'knife'], ['place', hand]]
            in_object_attribute = [f_in_object, I_attribute, H_attribute, C_attribute, T_attribute]
            
            #outputノード
            f_out_object = [f'FU_{str(i).zfill(3)}_F_out_000', f'FU_{str(i).zfill(3)}_H_out_001', f'FU_{str(i).zfill(3)}_C_out_002', f'FU_{str(i).zfill(3)}_T_out_003']
            I_attribute = [['label', object_], ['container', ['cutting board', cutting_board_ID[0]]], ['place', 'workspace'], ['cutting_style', cutting_style], ['physical_state', 'solid']]
            H_attribute = [['label', hand], ['equipment_status', 'fill'], ['tool', ['knife', knife_ID[0]]]]
            C_attribute = [['label', 'cutting board'], ['ingredients', [[object_, obj_key]]], ['place', 'workspace']]
            T_attribute = [['label', 'knife'], ['place', hand]]
            out_object_attribute = [f_out_object, I_attribute, H_attribute, C_attribute, T_attribute]
             
        #オブジェクト食材以外の場合
        else:
            error_state = f"You can't 'Cut' {object} because it's not an container."
            input(error_state)
            return None, error_state
            
        """機能ユニット作成"""
        return self.set_attribute(in_object_attribute, out_object_attribute, i, 'None'), 'No error'
    
    def Mix_unit(self, i):
        """
        Mixモーションを作成する関数
        """
        
        #タスク情報の取得
        object_ = list(self.data.task['object'])
        hand = self.data.task['hand']
        tool = self.data.task['tool']
        container = self.data.task['container']
        # targetContainer = self.task['targetContainer']
        
        """環境ノードからオブジェクトの種類を取得"""
        object_serch = [[self.data.Env_Grapf.nodes[key]['label'], key] for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] in object_]
        if object_serch == []:
            input(f"error:{object_}")
            return None, 'error'
            
        
        container_ID = [key for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == container]
        tool_ID = [key for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == tool]
        
        """食材オブジェクトの名前の決定と属性の改良"""
        f_in_object_I = []
        f_in_object_I = []
        f_out_object_I = []
        I_attribute_in = []
        I_attribute_out = []
        
        for ing_num, obj in enumerate(object_serch):
            f_in_object_I.append(f'FU_{str(i).zfill(3)}_F_in_{str(ing_num+3).zfill(3)}')
            I_attribute_in.append([['label', obj[0]], ['place', self.data.Env_Grapf.nodes[container_ID[0]]['place']], ['container', [ container, container_ID[0]]]])
            f_out_object_I.append(f'FU_{str(i).zfill(3)}_F_out_{str(ing_num+3).zfill(3)}')
            I_attribute_out.append([['label', self.data.Env_Grapf.nodes[obj[1]]['label']]])
            
            
        """機能ユニットの属性定義"""
        #inputノード
        f_in_object = [f'FU_{str(i).zfill(3)}_H_in_000', f'FU_{str(i).zfill(3)}_C_in_001', f'FU_{str(i).zfill(3)}_T_in_002'] + f_in_object_I
        I_attribute = [] + I_attribute_in
        H_attribute = [['label', hand], ['equipment_status', 'fill'], ['tool', [tool, tool_ID[0]]]]
        C_attribute = [['label', container], ['ingredients', object_serch]] 
        T_attribute = [['label', tool], ['place', hand]]
        in_object_attribute = [f_in_object, H_attribute, C_attribute, T_attribute] + I_attribute
        # input(f'f_in_object:{len(f_in_object)}, in_object_attribute:{len(in_object_attribute)}')
        # input(f'f_in_object:{f_in_object}, in_object_attribute:{in_object_attribute}')
        #outputノード
        f_out_object = [f'FU_{str(i).zfill(3)}_H_out_000', f'FU_{str(i).zfill(3)}_C_out_001', f'FU_{str(i).zfill(3)}_T_out_002'] + f_out_object_I
        out_object_attribute = [f_out_object, H_attribute, C_attribute, T_attribute] + I_attribute
        # input(f'f_out_object:{len(f_out_object)}, out_object_attribute:{len(out_object_attribute)}')
        # input(f'f_out_object:{f_out_object}, out_object_attribute:{out_object_attribute}')
            
        """機能ユニット作成"""
        return self.set_attribute(in_object_attribute, out_object_attribute, i, 'None'), 'No error'
    
    def Cook_unit(self, i):
        """
        Cookモーションを作成する関数
        """
        
        #タスク情報の取得
        object_ = list(self.data.task['object'])
        hand = self.data.task['hand']
        heat_level = self.data.task['heat_level']
        container = self.data.task['container']
        machine = self.data.task['machine']
        # targetContainer = self.task['targetContainer']
        
        """環境ノードからオブジェクトの種類を取得"""
        object_serch = [[self.data.Env_Grapf.nodes[key]['label'], key] for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] in object_]
        if object_serch == []:
            input(f"error:{object_}")
            return None, 'error'
        
        
        container_ID = [key for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == container]
        machine_ID = [key for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['label'] == machine]
        
        """食材オブジェクトの名前の決定と属性の改良"""
        f_in_object_I = []
        f_out_object_I = []
        I_attribute_in = []
        I_attribute_out = []
        
        for ing_num, obj in enumerate(object_serch):
            f_in_object_I.append(f'FU_{str(i).zfill(3)}_F_in_{str(ing_num+3).zfill(3)}')
            I_attribute_in.append([['label', obj[0]], ['place', self.data.Env_Grapf.nodes[container_ID[0]]['place']], ['container', [container, container_ID[0]]], ['machine', [machine, machine_ID[0]]]])
            f_out_object_I.append(f'FU_{str(i).zfill(3)}_F_out_{str(ing_num+3).zfill(3)}')
            I_attribute_out.append([['label', self.data.Env_Grapf.nodes[obj[1]]['label']], ['cooking_method', 'cooked'], ['container', [container, container_ID[0]]]])
            
            
        """機能ユニットの属性定義"""
        #inputノード
        f_in_object = [f'FU_{str(i).zfill(3)}_H_in_000', f'FU_{str(i).zfill(3)}_C_in_001', f'FU_{str(i).zfill(3)}_M_in_002'] + f_in_object_I
        I_attribute = [] + I_attribute_in
        H_attribute = [['label', hand], ['equipment_status', 'empty']]
        C_attribute = [['label', container], ['ingredients', object_serch], ['machine', [machine, machine_ID[0]]]] 
        M_attribute = [['label', machine], ['ingredients', object_serch], ['container', [container, container_ID[0]]]]
        in_object_attribute = [f_in_object, H_attribute, C_attribute, M_attribute] + I_attribute
        
        #outputノード
        f_out_object = [f'FU_{str(i).zfill(3)}_H_out_000', f'FU_{str(i).zfill(3)}_C_out_001', f'FU_{str(i).zfill(3)}_M_out_002'] + f_out_object_I
        I_attribute = [] + I_attribute_out
        H_attribute = [['label', hand], ['equipment_status', 'empty']]
        C_attribute = [['label', container], ['ingredients', object_serch], ['machine', [machine, machine_ID[0]]]] 
        M_attribute = [['label', machine], ['ingredients', object_serch], ['container', [container, container_ID[0]]], ['equipment_status', heat_level]]
        
        out_object_attribute = [f_out_object, H_attribute, C_attribute, M_attribute] + I_attribute 
             
            
        """機能ユニット作成"""
        return self.set_attribute(in_object_attribute, out_object_attribute, i, heat_level), 'No error'
        
    
    def classify_by_action(self, i):
            """
            この関数は入力されたタスク機能ユニットに変換する関数です。
            入力:タスク
            出力：機能ユニット
            """
            
            #タスクの動作を取得
            action = self.data.task['action']
            
            print(f'{i}番目のタスク')
            
            #動作がPicの場合
            if action == 'Pic':
                print('Pic')
                return self.Pic_unit(i)
                
            
            #動作がPlaceの場合
            elif action == 'Place':
                print('Place')
                return self.Place_unit(i)
                
            #動作がPourの場合
            elif action == 'Pour':
                print('Pour')
                return self.Pour_unit(i)
            
            #動作がCutの場合
            elif action == 'Cut':
                print('Cut')
                return self.Cut_unit(i)
            
            #動作がMixの場合
            elif action == 'Mix':
                print('Mix')
                return self.Mix_unit(i)
            
            #動作がCookの場合 
            elif action == 'Cook':
                print('Cook')
                return self.Cook_unit(i)
            

    
    def evaluate_unit_feasibility(self, Functional_unit, i):
        """
        環境オブジェクトノードと機能ユニットを比較して実行可否判定をする関数
        出力：FOONのグラフ
        """
        #機能ユニットの取り出し
        
        task = [key for key in Functional_unit.nodes.keys() if 'A' in key]
        print(f'task : {Functional_unit.nodes.keys()}')
        FU_obj = [ [Functional_unit.nodes[key]['label'], key] for key in Functional_unit.nodes.keys() if 'in' in key]
        FU_obj_out = [ [Functional_unit.nodes[key]['label'], key] for key in Functional_unit.nodes.keys() if 'out' in key]
        EV_obj = [ [self.data.Env_Grapf.nodes[key]['label'], key] for key in self.data.Env_Grapf.nodes.keys() if self.data.Env_Grapf.nodes[key]['node_state'] == 'latest']
        "名前が同じオブジェクトを取り出して属性を比較"
        error_state = self.fetch_and_compare_attributes(FU_obj, FU_obj_out, EV_obj, Functional_unit, i)
        return error_state
    
    def fetch_and_compare_attributes(self, FU_obj, FU_obj_out, EV_obj, Functional_unit, i):
        error_point = ''
        turget_obj = []
        Flag = True
        "同じ名前のオブジェクトの抽出"
        for FU_obj_i in FU_obj:
            same_obj = [ [FU_obj_i, EV_obj_i] for EV_obj_i in EV_obj if FU_obj_i[0] == EV_obj_i[0]]
            if same_obj == []:
                input(f'error:FU_obj_i:{FU_obj_i}, EV_obj:{EV_obj}')
                error_state = "There is no object named {FU_obj_i}. Please select from {EV_obj}."
                input(f'error state : \n{error_state}')
                return error_state
            turget_obj.append(same_obj[0])
         
        "オブジェクトを比較"
        for to in turget_obj:
            #キーの取得
            keys = Functional_unit.nodes[to[0][1]].keys()
            #キーの比較
            for key in keys:
                if key == 'ingredients':
                    print(to)
                    # input(f'Functional_unit.nodes[to[0][1]][key]:{Functional_unit.nodes[to[0][1]][key]}')
                    # input(f'Functional_unit.nodes[to[0][1]][key][0]:{Functional_unit.nodes[to[0][1]][key][0]}')
                    Fun = Functional_unit.nodes[to[0][1]][key][0][0]
                    for node in self.data.Env_Grapf.nodes[to[1][1]][key]:
                        print(node)
                        print(node[0])
                    EGn = [node[0] for node in self.data.Env_Grapf.nodes[to[1][1]][key]]
                    result = Fun in EGn
                elif isinstance(Functional_unit.nodes[to[0][1]][key], list):
                    Fun = Functional_unit.nodes[to[0][1]][key][0]
                    EGn = self.data.Env_Grapf.nodes[to[1][1]][key][0]
                    result = Fun == EGn
                else:
                    Fun = Functional_unit.nodes[to[0][1]][key]
                    EGn = self.data.Env_Grapf.nodes[to[1][1]][key]
                    result = Fun == EGn
                if result == False:
                    Flag = False
                    error_point += f"\nnode:{Functional_unit.nodes[to[0][1]]['label']}, attribute:{key}, Environment Object Attributes:{EGn}, The object state attributes required to perform the task:{Fun}" 
                    input(f"{i}番目:不正解, node:{Functional_unit.nodes[to[0][1]]['label']}, kye:{key}, Fun:{Fun}, EGn:{EGn}, Flag:{Fun==EGn}")
            #比較した結果が正しかったら環境オブジェクトノードを更新

        if Flag == True:
            print(f"{i}番目:正解")
            self.update_environment(Functional_unit, turget_obj, FU_obj_out, i)
        #比較した結果が正しくなかったらエラー文を生成し、再度作業計画
        else:
            input(error_point)
            error_state = self.generate_error_message(i, error_point, Functional_unit)
            return error_state
        return 'No error'   
    
    def generate_error_message(self, i, error_point, Functional_unit):
        error_state = f'''<Input and output to LLM>\n{str(self.data.user_input)}\n<Task Planning from LLM>\n{str(self.data.task_str)}\n</Task Planning from LLM>\n</Input and output to LLM>\n<Relevant information you provide to revise the task plan>\n<Wrong task>\n{str(self.data.task)}\n</Wrong task>\n<The mismatched nodes and attributes>\n{str(error_point)}\n</The mismatched nodes and attributes>\n<Environment Object Node>\n{Fm.graph_to_json_str(self.data.Env_Grapf)}\n</Environment Object Node>\n<Functional_unit>\n{Fm.graph_to_json_str(Functional_unit)}\n</Functional_unit>\n</Relevant information you provide to revise the task plan>'''
        input(f'error_state:{error_state}')
        return error_state
    
    def extract_pattern(self, input_string, pattern):
        """
        Extracts the pattern '_?_', where '?' is any single character, from the input string.
    
        Parameters:
        input_string (str): The string from which to extract the pattern.
    
        Returns:
        str: The extracted pattern if found, else an empty string.
        """
        match = re.search(pattern, input_string)
        if match:
            return match.group(0)
        else:
            return '' 
    
    def update_environment(self, Functional_unit, turget_obj, FU_obj_out, i):
        "環境オブジェクトノードを更新する関数です"
        #FOONグラフに環境オブジェクトノードのFUノードをコピーし追加
        input_node_name_list = []
        
        "FOONグラフの作成"
        for to in turget_obj:
            #typeを使ってノードの名前を決定            
            node_name = f'FO_{str(i).zfill(3)}{self.extract_pattern(to[1][1], r"_[A-Z0-9]_")}{self.extract_pattern(to[1][1], r"(?<=_)[0-9]+$")}'
            same_node = [self.extract_pattern(key, r"_[A-Z]_\d+$") for key in self.data.FOON.nodes.keys()]
            if self.extract_pattern(node_name, r"_[A-Z]_\d+$") not in same_node:
                GM.copy_node_with_new_name(self.data.Env_Grapf, self.data.FOON, to[1][1], node_name)
            else:
                node_name = [key for key in self.data.FOON.nodes.keys() if self.extract_pattern(node_name, r"_[A-Z]_\d+$") in key]
                node_name = sorted(node_name)[-1]
            input_node_name_list.append(node_name)
        
        #モーションノードを追加
        node_name_M = f'FO_{str(i).zfill(3)}_A'
        GM.copy_node_with_new_name(Functional_unit, self.data.FOON, f'FU_{str(i).zfill(3)}_A', node_name_M)
        GM.connect_nodes(self.data.FOON, input_node_name_list, [node_name_M])
        
        #モーションによる更新済みのノードを追加
        output_name_list = []
        name_list = []
        for to in turget_obj:
            #typeを使ってノードの名前を決定      
            node_name = f'FO_{str(i+1).zfill(3)}{self.extract_pattern(to[1][1], r"_[A-Z0-9]_")}{self.extract_pattern(to[1][1], r"(?<=_)[0-9]+$")}'
            output_name_list.append(node_name)
            GM.copy_node_with_new_name(self.data.Env_Grapf, self.data.FOON, to[1][1], node_name)
            #更新用のname_listを作成
            name_list.append([to[0][1].replace('in', 'out'), node_name, to[1][1], to[1][0]])
            
        GM.connect_nodes(self.data.FOON, [node_name_M], output_name_list)
        
        # GM.visualize_graph_with_graphviz(self.FOON, ['label', 'ingredients', 'container', 'place'])
            
        #FOONのoutputノードの更新
        self.update_node_attributes(Functional_unit, name_list)
            
        
        "環境オブジェクトノードを更新"
        #FOONの更新済みノードを追加
        for name in name_list:
            GM.copy_node_with_new_name(self.data.FOON, self.data.Env_Grapf, name[1], name[2])
            
    def update_node_attributes(self, Functional_unit, name_list, togle = False):
        "FU_obj_outのオブジェクトの属性から属性を更新する関数"
        for name in name_list:
            if name[0] in Functional_unit.nodes.keys():
                latest_name = name
                for key in Functional_unit.nodes[name[0]].keys():
                    self.data.FOON.nodes[name[1]][key] = Functional_unit.nodes[name[0]][key]

            # else:
            #     input('変なところに入っていますね')
            #     for key in Functional_unit.nodes[latest_name[0]].keys():
            #         if key == 'label':
            #             continue
            #         self.data.FOON.nodes[name[1]][key] = Functional_unit.nodes[latest_name[0]][key]
            #     if 'place' in Functional_unit.nodes[latest_name[0]].keys():
            #         self.data.FOON.nodes[name[1]]['place'] = self.data.Env_Grapf.nodes[latest_name[2]]['place']
                    
    def Functional_unit_with_variables(self, task_list, action_num):
        """
        関数　:　入力された作業計画を機能ユニットに変換する関数
        入力：{action:~, object:~, space:~, hand:~}
        出力：[機能ユニットG1, 機能ユニットG2, 機能ユニットG3]
        """
        error_state = ''
        #タスクごとに機能ユニットを作成
        for i, task in enumerate(task_list):
            #１つのタスクに対して機能ユニットを作成
            self.data.task = task
            Functional_unit, error_state = self.classify_by_action(i+action_num)
            if error_state == 'No error':
                self.data.Functional_unit_list.append(Functional_unit)
                error_state = self.evaluate_unit_feasibility(Functional_unit, i+action_num)
            if error_state != 'No error':
                return error_state, i+action_num
        return 'No error', len(task_list)+action_num
                    
                    
