# -*- coding: utf-8 -*-
"""
Offline tests for the task-planning pipeline (no OpenAI / Google Vision calls).

Each folder in tests/fixtures/ is a recorded run from the evaluation experiments
(subtitles and graphs only; the video frames are not distributed):
    G_list.pickle      target object nodes   (output of MainFunctionUnit_Generator)
    EO000.json         environment node      (output of EnvObjectNode)
    result.pickle      FOON per target       (output of TaskPlanner)
    llm_answers.json   final accepted LLM answer per target (from FOON/prompt_list.pickle)
Some runs also have the stage 2 inputs:
    Target_Object_list.pickle   recorded LLM estimate per image (Object_folder/)
    word_dic.pickle             subtitles per image             (GPT4o_input_img/word_dic)

Run from the repository root:
    python -m unittest discover -s tests -v
"""
import builtins
import contextlib
import io
import json
import os
import pickle
import shutil
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FIXTURES = os.path.join(REPO_ROOT, 'tests', 'fixtures')
sys.path.insert(0, os.path.join(REPO_ROOT, 'scripts'))
# GPT_manipulation needs a key to construct the client; no request is ever sent.
os.environ.setdefault('OPENAI_API_KEY', 'offline-test')

import networkx as nx
import EnvObjectNode
import FOONGenerator
import GPT_manipulation
import MainFunctionUnit_Generator
import TaskPlanner

RUNS = sorted(d for d in os.listdir(FIXTURES) if os.path.isdir(os.path.join(FIXTURES, d)))


def load_run(run):
    folder = os.path.join(FIXTURES, run)
    with open(os.path.join(folder, 'G_list.pickle'), 'rb') as f:
        G_list = pickle.load(f)
    with open(os.path.join(folder, 'result.pickle'), 'rb') as f:
        result = pickle.load(f)
    with open(os.path.join(folder, 'llm_answers.json'), encoding='utf-8') as f:
        answers = json.load(f)
    return folder, G_list, result, answers


def graph_signature(G):
    """ノード属性とエッジで比較 / Compare by node attributes and edges"""
    # 'id' duplicates the node key and is dropped when a graph is loaded from JSON.
    nodes = {n: json.dumps({k: v for k, v in d.items() if k != 'id'}, sort_keys=True) for n, d in G.nodes(data=True)}
    return nodes, set(G.edges())


class OfflineTestCase(unittest.TestCase):
    def setUp(self):
        # Run inside a temp dir: the pipeline writes intermediate files (e.g. ./graph.eps) to the cwd.
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        cwd = os.getcwd()
        os.chdir(self.tmp)
        self.addCleanup(os.chdir, cwd)
        # The code pauses on input() for debugging; never block the tests.
        patcher = mock.patch.object(builtins, 'input', lambda *args: '')
        patcher.start()
        self.addCleanup(patcher.stop)

    def quiet(self):
        return contextlib.redirect_stdout(io.StringIO())


class TestTargetObjectNodes(OfflineTestCase):
    def generate(self, run):
        """記録された推定結果から目標オブジェクトノードを生成 / Build target object nodes from the recorded LLM estimates"""
        folder = os.path.join(FIXTURES, run)
        with open(os.path.join(folder, 'Target_Object_list.pickle'), 'rb') as f:
            targets = pickle.load(f)
        # Every image already has a recorded estimate, so the images themselves are never read.
        input_folder = os.path.join(self.tmp, run, 'GPT4o_input_img')
        os.makedirs(input_folder)
        for img_name, _ in targets:
            open(os.path.join(input_folder, img_name), 'w').close()
        shutil.copy(os.path.join(folder, 'word_dic.pickle'), input_folder)
        os.makedirs(os.path.join(self.tmp, run, 'Object_folder'))
        shutil.copy(os.path.join(folder, 'Target_Object_list.pickle'), os.path.join(self.tmp, run, 'Object_folder'))

        def no_llm(gpt):
            self.fail('MainFunctionUnit_Generator called the LLM although every estimate is recorded')

        # Stage 2 must run unattended: fail on any input() pause.
        with mock.patch.object(GPT_manipulation.GPT_manipulation, 'GPT4o_exe', no_llm), \
             mock.patch.object(builtins, 'input', side_effect=AssertionError('input() called')), \
             self.quiet() as out:
            G_list, _ = MainFunctionUnit_Generator.MainFunctionUnit_Generator().main(input_folder, 'test')
        return G_list, out.getvalue()

    def test_rebuilds_recorded_target_nodes(self):
        # In this run the saved G_list was not edited by hand, so it must be reproduced exactly.
        run = 'run_2025_01_21_02_49_01'
        G_list, _ = self.generate(run)
        _, recorded, _, _ = load_run(run)
        self.assertEqual([graph_signature(G) for G in G_list], [graph_signature(G) for G in recorded])

    def test_skips_unsupported_object_types(self):
        # combined_image_16 shows the finished dish; the LLM answered with type 'dish'.
        G_list, log = self.generate('run_2025_01_21_02_38_47')
        self.assertIn("Skipping combined_image_16.jpg: unsupported object type(s) ['dish']", log)
        self.assertFalse(any(n.startswith('TO_016') for G in G_list for n in G.nodes))
        for G in G_list:
            for _, d in G.nodes(data=True):
                self.assertIn(d['type'], ['motion', 'ingredients', 'container', 'machine', 'tool'])


