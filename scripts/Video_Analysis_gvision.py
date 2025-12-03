import os
import cv2
import datetime
import pickle
import shutil
from PIL import Image
from sentence_transformers import SentenceTransformer

class Video_Analysis:
    def __init__(self, video_path, google_json):
        """
        video_path: full path of the cooking video to analyze
        google_json: full path of json file for google credentials to use Vision API
        """
        self.video_path = video_path
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.google_vision_json = google_json
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.word_list = []
        self.word_dic = {}
        self.error_count = 0

    def video2jpg(self, output_folder):
        """
        Extract frames from original video
        output_folder: full path where the frames will be saved
        """ 
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        print("Frames per second:", round(fps))

        frame_count = 0
        image_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if round(frame_count % (round(fps)/5)) == 0:
                filename = "image_" + datetime.datetime.now() + ".jpg"
                img_path = os.path.join(output_folder, filename)
                cv2.imwrite(img_path, frame)
                image_count += 1
            frame_count += 1

        print(f'Total images;', image_count)

        cap.release()
        cv2.destroyAllWindows()
    
    def detect_text(self, img_path):
        """
        Detects text in the image file using google vision.

        Args:
            img_path: full path of the image to be analyzed
        Returns:
            Detected text in the image, None string otherwise.
        """
        from google.cloud import vision
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(self.google_vision_json)
        client = vision.ImageAnnotatorClient(credentials=credentials)

        with open(img_path, "rb") as img_file:
            content = img_file.read()
        
        img = vision.Image(content=content)

        response = client.text_detection(image=img)
        texts = response.text_annotations

        if len(texts) == 0:
            print("text: None")
            return "None"
        else:
            print(f"text:", texts[0].description)
            return texts[0].description

    def compare_texts(self, text1, text2):
        """
        Compares the similarity of 2 texts by calculating a similarity score
        and a flag for detected errors.
        Args:
            text1: string with the first text
            text2: string with the second text
        Returns:
            flag: bool value to determine if there was an error (True) or not (False)
        """
        # Similarity through Levenshtein distance
        distance = self.levenshtein_distance(text1, text2)

        len1 = len(text1)
        len2 = len(text2)

        similarity = 1 - (distance / (len1 + len2))

        # Error
        if similarity != 1:
            self.error_count += 1
        if similarity > 0.9:
            flag = False
        else:
            flag = True
        
        print(f"\n=====================================\ntext1 : {text1}\ntext2 : {text2}\n類似度 : {similarity}\n=====================================\n")
        self.word_list.append(f"\n=====================================\ntext1 : {text1}\ntext2 : {text2}\n類似度 : {similarity}\n=====================================\n")

        return flag

    def levenshtein_distance(self, s1, s2):
        """
        Calculate the Levenshtein distance between two texts
        Args:
            s1: string with the first text
            s2: string with the second text
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
            distances_ = distances_
        return distances[-1]
    
    def organize_images_with_ocrself(self, img_folder_path):
        """
        Use OCR to detect the text in the subtitles and separate the frames into
        folders, one for each action.
        Args:
            img_folder_path: the full path of the folder containing the extracted frames
        """

        try:
            img_name_list = sorted(os.listdir(img_folder_path))
        except:
            img_name_list = None
        
        organized_folder = os.path.join()
        os.makedirs(organized_folder, exist_ok=True)

        word_dic = {} # keys are the action class, value is a list of [text, image name]
        move_class = 0
        pre_word = ''

        img_class_list = [] # list to store images that belong to the same action class

        # Separate image according to OCR results
        for i, img_name_i in enumerate(img_name_list):
            img_path = os.path.join(img_folder_path, img_name_i)
            latest_word = self.detect_text(img_path)
            if i == 0:
                print("Start organize...")
                organized_folder_i = os.path.join(organized_folder, str(move_class))
                os.makedirs(organized_folder_i, exist_ok=True)
                img_class_list.append(img_name_i)
                pre_word = latest_word
            
            print(f"move_class:{move_class}, img_name_i:{img_name_i}")
            if self.compare_texts(pre_word, latest_word):
                word_dic.update({move_class:[pre_word, img_class_list]}) 
                img_class_list = []
                move_class += 1
                organized_folder_i = os.path.join(organized_folder, str(move_class))
                os.makedirs(organized_folder_i, exist_ok=True)
                print(f"Change class | move_class:{move_class}, img_name_i:{img_name_i}\n\n")
            elif  i == len(img_name_list)-1:
                word_dic.update({move_class:[pre_word, img_class_list]}) 
                print(f"Change class | move_class:{move_class}, img_name_i:{img_name_i}\n\n")
                break

            img_class_list.append(img_name_i)
            try:
                if os.path.exists(img_path):
                    fileName = os.path.basename(img_path)
                    destinationFilePath = os.path.join(organized_folder_i, fileName)
                    shutil.move(img_path, destinationFilePath)
                    print(f"Image '{fileName}' has been moved to '{organized_folder_i}'.")
                else:
                    print(f"Error: '{img_path}' does not exist.")
            except (shutil.Error, IOError) as e:
                print(f"Error moving the image: {e}")

            pre_word = latest_word
        
        self.word_dic = word_dic
        pickle_file_path = os.path.join(organized_folder, "word_dic.pickle")

        with open(pickle_file_path, 'wb') as file:
            pickle.dump(word_dic, file)
        
        print("Word dictionary:", word_dic)

    def removeSparseImageDirs(self, all_img_folder, trash_folder):
        """
        Removes generated folders with few images to filter small actions
        Args:
            all_img_folder: one of the generated action class folders
            trash_folder: full path of the trash folder
        """

        try:
            file_name = sorted(os.listdir(all_img_folder))
        except:
            file_name = None
        file_name.remove("word_dic.pickle")
        for i, fm in enumerate(file_name):
            file_path = os.path.join(all_img_folder, fm)
            img_num = len(os.listdir(file_path))
            if img_num < 4:
                fileName = os.path.basename(file_path)
                destinationFilePath = os.path.join(trash_folder, fileName)
                shutil.move(file_path, destinationFilePath)
                print(f"Image '{fileName}' has been moved to '{trash_folder}'.")
                del self.word_dic[int(fm)]
    
    def get_combined_img(self, folder_path, save_folder_path, combined_image_name):
        """
        Generate a 9 image grid.
        Args:
            folder_path: full path with the images of a class action
            save_folder_path: full path of where to save the grid
            combined_image_name: name of the combined image
        """
        
        os.makedirs(save_folder_path, exist_ok=True)
        filenames = sorted(os.listdir(folder_path))

        # Parameters for single image grid
        num_images_needed = 9
        padding = 10            # Space between images
        image_size = 300        # Size to which each image will be resized

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
        """
        Call the get_combined_img function for all generated actions.
        Args:
            organize_folder_path: path of the organized folder by actions
            save_folder_path: full path of where to save the combined images
        """


        folder_name_list = sorted(os.listdir(organize_folder_path))
        folder_name_list.remove('word_dic.pickle')
        folder_name_num_list = sorted([int(i) for i in folder_name_list])
        folder_name_list = [str(i) for i in folder_name_num_list]
        for i, folder_name in enumerate(folder_name_list):
            folder_path = os.path.join(organize_folder_path, folder_name)
            combined_image_name = f'combined_image_{i}.jpg'
            self.get_combined_img(folder_path, save_folder_path, combined_image_name)

    def main(self):
        """
        Main function to separate frames into actions according to the text from subtitles
        Returns:
            save_folder_path: full path of where the actions and word_dic.pickle are saved.
        """

        # Parameters
        video_path = self.video_path
        image_folder = os.path.join(self.current_path, f"images_{datetime.datetime.now()}")
        all_image_folder = os.path.join(image_folder, "all_images")
        os.makedirs(all_image_folder, exist_ok=True)
        
        # Extract frames from video
        self.video2jpg(video_path, all_image_folder)

        # Use Google Cloud Vision to read the subtitles
        self.organize_images_with_ocrself(all_image_folder)

        # Remove actions with very few images (<4)
        Trash_Folder_path = os.path.join(image_folder, 'Trash')
        organize_folder_path = os.path.join(image_folder, 'organized_folder')
        os.makedirs(Trash_Folder_path, exist_ok=True)
        self.removeSparseImageDirs(organize_folder_path, Trash_Folder_path)

        # Combine images
        save_folder_path = os.path.join(image_folder, 'GPT4o_input_img')
        os.makedirs(save_folder_path)
        self.ImageCombiner(organize_folder_path, save_folder_path)
        pickle_file_path = os.path.join(save_folder_path, "word_dic.pickle")
        with open(pickle_file_path, 'wb') as file:
            pickle.dump(self.word_dic, file)
        
        return save_folder_path
    
if __name__ == '__main__':

    video_path = "path/to/video"  # .mp4 format is preferred
    google_json_path = "path/to/google/credentials"
    VA = Video_Analysis(video_path, google_json_path)
    word_dic = VA.main()
    word_list = VA.word_list
    error_count = VA.error_count