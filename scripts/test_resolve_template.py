import json
import unittest
from pathlib import Path

from resolve_template import physical_position, resolve


ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


class ResolveTemplateTest(unittest.TestCase):
    def test_thumb_position_ids_resolve_to_stable_defy_slots(self):
        source = load('examples/VirtualDefy.json')
        expected = {
            'defy:left:r5:c1': 64,  # Super 1 in the supplied L1 screenshot
            'defy:right:r5:c4': 75,  # Macro 1
            'defy:right:r5:c7': 78,  # Battery level
            'defy:right:r5:c8': 79,  # Bluetooth pairing
        }
        for position_id, index in expected.items():
            with self.subTest(position_id=position_id):
                self.assertEqual(physical_position(source, position_id), index)

    def test_action_bindings_resolve_profile_layer_roles(self):
        template = {
            'schema_version': 1, 'id': 'navigation', 'name': 'Navigation',
            'platforms': ['macos'], 'bindings': [{
                'id': 'app_launcher', 'name': 'Open app launcher',
                'position_l1': 'Super 1', 'position_id': 'defy:left:r5:c1',
                'color_category': 'activation',
                'bazecor_action': {'type': 'one-shot-layer', 'target': 'app_launcher'},
            }],
        }
        profile = {'schema_version': 1, 'id': 'test', 'os': 'macos',
                   'layer_targets': {'app_launcher': 4}}
        result = resolve(template, 'macos', profile, load('examples/VirtualDefy.json'))
        self.assertEqual(result['bindings'][0]['bazecor_action']['target_layer'], 4)

    def test_action_binding_requires_a_known_destination_role(self):
        template = {
            'schema_version': 1, 'id': 'navigation', 'name': 'Navigation',
            'platforms': ['macos'], 'bindings': [{
                'id': 'app_launcher', 'name': 'Open app launcher',
                'position_l1': 'Super 1', 'position_id': 'defy:left:r5:c1',
                'color_category': 'activation',
                'bazecor_action': {'type': 'one-shot-layer', 'target': 'missing'},
            }],
        }
        profile = {'schema_version': 1, 'id': 'test', 'os': 'macos', 'layer_targets': {}}
        with self.assertRaisesRegex(ValueError, 'layer_targets'):
            resolve(template, 'macos', profile, load('examples/VirtualDefy.json'))

    def test_vscode_uses_actual_platform_navigation_shortcuts(self):
        template = load('templates/vscode.json')
        source = load('examples/VirtualDefy.json')
        mac = resolve(template, 'macos', source=source)
        windows = resolve(template, 'windows', source=source)
        linux = resolve(template, 'linux', source=source)
        self.assertEqual(len(mac['bindings']), 7)
        self.assertEqual([r['shortcut'] for r in mac['bindings'] if r['id'] == 'go_back'], ['Ctrl+Minus'])
        self.assertEqual([r['shortcut'] for r in windows['bindings'] if r['id'] == 'go_back'], ['Alt+Left'])
        self.assertEqual([r['shortcut'] for r in linux['bindings'] if r['id'] == 'go_back'], ['Ctrl+Alt+Minus'])
        self.assertEqual([r['position_index'] for r in mac['bindings'] if r['id'] == 'search_files'], [36])

    def test_raycast_profile_expands_hyper_and_filters_absent_app(self):
        template = load('templates/app-launcher.json')
        profile = load('profiles/macos.example.json')
        profile['available_apps'].append('vivaldi')
        profile['shortcut_overrides']['app-launcher.vivaldi'] = 'Hyper+V'
        result = resolve(template, 'macos', profile)
        self.assertEqual(len(result['bindings']), 3)
        self.assertEqual(next(r['shortcut'] for r in result['bindings'] if r['id'] == 'vivaldi'),
                         'Ctrl+Alt+Cmd+Shift+V')
        profile['available_apps'].remove('vivaldi')
        filtered = resolve(template, 'macos', profile)
        self.assertEqual(len(filtered['bindings']), 2)
        self.assertTrue(any(action == 'vivaldi' for action, _ in filtered['skipped']))

    def test_omarchy_requires_matching_environment(self):
        template = load('templates/omarchy.json')
        with self.assertRaisesRegex(ValueError, 'requires Omarchy'):
            resolve(template, 'linux', load('profiles/windows.example.json') | {'os': 'linux'})

    def test_physical_id_survives_l1_reassignment(self):
        template = load('templates/vscode.json')
        source = load('examples/VirtualDefy.json')
        keys = source['virtual']['keymap.custom']['data'].split()
        keys[36] = str(4 + ord('Q') - ord('A'))
        source['virtual']['keymap.custom']['data'] = ' '.join(keys)
        result = resolve(template, 'macos', source=source)
        file_search = next(row for row in result['bindings'] if row['id'] == 'search_files')
        self.assertEqual(file_search['position_index'], 36)
        self.assertEqual(file_search['current_l1_label'], 'Q')
        self.assertTrue(any('search_files' in warning for warning in result['warnings']))

    def test_tmux_prefix_sequence(self):
        source = load('examples/VirtualDefy.json')
        tmux = resolve(load('templates/tmux.json'), 'linux', source=source)
        self.assertEqual(next(row['shortcut'] for row in tmux['bindings'] if row['id'] == 'split_right'), ['Ctrl+B', 'Shift+5'])

    def test_blender_view_uses_numpad_codes(self):
        result = resolve(load('templates/blender-view.json'), 'windows',
                         source=load('examples/VirtualDefy.json'))
        self.assertEqual(next(row['shortcut'] for row in result['bindings'] if row['id'] == 'front'), 'Numpad1')
        self.assertFalse(result['warnings'])


if __name__ == '__main__':
    unittest.main()
