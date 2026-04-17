# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 12:00:24 2024

@author: user
"""

import networkx as nx
from graphviz import Digraph
import matplotlib.pyplot as plt
import os
import tempfile
import shutil

def update_graph_attributes(souce_graph, turget_graph, node_name_list):
    """
    souce_graphのにあるノードの属性をturget_graphにあるノードの属性に書き換える関数
    入力:
        souce_graph: コピーする側のグラフ
        turget_graph: コピーされる側のグラフ
        node_name_list: [[souce_node_name1, turget_node_name1], [souce_node_name2, turget_node_name2], ... ]
    """
    for node_name in node_name_list:
        keys_ = souce_graph.nodes[node_name[0]].keys()
        for key in keys_:
            if key in turget_graph.nodes[node_name[1]].keys():
                turget_graph.nodes[node_name[1]][key] = souce_graph.nodes[node_name[0]][key]

# def visualize_graph_with_graphviz(graph, attributes=[], filename="graph", output_dir="."):
#     """
#     Graphvizを使用してNetworkXのグラフを可視化します。指定された属性も出力します。
#     属性がない場合は出力しません。

#     入力:
#         graph: NetworkXのグラフオブジェクト
#         attributes: 属性名のリスト
#         filename: 保存するファイル名（デフォルトは "graph"）
#         output_dir: 保存するディレクトリ（デフォルトはカレントディレクトリ）
#     """
#     # 一時ディレクトリを作成
#     with tempfile.TemporaryDirectory() as tempdir:
#         filepath = os.path.join(tempdir, filename)

#         # GraphvizのDigraphオブジェクトを作成
#         dot = Digraph()

#         # グラフのノードを追加
#         for node in graph.nodes(data=True):
#             label = str(node[0])
#             for attr in attributes:
#                 if attr in node[1]:
#                     label += f"\n{attr}: {node[1][attr]}"
#             if '_A' in str(node[0]):
#                 dot.node(str(node[0]), color='red', style='filled', fillcolor='red', label=label)
#             else: 
#                 dot.node(str(node[0]), color='blue', label=label)

#         # グラフのエッジを追加
#         for source, target, data in graph.edges(data=True):
#             label = ""
#             for attr in attributes:
#                 if attr in data:
#                     label += f"{attr}: {data[attr]}\n"
#             dot.edge(str(source), str(target), label=label.strip())

#         # グラフをファイルとして保存
#         dot.render(filepath, format='png', cleanup=True)  # cleanup=Trueは中間ファイルを削除

#         # 一時ファイルから指定したディレクトリにファイルをコピー
#         final_path = os.path.join(output_dir, f"{filename}.png")
#         shutil.copyfile(f"{filepath}.png", final_path)

#         # 保存した画像を表示
#         img = plt.imread(final_path)
#         plt.imshow(img)
#         plt.axis('off')
#         plt.show()

import os
import shutil
import tempfile
import matplotlib.pyplot as plt
from graphviz import Digraph

def visualize_graph_with_graphviz(graph, attributes=[], filename="graph", output_dir=".", output_format='eps'):
    """
    Graphvizを使用してNetworkXのグラフを可視化します。指定された属性も出力します。
    """
    # 一時ディレクトリを作成
    with tempfile.TemporaryDirectory() as tempdir:
        filepath = os.path.join(tempdir, filename)
        dot = Digraph()
        
        # ノードを追加
        for node, data in graph.nodes(data=True):
            if data.get('label') == 'Pic':
                label = f"label: Pick\n"
            else:
                label = f"label: {data.get('label', node)}\n"
            for attr in attributes:
                if attr in data:
                    label += f"{attr}: {data[attr]}\n"
            
            if data.get('label') in ['Pic', 'Place', 'Pour', 'Cut']:
                dot.node(str(node), color='black', style='filled', fillcolor='lightcoral', label=label, fontsize="24")
            else:
                dot.node(str(node), color='black', style='filled', fillcolor='lightskyblue', label=label, fontsize="18")

        # エッジを追加
        for source, target, data in graph.edges(data=True):
            label = ""
            for attr in attributes:
                if attr in data:
                    label += f"{attr}: {data[attr]}\n"
            dot.edge(str(source), str(target), label=label.strip(), color="gray")
        
        # グラフをファイルとして保存
        dot.render(filepath, format=output_format, cleanup=True)
        final_path = os.path.join(output_dir, f"{filename}.{output_format}")
        shutil.copyfile(f"{filepath}.{output_format}", final_path)
        
        # PNG形式の場合のみ表示
        if output_format == 'png':
            img = plt.imread(final_path)
            plt.imshow(img)
            plt.axis('off')
            plt.show()
        
        print(f"Graph saved as {final_path}")

    

