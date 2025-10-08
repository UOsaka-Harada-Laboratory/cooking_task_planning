# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 02:43:55 2024

@author: user
"""
import File_management as Fm
import cv2
import os
from sentence_transformers import SentenceTransformer


class Video_Analysis:
    def __init__(self, movie_path, google_json):
        ###Youtube用
        self.movie_path = movie_path
        ###現在のパス
        self.current_path = Fm.get_current_path()
        ###google visionのプロジェクトID text-detection2948
        self.google_vision_json = google_json
        # モデルのロード
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.word_list = []
        self.word_dic = {}
        self.error_count = 0
    
    def movie2jpg(self, movie_path, output_folder):
        # 動画ファイルの読み込み
        cap = cv2.VideoCapture(movie_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        input(round(fps))
        
        # フレームを1つずつ保存
        frame_count = 0
        image_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if round(frame_count % (round(fps)/5)) == 0:
                filename = 'image_' + Fm.get_current_time() + ".jpg"
                img_path = Fm.join_path_and_filename(output_folder, filename)
                cv2.imwrite(img_path, frame)
                image_count += 1
            frame_count += 1
        
        # 動画の総フレーム数を取得
        print(f'Total images: {image_count}')
        
        cap.release()
        cv2.destroyAllWindows()
                    
    def detect_text(self, path):
        """Detects text in the file."""
        from google.cloud import vision
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(self.google_vision_json)
        client = vision.ImageAnnotatorClient(credentials=credentials)

        with open(path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        response = client.text_detection(image=image)
        texts = response.text_annotations
        
        if len(texts) == 0:
            print("text:None\n\n")
            return 'None'
        else:
            print(f"text:{texts[0].description}\n\n")
    
            return texts[0].description
        
    
    def compare_texts(self, text1, text2):
        """
        2つのテキストの類似度を計算し、文字の誤変換や欠損を認識する関数
        
        Args:
            text1 (str): 比較対象の文章1
            text2 (str): 比較対象の文章2
            
        Returns:
            float: 2つの文章の類似度 (0.0 ~ 1.0)
            bool: 文字の誤変換や欠損が検出されたかどうかのフラグ
        """
        # Levenshtein 距離の計算
        distance = self.levenshtein_distance(text1, text2)
        
        # 文章の長さ
        len1 = len(text1)
        len2 = len(text2)
        
        # 類似度の計算
        similarity = 1 - (distance / (len1 + len2))
        
        # 誤変換/欠損の検出
        has_anomaly = False
        if similarity < 0.9 or abs(len1 - len2) > 5:
            has_anomaly = True
            
        print(f"\n=====================================\ntext1 : {text1}\ntext2 : {text2}\n類似度 : {similarity}\n=====================================\n")
        self.word_list.append(f"\n=====================================\ntext1 : {text1}\ntext2 : {text2}\n類似度 : {similarity}\n=====================================\n")
        if similarity != 1:
            self.error_count += 1
        if similarity > 0.9:
            flag = False
        else:
            flag = True
        
        return flag
    
    def levenshtein_distance(self, s1, s2):
        """
        2つの文字列のLevenshtein距離を計算する関数
        """
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        distances = range(len(s1) + 1)
        for i2, c2 in enumerate(s2):
            distances_ = [i2+1]
            for i1, c1 in enumerate(s1):
                if c1 == c2:
                    distances_.append(distances[i1])
                else:
                    distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
            distances = distances_
        return distances[-1]
    
    def organize_images_with_ocrself(self, img_folder_path):
        """
        ocrによって動作ごとに画像をフォルダ別け
        入力：すべての画像が入ったフォルダ
        動作：フォルダを新たに作成し、動作ごとに画像を別ける
        出力：画像の入ったフォルダパス
        """
        #画像ファイル名の取り出し
        img_name_list = Fm.get_filename_from_folder(img_folder_path)
        organized_folder = Fm.join_path_and_filename(Fm.get_parent_directory_path(img_folder_path), 'organized_folder')
        Fm.Create_folder(organized_folder) 
        #word_dic = {動作クラス：[文字テキスト, [画像名]]}
        word_dic = {}
        #クラス
        move_class = 0
        pre_word = ''
        
        #同じクラスの画像リスト
        img_class_list = []
        
        #画像ごとに言葉の抽出をOCRで行い
        for i, img_name_i in enumerate(img_name_list):
            img_path = Fm.join_path_and_filename(img_folder_path, img_name_i)
            latest_word = self.detect_text(img_path)
            if i == 0:
                input('start_organize\n\n')
                organized_folder_i = Fm.join_path_and_filename(organized_folder, str(move_class))
                Fm.Create_folder(organized_folder_i)
                img_class_list.append(img_name_i)
                pre_word = latest_word
                
            print(f"move_class:{move_class}, img_name_i:{img_name_i}\n\n")
            if self.compare_texts(pre_word, latest_word):
                word_dic.update({move_class:[pre_word, img_class_list]}) 
                img_class_list = []
                move_class += 1
                organized_folder_i = Fm.join_path_and_filename(organized_folder, str(move_class))
                Fm.Create_folder(organized_folder_i)
                print(f"Chang class | move_class:{move_class}, img_name_i:{img_name_i}\n\n")
            elif  i == len(img_name_list)-1:
                word_dic.update({move_class:[pre_word, img_class_list]}) 
                print(f"Chang class | move_class:{move_class}, img_name_i:{img_name_i}\n\n")
                break
                
            img_class_list.append(img_name_i)
            Fm.moveImageToFolder(img_path, organized_folder_i)
            pre_word = latest_word
        
        self.word_dic = word_dic
        Fm.save_pickle_file(organized_folder, "word_dic.pickle", self.word_dic)
        input(word_dic)
        
        
    def removeSparseImageDirs(self, all_image_folder, Trash_Folder_path):
        file_name = Fm.get_filename_from_folder(all_image_folder)
        file_name.remove("word_dic.pickle")
        for i, fm in enumerate(file_name):
            # input(fm)
            file_path = Fm.join_path_and_filename(all_image_folder, fm)
            img_num = len(Fm.get_filename_from_folder(file_path))
            if img_num < 4:
                # input(fm)
                Fm.moveImageToFolder(file_path, Trash_Folder_path)
                del self.word_dic[int(fm)]

    def get_combined_img(self, folder_path, save_folder_path, combined_image_name):
        # Ensure the save folder exists
        os.makedirs(save_folder_path, exist_ok=True)
    
        # Get all image filenames from the folder
        filenames = sorted(Fm.get_filename_from_folder(folder_path))
        
        # Number of images needed
        num_images_needed = 9
        padding = 10  # Space between images
        image_size = 300  # Size to which each image will be resized
    
        # Select 9 images (first, last, and evenly spaced others)
        if len(filenames) >= num_images_needed:
            selected_filenames = [filenames[0]]
            interval = (len(filenames) - 2) // (num_images_needed - 2)
            for i in range(1, num_images_needed - 1):
                selected_filenames.append(filenames[i * interval])
            selected_filenames.append(filenames[-1])
        else:
            selected_filenames = filenames
            while len(selected_filenames) < num_images_needed:
                selected_filenames.append(None)  # Placeholder for empty slots
    
        # Create a new blank image for the 3x3 grid
        grid_size = (3 * image_size + 2 * padding, 3 * image_size + 2 * padding)
        combined_image = Image.new('RGB', grid_size, color=(255, 255, 255))
    
        # Paste the images into the grid
        for idx, filename in enumerate(selected_filenames):
            row, col = divmod(idx, 3)
            x = col * (image_size + padding)
            y = row * (image_size + padding)
            
            if filename is not None:
                img = Image.open(os.path.join(folder_path, filename))
                img = img.resize((image_size, image_size), Image.LANCZOS)
                combined_image.paste(img, (x, y))
        
        # Save the combined image
        save_path = os.path.join(save_folder_path, combined_image_name)
        combined_image.save(save_path)
    
        print(f'Combined image saved to {save_path}')

    
    def ImageCombiner(self, organize_folder_path, save_folder_path):
        folder_name_list = Fm.get_filename_from_folder(organize_folder_path)
        folder_name_list.remove('word_dic.pickle')
        folder_name_num_list = sorted([int(i) for i in folder_name_list])
        folder_name_list = [str(i) for i in folder_name_num_list]
        for i, folder_name in enumerate(folder_name_list):
            folder_path = Fm.join_path_and_filename(organize_folder_path, folder_name)
            combined_image_name = f'combined_image_{i}.jpg'
            self.get_combined_img(folder_path, save_folder_path, combined_image_name)
        
        
         
    
    def main(self):
        # ###URLから動画を取得
        # ###入力：URL
        # ###出力：動画のパス
        # movie_path = self.get_cooking_video()
        movie_path = self.movie_path
        google_json = self.google_vision_json
        
        ###動画をフレームごとに分割し、画像をフォルダに保存
        ###入力：動画のpathと出力先のpath
        ###出力：保存先フォルダを保存
        image_folder = Fm.join_path_and_filename(self.current_path, f"images\\images_{Fm.get_current_time()}")
        all_image_folder = Fm.join_path_and_filename(image_folder, "all_images") 
        Fm.Create_folder(all_image_folder)
        self.movie2jpg(movie_path, all_image_folder)
        
        # # ###画像をGoogle cloud visionを用いて文字抽出
        self.organize_images_with_ocrself(all_image_folder)
        
        ##枚数が少ないフォルダを削除
        ##枚数が少ない物はゴミフォルダに移動
        # image_folder = r"C:\Users\user\new_research\images\角煮"
        # self.word_dic = Fm.load_pickle_file(r'C:\Users\user\new_research\images\角煮\organized_folder\word_dic.pickle')
        input(self.word_dic)
        Trash_Folder_path = Fm.join_path_and_filename(image_folder, 'Trash')
        organize_folder_path = Fm.join_path_and_filename(image_folder, 'organized_folder')
        Fm.Create_folder(Trash_Folder_path)
        self.removeSparseImageDirs(organize_folder_path, Trash_Folder_path)
        
        ###ChatGPTに入力するための画像を作成
        save_folder_path = Fm.join_path_and_filename(image_folder, 'GPT4o_input_img')
        Fm.Create_folder(save_folder_path)
        self.ImageCombiner(organize_folder_path, save_folder_path)
        Fm.save_pickle_file(save_folder_path, 'word_dic', self.word_dic)
        
        return save_folder_path

        
if __name__ == '__main__':

    video_path = "path/to/video" # .mp4 format is preferred
    google_json_path = "path/to/google/credentials"

    VA = Video_Analysis(video_path, google_json_path)
    word_dic = VA.main()
    word_list = VA.word_list
    error_count = VA.error_count