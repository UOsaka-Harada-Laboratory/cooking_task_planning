# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 03:02:34 2024

@author: user
"""

import os
import datetime
import shutil
import pickle
import csv
import networkx as nx
import json

def beep(times=1, interval=0.2):
    """
    端末ベルを鳴らす（winsound.Beep のクロスプラットフォーム代替）
    """
    import sys, time
    for _ in range(times):
        sys.stdout.write('\a')
        sys.stdout.flush()
        time.sleep(interval)

def get_current_path():
    """
    現在のディレクトリのパスを取得する関数
    
    Returns:
        str: 現在のディレクトリのパス
    """
    script_path = os.path.abspath(__file__)
    script_directory = os.path.dirname(script_path)
    return script_directory

def Create_folder(path):
    """
    指定されたパスにフォルダ
    
    Args:
        path (str): フォルダを作成するパス
    """
    # パスが存在するかを確認
    if not os.path.exists(path):
        # パスが存在しない場合は、新しいフォルダを作成
        os.makedirs(path)
        print(f"新しいフォルダ '{path}' を作成しました。")
    else:
        print(f"フォルダ '{path}' は既に存在します。")
        

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
        
def join_path_and_filename(directory_path, filename):
    """
    ディレクトリパスとファイル名を結合する
    
    Args:
        directory_path (str): ディレクトリパス
        filename (str): ファイル名
    
    Returns:
        str: 結合されたパス
    """
    full_path = os.path.join(directory_path, filename)
    return full_path

def get_current_time():
    """
    現在のタイムスタンプを取得し、年_月_日_時_分_秒の文字列に変換する
    
    Returns:
        str: 年_月_日_時_分_秒_ミリ秒の文字列
    """
    # 現在のタイムスタンプを取得
    now = datetime.datetime.now()
    
    # 年_月_日_時_分_秒の文字列に変換
    return now.strftime('%Y_%m_%d_%H_%M_%S_%f')

def get_filename_from_folder(folder_path):
    """
    指定したフォルダー内のファイル名をすべて取り出し、リスト型で返す関数
    
    Args:
        folder_path (str): ファイル名を取り出したいフォルダーのパス
    
    Returns:
        list or None: フォルダー内のファイル名のリスト。フォルダが空の場合はNoneを返す。
        指定したパスが存在しない場合もNoneを返し、警告メッセージを表示する。
    """
    try:
        # フォルダー内のファイル名を取得
        file_names = os.listdir(folder_path)
        
        # フォルダが空の場合はNoneを返す
        if not file_names:
            return None
        
        file_names = sorted(file_names)
        
        return file_names
    
    except FileNotFoundError:
        print(f"警告: 指定したパス '{folder_path}' は存在しません。")
        return None
    
def delete_folder(folder_path):
    """
    指定したフォルダーを削除する関数
    
    Args:
        folder_path (str): 削除したいフォルダーのパス
    
    Returns:
        bool: 削除に成功した場合はTrue、失敗した場合はFalseを返す
    """
    try:
        # フォルダーが空の場合は os.rmdir() で削除
        if not os.listdir(folder_path):
            os.rmdir(folder_path)
            print(f"空のフォルダー '{folder_path}' を削除しました。")
            return True
        # フォルダーが空でない場合は shutil.rmtree() で再帰的に削除
        else:
            shutil.rmtree(folder_path)
            print(f"フォルダー '{folder_path}' とその内容を削除しました。")
            return True
    except (OSError, shutil.Error) as e:
        print(f"フォルダー '{folder_path}' の削除に失敗しました: {e}")
        return False
        
def get_parent_directory_path(input_folder_path):
    """
    入力されたパスの親ディレクトリのパスを返す関数
    
    Args:
        input_folder_path (str): 対象となるパス
    
    Returns:
        str: 対象となるパスの親ディレクトリのパス
    """
    # 入力パスの親ディレクトリのパスを取得
    parent_dir_path = os.path.abspath(os.path.join(input_folder_path, os.pardir))
    
    return parent_dir_path

def moveImageToFolder(sourceFilePath, destinationFolderPath):
    """
    フォルダにある画像を別のフォルダに移すコードを作成してください
    入力：元のファイルのパス、移した後のパス
    出力：なし
    """
    try:
        # ファイルが存在することを確認
        if os.path.exists(sourceFilePath):
            # ファイル名を取得
            fileName = os.path.basename(sourceFilePath)
            # 移動先のファイルパスを作成
            destinationFilePath = os.path.join(destinationFolderPath, fileName)
            
            # ファイルを移動
            shutil.move(sourceFilePath, destinationFilePath)
            print(f"Image '{fileName}' has been moved to '{destinationFolderPath}'.")
        else:
            print(f"Error: '{sourceFilePath}' does not exist.")
    except (shutil.Error, IOError) as e:
        print(f"Error moving the image: {e}")
        
def get_str_from_txt(file_path):
    """
    指定したファイルパスのテキストファイルから文字列を取得する関数
    
    Args:
        file_path (str): テキストファイルのパス
    
    Returns:
        str: テキストファイルの内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None
    except UnicodeDecodeError:
        print(f"Error: Unable to decode {file_path} with 'utf-8' encoding.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def load_txt_file(file_path, encoding='utf-8'):
    with open(file_path, 'r', encoding=encoding) as file:
        content = file.read()
    return content

def save_pickle_file(save_folder_path, file_name, mes):
    # Ensure the save folder path exists
    os.makedirs(save_folder_path, exist_ok=True)
    
    # Define the file path
    file_path = os.path.join(save_folder_path, file_name)
    
    # Save the mes object to the file
    with open(file_path, 'wb') as file:
        pickle.dump(mes, file)

    print(f"Data saved to {file_path}")
    
def save_text_file(save_folder_path, file_name, mes, encoding='utf-8', toggle=False):
    # Ensure the save folder path exists
    os.makedirs(save_folder_path, exist_ok=True)
    
    # Define the file path
    file_path = os.path.join(save_folder_path, file_name)

    # If toggle is True, read the existing content and append the new text
    if toggle and os.path.exists(file_path):
        with open(file_path, 'r', encoding=encoding) as file:
            existing_content = file.read()
        mes = existing_content + mes  # Append the new message to the existing content

    # Save the mes object to the file with specified encoding
    with open(file_path, 'w', encoding=encoding) as file:
        file.write(mes)

    print(f"Data saved to {file_path}")


def save_csv_file(save_folder_path, file_name, data):
    """
    この関数はデータをCSVファイルとして保存します。

    Parameters:
    save_folder_path (str): 保存するフォルダのパス
    file_name (str): 保存するファイルの名前
    data (list of list): 保存するデータ
    """
    # Ensure the save folder path exists
    os.makedirs(save_folder_path, exist_ok=True)
    
    # Define the file path
    file_path = os.path.join(save_folder_path, file_name)
    
    # Save the data to the CSV file
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

    print(f"Data saved to {file_path}")

def save_json_file(folder_path, file_name, G):
    """
    グラフをJSONファイルで保存する関数

    Parameters:
    folder_path (str): 保存先のフォルダパス
    file_name (str): 保存するファイル名（.json 拡張子を含む）
    G (networkx.Graph): 保存するNetworkXグラフ

    Returns:
    None
    """
    # フォルダが存在しない場合は作成する
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # フルパスを作成
    file_path = os.path.join(folder_path, file_name)
    
    # グラフをJSON形式に変換
    graph_data = nx.node_link_data(G)
    
    # JSONファイルに書き込む
    with open(file_path, 'w') as json_file:
        json.dump(graph_data, json_file, indent=4)
    
    print(f"Graph saved as JSON in {file_path}")
    
def load_pickle_file(file_path):
    # Load the mes object from the file
    with open(file_path, 'rb') as file:
        mes = pickle.load(file)
    
    return mes


def load_csv_file(file_path):
    """
    この関数はCSVファイルからデータを浮動小数点数として読み込みます。

    Parameters:
    file_path (str): 読み込むファイルのパス

    Returns:
    list of list: 読み込んだデータ
    """
    data = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            # Try to convert each item to float if possible
            converted_row = []
            for item in row:
                try:
                    converted_item = float(item)
                except ValueError:
                    converted_item = item
                converted_row.append(converted_item)
            data.append(converted_row)
    print(f"Data loaded from {file_path}")
    return data

def load_json_as_txt(file_path):
    """
    指定されたファイルパスからJSONファイルを読み込み、
    テキスト形式で返す関数。
    
    :param file_path: 読み込むJSONファイルのパス
    :return: JSONデータのテキスト形式
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
    return json.dumps(data, indent=4)

def load_json_as_graph(file_path):
    """
    指定されたパスからjsonファイルを読み込みnetworkxのグラフに変換します。
    
    :param file_path: JSONファイルのパス
    :return: NetworkXのグラフオブジェクト
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # グラフの初期化
    G = nx.Graph()

    # JSONデータからグラフのエッジを追加
    for edge in data.get('edges', []):
        source = edge.pop('source')
        target = edge.pop('target')
        G.add_edge(source, target, **edge)

    # JSONデータからグラフのノードを追加
    for node in data.get('nodes', []):
        node_id = node.pop('id')
        G.add_node(node_id, **node)

    return G

def check_folder_exists(folder_path):
    """
    Check if the specified folder path exists and is a directory.

    Parameters:
    folder_path (str): The path to the folder.

    Returns:
    bool: True if the folder exists and is a directory, False otherwise.
    """
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        print(f"The folder '{folder_path}' exists.")
        return True
    else:
        print(f"The folder '{folder_path}' does not exist.")
        return False
        
if __name__ == "__main__":
    print(get_current_path())