def connect_nodes(target_graph, source_node_name_list, target_node_name_list):
    """
    この関数はtarget_graph内にあるsource_node_name_listとtarget_node_name_listをエッジでつなぐ関数です.
    source_node_name_listからtarget_node_name_listへエッジを繋いでください.

    入力:
        target_graph: source_node_name_listとtarget_node_name_listが格納されたグラフ
        source_node_name_list: target_node_name_listに繋ぐノード名のリスト
        target_node_name_list: source_node_name_listから繋がれるノード名のリスト
    """
    for source_node in source_node_name_list:
        for target_node in target_node_name_list:
            target_graph.add_edge(source_node, target_node)
    

def copy_node_with_new_name(source_graph, target_graph, old_node, new_node):
    """
    Copy a node in a directed graph with a new name, including its attributes and edges.
    If the new node already exists in the target graph, its attributes will be updated.

    Parameters:
    source_graph (nx.DiGraph): The source directed graph.
    target_graph (nx.DiGraph): The target directed graph.
    old_node (str or int): The node to be copied.
    new_node (str or int): The new name for the copied node.

    Returns:
    None
    """
    if old_node not in source_graph.nodes:
        raise ValueError(f"The node {old_node} does not exist in the source graph.")


    if new_node in target_graph.nodes:
        for key in source_graph.nodes[old_node].keys():
            target_graph.nodes[new_node][key] = source_graph.nodes[old_node][key]
    else:
        target_graph.add_node(new_node, **source_graph.nodes[old_node])
    
def find_output_nodes_from(digraph, start_node):
    """
    指定されたノードからの出力ノードを検索する関数。

    Parameters:
    digraph (networkx.DiGraph): 有効グラフ
    start_node: 開始ノード

    Returns:
    list: 出力ノードのリスト
    """
    
    # 到達可能なノードの中で out-degree が 0 のノードを検索
    output_nodes = [edge[1] for edge in digraph.edges() if edge[0] == start_node]
    
    return output_nodes

def get_sub_nodes_and_edges(graph, action_nodes, i):
    """
    連続する3つのアクションノードを含む部分グラフを作成し、
    それに関連するノードとエッジを取得します。
    
    Parameters:
    - graph: networkx のグラフ
    - action_nodes: アクションノードのリスト
    - i: 取り出す連続するアクションノードの開始インデックス
    
    Returns:
    - sub_nodes: 部分グラフのノード集合
    - sub_edges: 部分グラフのエッジのリスト
    """
    sub_actions = action_nodes[i:i+3]  # 連続する3つのアクションノード
    sub_nodes = set(sub_actions)
    sub_edges = []

    extra_nodes = set()
    for action_node in sub_actions:
        for source, target in graph.edges:
            if source == action_node and "_A" not in target:
                extra_nodes.add(target)
                sub_edges.append((source, target))
            elif target == action_node and "_A" not in source:
                extra_nodes.add(source)
                sub_edges.append((source, target))

    sub_nodes.update(extra_nodes)
    return sub_actions, sub_nodes, sub_edges

