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
        with open(os.path.join(folder_path, 'system.txt'), 'r', encoding='utf-8') as file:
             text = file.read()
        self.prompt_role_system_add(text)
        files = os.listdir(folder_path)
        user_txt_file = [i for i in files if 'user' in i and '_txt' in i]
        user_txt_file.sort()
        user_jpg_file = [i for i in files if 'user' in i and '_jpg' in i]
        user_jpg_file.sort()
        assistant_file = [i for i in files if 'assistant' in i]
        assistant_file.sort()
        if user_txt_file != [] and user_jpg_file != []:
            for i, uf in enumerate(user_txt_file):
                with open(os.path.join(folder_path, user_txt_file[i]), 'r', encoding='utf-8') as file:
                    text = file.read()
                with open(os.path.join(folder_path, user_jpg_file[i]), 'r', encoding='utf-8') as file:
                    img = file.read()
                self.prompt_role_user_add(text, img)
                with open(os.path.join(folder_path, assistant_file[i]), 'r', encoding='utf-8') as file:
                    text = file.read()
                self.prompt_role_assistant_add(text)
        elif user_jpg_file == []:
            for i, uf in enumerate(user_txt_file):
                with open(os.path.join(folder_path, user_txt_file[i]), 'r', encoding='utf-8') as file:
                    text = file.read()
                self.prompt_role_user_add(text)
                with open(os.path.join(folder_path, assistant_file[i]), 'r', encoding='utf-8') as file:
                    text = file.read()
                self.prompt_role_assistant_add(text)
        self.save_prompt_to_pickle(save_file_path)

        
    def Target_Object_user_input(self, V_title, img_path, word_list, num, temp_file_path="./prompt/template/temp.txt"):
        with open(temp_file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
        text += V_title + '\nAll caption for the video: ' + str(word_list) + '\nVideo subtitles: ' + word_list[int(num)]
        self.prompt_role_user_add(text, img_path)
        # print(text)
        result = self.GPT4o_exe()
        self.prompt_role_assistant_add(result)
        return result
        
if __name__=="__main__": 
    api_key = "API_KEY_HERE_OR_LOAD" 
    gpt = GPT_manipulation(api_key=api_key)