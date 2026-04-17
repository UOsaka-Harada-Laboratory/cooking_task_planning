# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 17:32:39 2024

@author: user
"""

import File_management as Fm
import networkx as nx
import GPT_manipulation as GPT

class GenerateFoon():
        
        
    def main(self, EG):
        print(str(EG))
        
        
if __name__ == '__main__':
    EG = Fm.load_json_file(f'/path/to/Environmental_Object_Node/EO000.json')
    GF = GenerateFoon()
    gpt = GPT.GPT_manipulation()
    A = Fm.load_pickle_file('/path/to/Object_folder/G_list.pickle')
    Fm.save_json_file('/path/to/Environmental_Object_Node', 'memo', A[0])
    GF.main(EG)
    gpt.prompt_role_system_add(Fm.load_txt_file('/path/prompt/foon/system.txt'))
    gpt.prompt_role_user_add(Fm.load_txt_file('/path/to/prompt/foon/user.txt'))
    print(gpt.prompt)
    ans = gpt.GPT_exe()
    print(ans)
    Fm.save_text_file('/path/to/Environmental_Object_Node', 'ans.txt', ans)