import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from query_layout import inspect_layout, search


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'examples/VirtualDefy.json'


def source():
    return json.loads(SOURCE.read_text(encoding='utf-8'))


def set_key(doc, layer, index, code):
    keys = doc['virtual']['keymap.custom']['data'].split()
    keys[(layer - 1) * 80 + index] = str(code)
    doc['virtual']['keymap.custom']['data'] = ' '.join(keys)


class QueryLayoutTest(unittest.TestCase):
    def test_geometry_and_neighbors_cover_both_halves_and_thumb(self):
        rows = inspect_layout(source())['positions']
        self.assertEqual(len(rows), 710)
        by_id = {(r['layer'], r['position_id']): r for r in rows}
        left = by_id[1, 'defy:left:r3:c5']
        self.assertEqual((left['side'], left['row'], left['column'], left['key_index'], left['l1_label']),
                         ('left', 3, 5, 36, 'F'))
        self.assertIn('L1 D', left['nearby'])
        right = by_id[1, 'defy:right:r4:c2']
        self.assertEqual((right['side'], right['key_index']), ('right', 58))
        self.assertIn('L1 M', right['nearby'])
        thumb = by_id[1, 'defy:right:r5:c4']
        self.assertIn('thumb', thumb['landmark'])
        self.assertIn('L1', thumb['nearby'])

    def test_duplicate_outputs_and_changed_l1_label(self):
        doc = source()
        set_key(doc, 1, 36, 20)  # Q at the physical F position.
        result = inspect_layout(doc)
        q = next(r for r in result['positions'] if r['layer'] == 1 and r['key_index'] == 36)
        self.assertEqual(q['l1_label'], 'Q')
        spaces = search(result, 'Space')['confirmed_matches']
        self.assertTrue(all(r['output'] != 'Backspace' for r in spaces))
        l1_spaces = [r for r in spaces if r['layer'] == 1]
        self.assertGreaterEqual(len(l1_spaces), 2)
        self.assertEqual({r['side'] for r in l1_spaces}, {'left', 'right'})

    def test_manifest_match_mismatch_and_unsupported_are_distinct(self):
        doc = source()
        set_key(doc, 4, 36, 4105)  # Cmd+F.
        template = {
            'schema_version': 1, 'id': 'sample', 'name': 'Sample',
            'platforms': ['macos'], 'bindings': [
                {'id': 'find', 'name': 'Find files', 'position_id': 'defy:left:r3:c5',
                 'position_l1': 'F', 'color_category': 'search',
                 'shortcuts': {'macos': 'Cmd+F'}},
                {'id': 'open', 'name': 'Open dashboard', 'position_id': 'defy:right:r4:c2',
                 'position_l1': 'N', 'color_category': 'app',
                 'shortcuts': {'macos': 'Cmd+N'}},
                {'id': 'lock', 'name': 'Lock utility layer', 'position_id': 'defy:right:r5:c4',
                 'position_l1': 'Macro 1', 'color_category': 'activation',
                 'bazecor_action': {'type': 'layer-lock', 'target': 'utility'}},
            ],
        }
        manifest = {'schema_version': 1, 'id': 'sample-pc', 'profile': 'profile.json',
                    'layer_targets': {'utility': 4},
                    'layers': [{'layer': 4, 'template': 'sample.json'}]}
        profile = {'schema_version': 1, 'id': 'sample', 'os': 'macos'}
        result = inspect_layout(doc, manifest, profile, lambda _: template)
        self.assertEqual([r['status'] for r in result['actions']],
                         ['confirmed', 'mismatch', 'unverified'])
        self.assertEqual(len(search(result, 'Find files')['confirmed_matches']), 1)
        self.assertEqual(len(search(result, 'Open dashboard')['confirmed_matches']), 0)
        self.assertEqual(len(search(result, 'Lock utility layer')['proposed_matches']), 1)

    def test_copied_device_command_is_recognized_after_original_is_cleared(self):
        doc = source()
        set_key(doc, 1, 73, 65535)
        set_key(doc, 4, 78, 54108)
        template = {'schema_version': 1, 'id': 'device', 'name': 'Device',
                    'platforms': ['macos'], 'bindings': [{
                        'id': 'battery', 'name': 'Show battery level',
                        'position_id': 'defy:right:r5:c7', 'position_l1': 'Right Alt',
                        'color_category': 'system',
                        'bazecor_action': {'type': 'device-command', 'command': 'battery-level'},
                    }]}
        manifest = {'schema_version': 1, 'id': 'pc', 'layers': [
            {'layer': 4, 'template': 'device.json'}]}
        profile = {'schema_version': 1, 'id': 'pc', 'os': 'macos'}
        result = inspect_layout(doc, manifest, profile, lambda _: template)
        self.assertEqual(result['actions'][0]['status'], 'confirmed')

    def test_access_is_reported_only_for_confirmed_entry_key(self):
        doc = source()
        template = {'schema_version': 1, 'id': 'entry', 'name': 'Entry',
                    'platforms': ['macos'], 'bindings': [{
                        'id': 'open', 'name': 'Open utility layer',
                        'position_id': 'defy:left:r5:c1', 'position_l1': 'Super 1',
                        'color_category': 'activation',
                        'bazecor_action': {'type': 'one-shot-layer', 'target': 'utility'},
                    }]}
        manifest = {'schema_version': 1, 'id': 'pc', 'layer_targets': {'utility': 4},
                    'layers': [{'layer': 1, 'template': 'entry.json'}]}
        profile = {'schema_version': 1, 'id': 'pc', 'os': 'macos'}
        rows = inspect_layout(doc, manifest, profile, lambda _: template)['positions']
        self.assertEqual(next(r for r in rows if r['layer'] == 4)['access'],
                         'No verified entry in manifest')
        set_key(doc, 1, 64, 49164)
        rows = inspect_layout(doc, manifest, profile, lambda _: template)['positions']
        self.assertIn('one-shot-layer to L4', next(r for r in rows if r['layer'] == 4)['access'])

    def test_cli_reads_inputs_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.json'
            path.write_bytes(SOURCE.read_bytes())
            before = path.read_bytes()
            completed = subprocess.run(
                [sys.executable, str(ROOT / 'scripts/query_layout.py'), str(path),
                 '--query', 'Space', '--format', 'json'],
                check=True, capture_output=True, text=True,
            )
            answer = json.loads(completed.stdout)
            self.assertGreaterEqual(len(answer['confirmed_matches']), 2)
            self.assertEqual(path.read_bytes(), before)
            inventory = subprocess.run(
                [sys.executable, str(ROOT / 'scripts/query_layout.py'), str(path),
                 '--inventory', '--format', 'json'],
                check=True, capture_output=True, text=True,
            )
            self.assertEqual(len(json.loads(inventory.stdout)['positions']), 710)
            self.assertEqual(path.read_bytes(), before)

    def test_cli_with_manifest_preserves_all_inputs(self):
        paths = [SOURCE, ROOT / 'profiles/macos-init.example.json',
                 ROOT / 'profiles/macos.example.json']
        before = [path.read_bytes() for path in paths]
        completed = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/query_layout.py'), str(paths[0]),
             '--manifest', str(paths[1]), '--query', 'Space', '--format', 'json'],
            check=True, capture_output=True, text=True,
        )
        answer = json.loads(completed.stdout)
        self.assertGreaterEqual(len(answer['confirmed_matches']), 2)
        self.assertEqual([path.read_bytes() for path in paths], before)


if __name__ == '__main__':
    unittest.main()
