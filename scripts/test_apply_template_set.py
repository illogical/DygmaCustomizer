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

    def test_mac_manifest_resolves_profile_and_reports_only_verified_blockers(self):
        manifest = read_json(ROOT / 'profiles/macbook-pro-m5-init.local.json')
        profile = read_json(ROOT / manifest['profile'])
        before = copy.deepcopy(self.source)
        output, reports, blockers = compose(
            self.source, self.source, manifest, profile,
            lambda path: read_json(ROOT / path))
        self.assertIsNone(output)
        self.assertEqual(self.source, before)
        self.assertEqual({report['target_layer'] for report in reports}, {1, 4, 5, 6})
        self.assertFalse(any(report['skipped'] for report in reports))
        self.assertTrue(any('Bazecor-verified' in issue for issue in blockers))
        self.assertTrue(any('verified LED mapping' in issue for issue in blockers))
        self.assertFalse(any('color category' in issue for issue in blockers))
        self.assertFalse(any('open_finder' in issue for issue in blockers))

    def test_deferred_key_is_red_and_other_layers_compose(self):
        pending = copy.deepcopy(self.template)
        pending['id'] = 'pending'
        pending['bindings'][0]['bazecor_action'] = {
            'type': 'superkey', 'gestures': {'tap': {'type': 'move-to-layer', 'target': 'secondary'}}}
        pending['bindings'][0].pop('shortcuts')
        manifest = {'schema_version': 1, 'id': 'test', 'deferred_red_slot': 11,
                    'layer_targets': {'secondary': 5},
                    'verified_leds': {}, 'layers': [
                        {'layer': 4, 'template': 'pending.json', 'color_slots': {'5': 'app'}},
                        {'layer': 5, 'template': 'ready.json', 'color_slots': {'5': 'app'}}]}
        source_before = copy.deepcopy(self.source)
        output, reports, blockers = compose(
            self.source, self.source, manifest, self.profile,
            lambda path: pending if path == 'pending.json' else self.template,
            policy='override', defer_unsupported=True)
        self.assertFalse(blockers)
        self.assertTrue(reports[0]['rows'][0]['deferred'])
        before = model(self.source)[1]
        after = model(output)[1]
        self.assertEqual(after['keymap.custom'][3 * 80 + 34], 65535)
        self.assertEqual(after['keymap.custom'][4 * 80 + 34], 4118)
        led = 16
        self.assertEqual(after['colormap.map'][3 * 178 + led], 11)
        self.assertEqual(output['virtual']['palette'], self.source['virtual']['palette'])
        self.assertEqual(self.source, source_before)

    def test_deferred_key_without_verified_led_refuses_output(self):
        manifest = read_json(ROOT / 'profiles/macbook-pro-m5-init.local.json')
        profile = read_json(ROOT / manifest['profile'])
        output, _, blockers = compose(
            self.source, self.source, manifest, profile,
            lambda path: read_json(ROOT / path), policy='override',
            defer_unsupported=True)
        self.assertIsNone(output)
        self.assertTrue(any('deferred secondary_and_tertiary_layers has no verified LED mapping'
                            in item for item in blockers))

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

    def test_compose_multiple_partial_templates_on_one_layer(self):
        second = copy.deepcopy(self.template)
        second['id'] = 'navigation'
        second['bindings'][0].update({
            'id': 'focus', 'name': 'Focus next control', 'position_l1': 'F',
            'position_id': 'defy:left:r3:c5', 'shortcuts': {'macos': 'F'},
        })
        manifest = {'schema_version': 1, 'id': 'test', 'layers': [
            {'layer': 4, 'template': 'a.json', 'color_slots': {'5': 'app'}},
            {'layer': 4, 'template': 'b.json', 'color_slots': {'5': 'app'}},
        ]}
        templates = {'a.json': self.template, 'b.json': second}
        before = copy.deepcopy(self.source)
        output, reports, blockers = compose(
            self.source, self.source, manifest, self.profile,
            lambda path: templates[path], with_colors=False)
        self.assertFalse(blockers)
        self.assertEqual(len(reports), 2)
        original = model(before)[1]['keymap.custom']
        updated = model(output)[1]['keymap.custom']
        self.assertEqual(
            [i for i, (a, b) in enumerate(zip(original, updated)) if a != b],
            [3 * 80 + 34, 3 * 80 + 36],
        )

    def test_same_layer_overlap_blocks_strict_and_writes_nothing(self):
        second = copy.deepcopy(self.template)
        second['bindings'][0]['shortcuts']['macos'] = 'G'
        manifest = {'schema_version': 1, 'id': 'test', 'layers': [
            {'layer': 4, 'template': 'a.json'},
            {'layer': 4, 'template': 'b.json'},
        ]}
        output, _, blockers = compose(
            self.source, self.source, manifest, self.profile,
            lambda path: self.template if path == 'a.json' else second,
            with_colors=False)
        self.assertIsNone(output)
        self.assertTrue(any('occupied' in blocker for blocker in blockers))

    def test_same_layer_override_uses_manifest_order(self):
        first = copy.deepcopy(self.template)
        first['bindings'][0]['shortcuts']['macos'] = 'F'
        second = copy.deepcopy(self.template)
        second['bindings'][0]['shortcuts']['macos'] = 'G'
        manifest = {'schema_version': 1, 'id': 'test', 'layers': [
            {'layer': 4, 'template': 'first.json'},
            {'layer': 4, 'template': 'second.json'},
        ]}
        templates = {'first.json': first, 'second.json': second}
        output, _, blockers = compose(
            self.source, self.source, manifest, self.profile,
            lambda path: templates[path], with_colors=False, policy='override')
        self.assertFalse(blockers)
        self.assertEqual(model(output)[1]['keymap.custom'][3 * 80 + 34], 10)

    def test_replace_layer_resets_once_then_applies_every_partial_template(self):
        second = copy.deepcopy(self.template)
        second['id'] = 'navigation'
        second['bindings'][0].update({
            'id': 'focus', 'name': 'Focus next control', 'position_l1': 'F',
            'position_id': 'defy:left:r3:c5', 'shortcuts': {'macos': 'F'},
        })
        source = copy.deepcopy(self.source)
        arrays = model(source)[1]
        arrays['keymap.custom'][3 * 80 + 20] = 4
        source['virtual']['keymap.custom']['data'] = ' '.join(map(str, arrays['keymap.custom']))
        manifest = {'schema_version': 1, 'id': 'test', 'layers': [
            {'layer': 4, 'template': 'a.json'},
            {'layer': 4, 'template': 'b.json'},
        ]}
        templates = {'a.json': self.template, 'b.json': second}
        output, _, blockers = compose(
            source, self.source, manifest, self.profile,
            lambda path: templates[path], with_colors=False, policy='replace-layer')
        self.assertFalse(blockers)
        keys = model(output)[1]['keymap.custom']
        self.assertEqual(keys[3 * 80 + 20], 65535)
        self.assertEqual(keys[3 * 80 + 34], 4118)
        self.assertEqual(keys[3 * 80 + 36], 9)

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
