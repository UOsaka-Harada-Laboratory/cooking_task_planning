# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 21:17:45 2024

@author: user
"""
from openai import OpenAI 
import openai
import base64
import os
import pickle
import File_management as Fm
import time

class GPT_manipulation:
    
    def __init__(self, api_key):
        self.prompt = []
        # Azure OpenAIの設定
        self.client = OpenAI(api_key=api_key)
        self.gpt4_client = openai
        self.gpt4_client.api_key = api_key
        
    # Open the image file and encode it as a base64 string
    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
        
    def GPT4o_exe(self):
        response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=self.prompt,
                    temperature=0.0,
                )
        
        return response.choices[0].message.content

    def GPT_exe(self, model='gpt-4', temperature=0.0):
        response = self.client.chat.completions.create(
                    model=model,
                    messages=self.prompt,
                    temperature=0.0,
                )
        
        return response.choices[0].message.content
    
    def prompt_role_system_add(self, mes):
        self.prompt.append({"role": "system", "content": mes})
    
    def prompt_role_user_add(self, mes, img_path=None):
        if img_path==None:
            self.prompt.append({"role": "user", "content": mes})
        else:
            base64_image = self.encode_image(img_path)
            self.prompt.append({"role": "user", "content": [
            {"type": "text", "text": mes},
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{base64_image}"}
            }
        ]})
                           
    def prompt_role_assistant_add(self, mes):
        self.prompt.append({"role": "assistant", "content": mes})
        
    def save_prompt_to_pickle(self, file_path):
        """
        プロンプトを pickle 形式で保存する関数
        """
        # ファイルが存在しないフォルダの場合は作成する
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # プロンプトを pickle 形式で保存
        with open(file_path, 'wb') as f:
            pickle.dump(self.prompt, f)
        
        print(f'プロンプトを {file_path} に保存しました。')
        
    def load_prompt_from_pickle(self, file_path):
        """
        プロンプトを pickle 形式から読み込む関数
        
        Args:
            folder_path (str): プロンプトが保存されているフォルダのパス
        
        Returns:
            list: 読み込んだプロンプト
        """
    
        
        # プロンプトを読み込む
        with open(file_path, 'rb') as f:
            self.prompt = pickle.load(f)
        print(f'プロンプトを {file_path} から読み込みました。')
        
    def text2prompt(self, folder_path, save_file_path):
        text = Fm.load_txt_file(Fm.join_path_and_filename(folder_path, 'system.txt'))
        self.prompt_role_system_add(text) 
        files = Fm.get_filename_from_folder(folder_path)
        user_txt_file = [i for i in files if 'user' in i and '_txt' in i]
        user_txt_file.sort()
        user_jpg_file = [i for i in files if 'user' in i and '_jpg' in i]
        user_jpg_file.sort()
        assistant_file = [i for i in files if 'assistant' in i]
        assistant_file.sort()
        if user_txt_file != [] and user_jpg_file != []:
            for i, uf in enumerate(user_txt_file):
                text = Fm.load_txt_file(Fm.join_path_and_filename(folder_path, user_txt_file[i]))
                img = Fm.load_txt_file(Fm.join_path_and_filename(folder_path, user_jpg_file[i]))
                self.prompt_role_user_add(text, img)
                text = Fm.load_txt_file(Fm.join_path_and_filename(folder_path, assistant_file[i]))
                self.prompt_role_assistant_add(text)
        elif user_jpg_file == []:
            for i, uf in enumerate(user_txt_file):
                text = Fm.load_txt_file(Fm.join_path_and_filename(folder_path, user_txt_file[i]))
                self.prompt_role_user_add(text)
                text = Fm.load_txt_file(Fm.join_path_and_filename(folder_path, assistant_file[i]))
                self.prompt_role_assistant_add(text)

        self.save_prompt_to_pickle(save_file_path)

        
        
    def Target_Object_user_input(self, V_title, img_path, word_list, num, temp_file_path=r"C:\Users\user\new_research\prompt\template\temp.txt" ):
        text = Fm.load_txt_file(temp_file_path)
        text += V_title + '\nAll caption for the video: ' + str(word_list) + '\nVideo subtitles: ' + word_list[int(num)]
        self.prompt_role_user_add(text, img_path)
        # print(text)
        result = self.GPT4o_exe()
        self.prompt_role_assistant_add(result)
        return result
    
        
if __name__=="__main__": 
    api_key = "API_KEY_HERE_OR_LOAD" 
    gpt = GPT_manipulation(api_key=api_key)
    # input()
    ### テスト用
    # gpt.prompt_role_system_add('テストです')
    # gpt.prompt_role_user_add('返事をしてください')
    
    ### プロンプトを読み込む
    # gpt.load_prompt_from_pickle('ES.pickle')
    # gpt.prompt_role_user_add('''
    #                          ''')
    # ans = gpt.GPT_exe(model="gpt-4")
    # print(ans)
    # print(gpt.cost)
    # def_file_manager.text_file_save(ans, 'C:/Users/ryuka/research/Youtube_task_planning/nisimura', file_name = 'file')
    
    ### コーディング用
    # input_file_path = 'C:/Users/ryuka/research/Youtube_task_planning/a.py'
    # output_file_name = input_file_path.split('/')[-1]
    # gpt.proglam_generater(input_file_path, output_file_name[:-4]+'_gen')
    
    ###Fewshot用
    # gpt.text2prompt(r'C:\Users\user\new_research\prompt\setup', r'C:\Users\user\new_research\prompt\input_target_object.pickle')
    # num = 13
    # V_title = "y2mate.com - これうますぎて作ったら永遠バクバク食べちゃうので注意が必要です鶏唐揚げの甘酢がらめ詳しいレシピはアプリで料理名を検索鶏肉  鶏もも肉  おかず_v720P"
    # img_path = fr"C:\Users\user\new_research\images\Few_shot_sample\GPT4o_input_img\combined_image_{str(num)}.jpg"
    # word_list = ['揚げ焼きで簡単', '激うま鶏肉おかず', 'ごしょうかーい', '鶏肉にお酒', '鶏肉にお酒塩こしょう', '鶏肉にお酒塩こしょうおろしにんにく', '鶏肉にお酒塩こしょうおろしにんにくおろししょうが', 'よーくもみもみ',
    #              'かたくり粉と薄力粉を入れて', 'かたくり粉と薄力粉を入れて', 'まぶすように混ぜる', 'これくらいしっかりまぶしてなー', 'サラダ油を熱したフライパンで', 'サラダ油を熱したフライパンで', '全体がこんがりきつね色になるまで',
    #              '揚げ焼きにしていくでぇ', '揚げあげりはこんな感じ!', '砂糖酢醤油白いりごま', 'さっきのからあげを投入', '全体にしっかりタレを絡めたら', 'ちょっと小さめに切ってあるから', 'ばくばく食べれちゃうねん', 'ほんまにおいしいから周りにも教えてくあげて']
    # result = gpt.Target_Object_user_input(V_title, img_path, word_list, num)
    # prompt = gpt.prompt
    # save_folder_path = r'C:\Users\user\new_research\prompt\setup'
    # user_path = f'user{str(num).zfill(2)}_txt.txt'
    # user_path_jpg = f'user{str(num).zfill(2)}_jpg.txt'
    # assistant_path = f'assistant{str(num).zfill(2)}.txt'
    # Fm.save_text_file(save_folder_path, user_path, prompt[-2]['content'][0]['text'])
    # Fm.save_text_file(save_folder_path, user_path_jpg, img_path)
    # Fm.save_text_file(save_folder_path, assistant_path, prompt[-1]['content'])
    
    ###taskplanのFewshot
    #gpt.text2prompt(r'C:\Users\user\new_research\prompt\taskplanning_without_Area', r'C:\Users\user\new_research\prompt\taskplanning_without_Area\taskplan_setup.pickle')