def render_and_save_graph(dot, sub_nodes, sub_edges, graph, highlight_node, highlight_connected, node_size_ratio, font_size_ratio, save_folder, i):
    """
    グラフを描画して保存する関数。
    
    Parameters:
    - dot: Graphviz の Digraph オブジェクト
    - sub_nodes: 部分グラフのノード集合
    - sub_edges: 部分グラフのエッジのリスト
    - graph: networkx のグラフ
    - highlight_node: 強調するノード
    - highlight_connected: 強調ノードに接続されたノードの集合
    - node_size_ratio: ノードのサイズを調整する比率
    - font_size_ratio: フォントサイズを調整する比率
    - save_folder: 画像保存先のフォルダパス
    - i: ファイル名に使用するインデックス
    """
    for node in sub_nodes:
        label = graph.nodes[node].get("label", node)
        if label == "Pic":
            label = "Pick"
        if node == highlight_node:
            dot.node(node, label, fontsize=str(10 * font_size_ratio), width=str(0.5 * node_size_ratio), height=str(0.5 * node_size_ratio), fillcolor="red", style="filled")
        elif node in highlight_connected:
            dot.node(node, label, fontsize=str(8 * font_size_ratio), width=str(0.4 * node_size_ratio), height=str(0.4 * node_size_ratio), fillcolor="lightgray", style="filled")
        else:
            dot.node(node, label, fontsize=str(6 * font_size_ratio), width=str(0.3 * node_size_ratio), height=str(0.3 * node_size_ratio))

    for source, target in sub_edges:
        dot.edge(source, target)

    filename = os.path.join(save_folder, f'graph_{i}')
    dot.render(filename, cleanup=True)
    print(f"Saved {filename}")

def make_graph_image_three_action_nodes(graph, save_folder='/path/to/graph', node_size_ratio=1.5, font_size_ratio=1.5):
    """
    指定された networkx の有向グラフから、アクションノード（"FO_XXX_A"）を3つ含む部分グラフを作成し、
    Graphviz を用いて画像を生成する。
    強調ノードは1回目、2回目、3回目で順番に変わり、それに合わせて3つのアクションノードの中の強調ノードを変更します。
    """
    import os
    from graphviz import Digraph
    
    os.makedirs(save_folder, exist_ok=True)
    
    action_nodes = [node for node in graph.nodes if "_A" in node]
    
    for i in range(len(action_nodes) - 2):
    
        # 強調ノードは回ごとに変更（1回目は1、2回目は2、3回目は3）
        if i == 0:
            sub_actions, sub_nodes, sub_edges = get_sub_nodes_and_edges(graph, action_nodes, i)
            highlight_node = sub_actions[0]  # 1回目は1番目のノードを強調
            highlight_connected = {node for source, node in sub_edges if source == highlight_node}
            highlight_connected |= {source for source, node in sub_edges if node == highlight_node}
            dot = Digraph(format='png')
            render_and_save_graph(dot, sub_nodes, sub_edges, graph, highlight_node, highlight_connected, node_size_ratio, font_size_ratio, save_folder, -2)
            sub_actions, sub_nodes, sub_edges = get_sub_nodes_and_edges(graph, action_nodes, i)
            highlight_node = sub_actions[1]  # 1回目は1番目のノードを強調
            highlight_connected = {node for source, node in sub_edges if source == highlight_node}
            highlight_connected |= {source for source, node in sub_edges if node == highlight_node}
            dot = Digraph(format='png')
            render_and_save_graph(dot, sub_nodes, sub_edges, graph, highlight_node, highlight_connected, node_size_ratio, font_size_ratio, save_folder, -1)
        else:
            sub_actions, sub_nodes, sub_edges = get_sub_nodes_and_edges(graph, action_nodes, i)
            highlight_node = sub_actions[1]  # 3回目は3番目のノードを強調
    
        highlight_connected = {node for source, node in sub_edges if source == highlight_node}
        highlight_connected |= {source for source, node in sub_edges if node == highlight_node}
        dot = Digraph(format='png')
        render_and_save_graph(dot, sub_nodes, sub_edges, graph, highlight_node, highlight_connected, node_size_ratio, font_size_ratio, save_folder, i)

        



if __name__=="__main__":  
    import File_management as Fm
    result = Fm.load_pickle_file('/to/path/FOON/result.pickle')
    graph = result[-1][0]
    make_graph_image_three_action_nodes(graph)
    
    
    
