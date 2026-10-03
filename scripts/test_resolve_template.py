import json
import unittest
from pathlib import Path

from resolve_template import resolve


ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


class ResolveTemplateTest(unittest.TestCase):
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
        self.assertEqual(len(result['bindings']), 2)
        self.assertEqual(next(r['shortcut'] for r in result['bindings'] if r['id'] == 'vivaldi'),
                         'Ctrl+Alt+Cmd+Shift+V')
        profile['available_apps'].remove('vivaldi')
        filtered = resolve(template, 'macos', profile)
        self.assertEqual(len(filtered['bindings']), 1)
        self.assertTrue(any(action == 'vivaldi' for action, _ in filtered['skipped']))

    def test_omarchy_requires_matching_environment(self):
        template = load('templates/omarchy.json')
        with self.assertRaisesRegex(ValueError, 'requires Omarchy'):
            resolve(template, 'linux', load('profiles/windows.example.json') | {'os': 'linux'})

    def test_ambiguous_l1_reference_is_rejected(self):
        template = load('templates/vscode.json')
        source = load('examples/VirtualDefy.json')
        keys = source['virtual']['keymap.custom']['data'].split()
        keys[0] = str(4 + ord('F') - ord('A'))
        source['virtual']['keymap.custom']['data'] = ' '.join(keys)
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            resolve(template, 'macos', source=source)


if __name__ == '__main__':
    unittest.main()