class TestEnvObjectNode(OfflineTestCase):
    def test_rebuilds_recorded_environment(self):
        for run in RUNS:
            with self.subTest(run=run):
                folder, G_list, _, _ = load_run(run)
                object_folder = os.path.join(self.tmp, run, 'Object_folder')
                with self.quiet():
                    json_path = EnvObjectNode.EnvObjectNode().main(G_list, object_folder)
                with open(json_path) as f:
                    new = json.load(f)
                with open(os.path.join(folder, 'EO000.json')) as f:
                    old = json.load(f)
                # Placement and ID order are random, so compare which objects exist.
                key = lambda data: sorted((n.get('label'), n.get('type')) for n in data['nodes'])
                self.assertEqual(key(new), key(old))


class TestTaskPlannerReplay(OfflineTestCase):
    def replay(self, run, answers):
        """記録されたLLM応答でTaskPlannerを実行 / Run TaskPlanner with recorded LLM answers"""
        folder, G_list, _, _ = load_run(run)
        answers = list(answers)
        calls = []

        def fake_llm(gpt):
            calls.append(gpt.prompt[-1]['content'])
            if not answers:
                self.fail(f'TaskPlanner requested more LLM answers than recorded ({len(calls)} calls)')
            return answers.pop(0)

        def recorded_environment(eo, G, Object_folder):
            # Use the recorded environment: a new random placement would not match the recorded plans.
            path = os.path.join(folder, 'EO000.json')
            with open(path) as f:
                eo.enviroment_node = nx.node_link_graph(json.load(f))
            return path

        # Keep FOONGenerator from writing its logs into the repository's prompt/ folder.
        work = tempfile.mkdtemp(dir=self.tmp)
        fewshot = os.path.join(work, 'fewshot')
        os.makedirs(fewshot)
        shutil.copy(os.path.join(REPO_ROOT, 'prompt', 'taskplanning_without_Area', 'taskplan_setup.pickle'), fewshot)
        foon_main = FOONGenerator.FOONGenerator.main

        def foon_main_tmp(self_, EG, graph, save_file_path):
            return foon_main(self_, EG, graph, Fewshot_folder_path=fewshot, save_file_path=save_file_path)

        save_folder = os.path.join(work, 'FOON')
        with mock.patch.object(GPT_manipulation.GPT_manipulation, 'GPT4o_exe', fake_llm), \
             mock.patch.object(EnvObjectNode.EnvObjectNode, 'main', recorded_environment), \
             mock.patch.object(FOONGenerator.FOONGenerator, 'main', foon_main_tmp), \
             self.quiet():
            TaskPlanner.TaskPlanner().main(G_list, os.path.join(work, 'Object_folder'), save_folder)
        with open(os.path.join(save_folder, 'result.pickle'), 'rb') as f:
            return pickle.load(f), calls

    def assertSameResult(self, new, old):
        self.assertEqual(len(new), len(old))
        for i, (n, o) in enumerate(zip(new, old)):
            self.assertEqual(graph_signature(n[0]), graph_signature(o[0]), f'FOON differs at target {i}')
            self.assertEqual(graph_signature(n[1]), graph_signature(o[1]), f'environment differs at target {i}')

    def test_replay_reproduces_recorded_foon(self):
        for run in RUNS:
            with self.subTest(run=run):
                _, _, result, answers = load_run(run)
                new, calls = self.replay(run, answers)
                self.assertEqual(len(calls), len(answers))
                self.assertSameResult(new, result)

    def test_invalid_plan_triggers_error_recovery(self):
        # Answer target 0 with the last target's plan (its ingredients are not in the pan yet):
        # the validator must reject it, ask for a correction, and accept the recorded plan on the retry.
        run = RUNS[0]
        _, _, result, answers = load_run(run)
        new, calls = self.replay(run, [answers[-1]] + answers)
        self.assertEqual(len(calls), len(answers) + 1)
        self.assertSameResult(new, result)


def wrs_available():
    try:
        import panda3d, open3d, sklearn  # noqa: F401  (motion planning dependencies)
    except ImportError:
        return False
    return True


@unittest.skipUnless(wrs_available(), 'motion planning dependencies (panda3d, open3d, scikit-learn) not installed')
class TestMotionPlanningAssets(OfflineTestCase):
    def test_every_modelled_object_has_stl_and_grasps(self):
        for path in ('motion_planning', 'wrs', ''):
            sys.path.insert(0, os.path.join(REPO_ROOT, path))
        import File_management as Fm
        import Motion_planner
        for run in RUNS:
            with self.subTest(run=run):
                EG = Fm.load_json_as_graph(os.path.join(FIXTURES, run, 'EO000.json'))
                with self.quiet():
                    Motion_planner.MotionPrep(None).set_stl(EG)
                files = [d[a] for _, d in EG.nodes(data=True) for a in ('stl_path', 'grasp_info_list') if a in d]
                self.assertTrue(files)
                for f in files:
                    self.assertTrue(os.path.isfile(f), f)


if __name__ == '__main__':
    unittest.main()
