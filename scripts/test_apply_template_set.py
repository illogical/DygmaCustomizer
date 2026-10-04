import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from apply_template_set import compose
from defy import model
from resolve_template import read_json


ROOT = Path(__file__).resolve().parents[1]


class ApplyTemplateSetTest(unittest.TestCase):
    def setUp(self):
        self.source = read_json(ROOT / 'examples/VirtualDefy.json')
        self.profile = {'schema_version': 1, 'id': 'test', 'os': 'macos', 'available_apps': []}
        self.template = {'schema_version': 1, 'id': 'save', 'name': 'Save', 'platforms': ['macos'],
                         'bindings': [{'id': 'save', 'name': 'Save', 'position_l1': 'S',
                                       'position_id': 'defy:left:r3:c3', 'color_category': 'app',
                                       'shortcuts': {'macos': 'Cmd+S'}}]}

    def test_compose_two_layers_preserves_unselected_layers_and_commands(self):
        manifest = {'schema_version': 1, 'id': 'test', 'layers': [
            {'layer': 4, 'template': 'a.json', 'color_slots': {'5': 'app'}},
            {'layer': 5, 'template': 'b.json', 'color_slots': {'5': 'app'}}]}
        before = copy.deepcopy(self.source)
        output, reports, blockers = compose(self.source, self.source, manifest, self.profile,
                                           lambda path: self.template)
        self.assertFalse(blockers)
        self.assertEqual(len(reports), 2)
        original = model(before)[1]
        updated = model(output)[1]
        changes = [i for i, (a, b) in enumerate(zip(original['keymap.custom'], updated['keymap.custom'])) if a != b]
        self.assertEqual(changes, [3*80+34, 4*80+34])
        self.assertEqual(output['virtual']['palette'], before['virtual']['palette'])

    def test_blocked_template_does_not_mutate_input(self):
        manifest = {'schema_version': 1, 'id': 'test', 'layers': [{'layer': 4, 'template': 'a.json'}]}
        before = copy.deepcopy(self.source)
        _, _, blockers = compose(self.source, self.source, manifest, self.profile,
                                 lambda path: self.template)
        self.assertTrue(blockers)
        self.assertEqual(self.source, before)

    def test_replace_one_layer_removes_old_action_and_keeps_other_layer(self):
        manifest = {'schema_version': 1, 'id': 'test', 'layers': [
            {'layer': 4, 'template': 'a.json'}, {'layer': 5, 'template': 'b.json'}]}
        initial, _, blockers = compose(self.source, self.source, manifest, self.profile,
                                       lambda path: self.template, with_colors=False)
        self.assertFalse(blockers)
        replacement = copy.deepcopy(self.template)
        replacement['bindings'][0]['position_l1'] = 'F'
        replacement['bindings'][0]['position_id'] = 'defy:left:r3:c5'
        updated, _, blockers = compose(initial, self.source, manifest, self.profile,
                                       lambda path: replacement, only_layer=5,
                                       with_colors=False, policy='replace-layer')
        self.assertFalse(blockers)
        old_keys = model(initial)[1]['keymap.custom']
        new_keys = model(updated)[1]['keymap.custom']
        self.assertEqual(new_keys[3*80:4*80], old_keys[3*80:4*80])
        self.assertEqual(new_keys[4*80+34], 65535)
        self.assertEqual(new_keys[4*80+36], 4118)

    def test_colors_only_keeps_key_assignments(self):
        manifest = {'schema_version': 1, 'id': 'test', 'layers': [
            {'layer': 1, 'template': 'a.json', 'color_slots': {'5': 'app'}}]}
        updated, _, blockers = compose(self.source, self.source, manifest, self.profile,
                                       lambda path: self.template, with_keys=False)
        self.assertFalse(blockers)
        self.assertEqual(model(updated)[1]['keymap.custom'], model(self.source)[1]['keymap.custom'])
        self.assertNotEqual(model(updated)[1]['colormap.map'], model(self.source)[1]['colormap.map'])

    def test_cli_failure_creates_no_partial_output(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = Path(folder) / 'set.json'
            output = Path(folder) / 'output.json'
            manifest.write_text(json.dumps({'schema_version': 1, 'id': 'test',
                                            'layers': [{'layer': 4, 'template': 'templates/macos-navigation.json'}]}))
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/apply_template_set.py'),
                                     'apply', str(ROOT / 'examples/VirtualDefy.json'), str(manifest),
                                     '--profile', str(ROOT / 'profiles/macos.example.json'),
                                     '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
