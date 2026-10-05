import copy
import unittest

from apply_template import apply, encode, plan
from defy import model
from resolve_template import read_json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ApplyTemplateTest(unittest.TestCase):
    def setUp(self):
        self.source = read_json(ROOT / 'examples/VirtualDefy.json')
        self.profile = {'schema_version': 1, 'id': 'test-mac', 'os': 'macos',
                        'available_apps': [], 'shortcut_overrides': {}}
        self.template = {'schema_version': 1, 'id': 'single', 'name': 'Single key',
                         'platforms': ['macos'], 'bindings': [{
                             'id': 'save', 'name': 'Save', 'position_l1': 'S',
                             'position_id': 'defy:left:r3:c3', 'color_category': 'navigation',
                             'shortcuts': {'macos': 'Cmd+S'}}]}

    def test_partial_apply_preserves_every_other_key_and_command(self):
        before = copy.deepcopy(self.source)
        report = plan(self.source, self.template, self.profile, 4, with_keys=True, with_colors=False)
        self.assertEqual(report['rows'][0]['after_keycode'], 4118)
        self.assertFalse(report['rows'][0]['collision'])
        apply(self.source, report)
        original_keys = model(before)[1]['keymap.custom']
        new_keys = model(self.source)[1]['keymap.custom']
        self.assertEqual([i for i, (a, b) in enumerate(zip(original_keys, new_keys)) if a != b], [274])
        self.assertEqual(new_keys[274], 4118)
        self.assertEqual(self.source['virtual']['palette'], before['virtual']['palette'])
        self.assertEqual(self.source['virtual']['colormap.map'], before['virtual']['colormap.map'])

    def test_collision_requires_override(self):
        report = plan(self.source, self.template, self.profile, 1, with_keys=True, with_colors=False)
        self.assertTrue(report['rows'][0]['collision'])
        with self.assertRaisesRegex(ValueError, 'Occupied positions'):
            apply(self.source, report)
        apply(self.source, report, override=True)

    def test_unverified_chord_is_reported_and_refused(self):
        template = copy.deepcopy(self.template)
        template['bindings'][0]['shortcuts']['macos'] = 'AltGr+P'
        report = plan(self.source, template, self.profile, 4)
        self.assertTrue(any(row.get('unsupported') for row in report['rows']))
        self.assertFalse(report['skipped'])
        with self.assertRaisesRegex(ValueError, 'Unsupported actions'):
            apply(self.source, report)

    def test_f5_uses_existing_plain_code_from_source(self):
        template = read_json(ROOT / 'templates/vscode.json')
        profile = self.profile | {'available_apps': ['vscode']}
        report = plan(self.source, template, profile, 5,
                      with_keys=True, with_colors=False)
        debug = next(row for row in report['rows'] if row['id'] == 'debug')
        self.assertEqual(model(self.source)[1]['keymap.custom'][2 * 80 + 5], 62)
        self.assertEqual(debug['after_keycode'], 62)
        self.assertNotIn('unsupported', debug)

    def test_fixture_verified_one_shot_l4_and_device_code_resolve(self):
        template = {
            'schema_version': 1, 'id': 'actions', 'name': 'Bazecor actions',
            'platforms': ['macos'], 'bindings': [{
                'id': 'launcher', 'name': 'Open app launcher',
                'position_l1': 'Super 1', 'position_id': 'defy:left:r5:c1',
                'color_category': 'activation',
                'bazecor_action': {'type': 'one-shot-layer', 'target': 'primary',
                                   'target_layer': 4},
            }, {
                'id': 'battery', 'name': 'Battery level',
                'position_l1': 'Right Alt', 'position_id': 'defy:right:r5:c7',
                'color_category': 'system',
                'bazecor_action': {'type': 'device-command', 'command': 'battery-level'},
            }],
        }
        profile = self.profile | {'layer_targets': {'primary': 4}}
        report = plan(self.source, template, profile, 1,
                      with_keys=True, with_colors=False)
        self.assertEqual(report['rows'][0]['after_keycode'], 49164)
        self.assertEqual(report['rows'][1]['after_keycode'], 54108)
        apply(self.source, report, override=True)
        self.assertEqual(model(self.source)[1]['keymap.custom'][64], 49164)

    def test_other_one_shot_target_remains_unsupported(self):
        template = read_json(ROOT / 'templates/layer-navigation.json')
        profile = self.profile | {'layer_targets': {'primary': 5, 'secondary': 5, 'tertiary': 6}}
        report = plan(self.source, template, profile, 1, with_colors=False)
        self.assertIn('verified encoding fixture', report['rows'][0]['unsupported'])

    def test_saved_move_to_layer_family_includes_l1_return(self):
        template = copy.deepcopy(self.template)
        template['bindings'][0].pop('shortcuts')
        template['bindings'][0]['bazecor_action'] = {
            'type': 'move-to-layer', 'target': 'destination'}
        for destination, code in ((1, 17492), (5, 17496), (7, 17498)):
            with self.subTest(destination=destination):
                profile = self.profile | {'layer_targets': {'destination': destination}}
                report = plan(self.source, template, profile, 4, with_colors=False)
                self.assertEqual(report['rows'][0]['after_keycode'], code)
                self.assertNotIn('unsupported', report['rows'][0])

    def test_move_fixture_does_not_silently_encode_layer_lock(self):
        template = copy.deepcopy(self.template)
        template['bindings'][0].pop('shortcuts')
        template['bindings'][0]['bazecor_action'] = {
            'type': 'layer-lock', 'target': 'destination'}
        profile = self.profile | {'layer_targets': {'destination': 7}}
        report = plan(self.source, template, profile, 4, with_colors=False)
        self.assertIn('verified encoding fixture', report['rows'][0]['unsupported'])

    def test_hyper_fixture_generalizes_to_raycast_letters_and_digits(self):
        template = copy.deepcopy(self.template)
        template['bindings'][0]['shortcuts']['macos'] = 'Hyper+A'
        profile = self.profile | {'hyper_modifiers': ['Ctrl', 'Alt', 'Cmd', 'Shift']}
        report = plan(self.source, template, profile, 4, with_colors=False)
        self.assertEqual(report['rows'][0]['after_keycode'], 6916)
        template['bindings'][0]['shortcuts']['macos'] = 'Hyper+B'
        report = plan(self.source, template, profile, 4, with_colors=False)
        self.assertEqual(report['rows'][0]['after_keycode'], 6917)
        template['bindings'][0]['shortcuts']['macos'] = 'Hyper+1'
        report = plan(self.source, template, profile, 4, with_colors=False)
        self.assertEqual(report['rows'][0]['after_keycode'], 6942)

    def test_modifier_tables_encode_mac_manifest_chords(self):
        expected = {
            'Cmd+S': 4118, 'Cmd+P': 4115, 'Cmd+Comma': 4150,
            'Ctrl+Minus': 301, 'Ctrl+Shift+Minus': 2349,
            'Shift+F12': 2117, 'Shift+Cmd+B': 6149,
            'Ctrl+Cmd+Left': 4432, 'Ctrl+Cmd+Right': 4431,
            'Shift+Cmd+Tab': 6187, 'Cmd+Tab': 4139,
            'Shift+Cmd+Grave': 6197, 'Cmd+Grave': 4149,
            'Shift+Ctrl+C': 2310,
        }
        for chord, code in expected.items():
            with self.subTest(chord=chord):
                self.assertEqual(encode(chord), code)
        with self.assertRaisesRegex(ValueError, 'verified keycode'):
            encode('Ctrl+Ctrl+A')

    def test_device_controls_copy_verified_l1_codes_even_after_l1_is_cleared(self):
        template = read_json(ROOT / 'templates/device-controls.json')
        source = copy.deepcopy(self.source)
        doc = copy.deepcopy(source)
        keys = model(doc)[1]['keymap.custom']
        keys[72] = keys[73] = 65535
        doc['virtual']['keymap.custom']['data'] = ' '.join(map(str, keys))
        report = plan(doc, template, self.profile, 4, with_colors=False, source=source)
        self.assertEqual([row['after_keycode'] for row in report['rows']], [54108, 54109])
        apply(doc, report)
        self.assertEqual(model(doc)[1]['keymap.custom'][3 * 80 + 78:3 * 80 + 80],
                         [54108, 54109])
        self.assertEqual(doc['virtual']['colormap.map'], source['virtual']['colormap.map'])

    def test_device_copy_rejects_a_changed_source_code(self):
        template = read_json(ROOT / 'templates/device-controls.json')
        source = copy.deepcopy(self.source)
        keys = model(source)[1]['keymap.custom']
        keys[73] = 65535
        source['virtual']['keymap.custom']['data'] = ' '.join(map(str, keys))
        report = plan(self.source, template, self.profile, 4, with_colors=False,
                      source=source)
        self.assertIn('matching verified L1 assignment', report['rows'][0]['unsupported'])
        self.assertEqual(report['rows'][1]['after_keycode'], 54109)

    def test_device_copy_does_not_use_old_destination_codes(self):
        template = read_json(ROOT / 'templates/device-controls.json')
        source = copy.deepcopy(self.source)
        keys = model(source)[1]['keymap.custom']
        keys[72] = keys[73] = 65535
        # These destination positions still contain the unrelated original codes.
        self.assertEqual(keys[78:80], [230, 53852])
        source['virtual']['keymap.custom']['data'] = ' '.join(map(str, keys))
        report = plan(self.source, template, self.profile, 4, with_colors=False,
                      source=source)
        self.assertTrue(all('matching verified L1 assignment' in row['unsupported']
                            for row in report['rows']))

    def test_media_template_copies_six_l3_codes_and_colors_only_on_l6(self):
        template = read_json(ROOT / 'templates/multimedia-controls.json')
        before = copy.deepcopy(self.source)
        report = plan(self.source, template, self.profile, 6)
        self.assertFalse(report['skipped'])
        self.assertTrue(all(not row.get('unsupported') and not row['collision'] for row in report['rows']))
        self.assertEqual([(row['position_index'], row['after_keycode']) for row in report['rows']],
                         [(19, 22710), (20, 22733), (21, 22709),
                          (35, 23786), (36, 19682), (37, 23785)])
        apply(self.source, report)
        old, new = model(before)[1], model(self.source)[1]
        key_changes = [i for i, (a, b) in enumerate(zip(old['keymap.custom'], new['keymap.custom'])) if a != b]
        led_changes = [i for i, (a, b) in enumerate(zip(old['colormap.map'], new['colormap.map'])) if a != b]
        self.assertEqual(key_changes, [400 + i for i in (19, 20, 21, 35, 36, 37)])
        self.assertEqual(led_changes, [5 * 178 + i for i in (10, 11, 12, 17, 18, 19)])
        self.assertEqual({new['colormap.map'][i] for i in led_changes}, {7})
        self.assertEqual(self.source['virtual']['palette'], before['virtual']['palette'])

    def test_media_copy_blocks_changed_l3_source(self):
        template = read_json(ROOT / 'templates/multimedia-controls.json')
        source = copy.deepcopy(self.source)
        keys = model(source)[1]['keymap.custom']
        keys[2 * 80 + 36] = 65535
        source['virtual']['keymap.custom']['data'] = ' '.join(map(str, keys))
        original = copy.deepcopy(self.source)
        report = plan(self.source, template, self.profile, 6, source=source)
        self.assertIn('matching verified L3 assignment', report['rows'][1]['unsupported'])
        with self.assertRaisesRegex(ValueError, 'Unsupported actions'):
            apply(self.source, report)
        self.assertEqual(self.source, original)

    def test_clear_device_controls_targets_actual_source_positions(self):
        template = read_json(ROOT / 'templates/device-controls-clear.json')
        original = copy.deepcopy(self.source)
        report = plan(self.source, template, self.profile, 1, with_colors=False)
        self.assertEqual([row['position_index'] for row in report['rows']], [73, 72])
        apply(self.source, report, override=True)
        before = model(original)[1]['keymap.custom']
        after = model(self.source)[1]['keymap.custom']
        self.assertEqual([i for i, (a, b) in enumerate(zip(before, after)) if a != b],
                         [72, 73])
        self.assertEqual(after[72:74], [65535, 65535])
        self.assertEqual(after[78:80], [230, 53852])

    def test_transparent_thumb_action_uses_known_transparent_keycode(self):
        template = {
            'schema_version': 1, 'id': 'transparent', 'name': 'Transparent trigger',
            'platforms': ['macos'], 'bindings': [{
                'id': 'one_shot_return', 'name': 'Transparent trigger position',
                'position_l1': 'Super 1', 'position_id': 'defy:left:r5:c1',
                'color_category': 'activation',
                'bazecor_action': {'type': 'transparent'},
            }],
        }
        arrays = model(self.source)[1]
        arrays['keymap.custom'][3 * 80 + 64] = 10
        self.source['virtual']['keymap.custom']['data'] = ' '.join(map(str, arrays['keymap.custom']))
        report = plan(self.source, template, self.profile, 4,
                      with_keys=True, with_colors=False)
        self.assertEqual(report['rows'][0]['after_keycode'], 65535)
        apply(self.source, report, override=True)
        self.assertEqual(model(self.source)[1]['keymap.custom'][3 * 80 + 64], 65535)

    def test_template_color_slot_maps_purpose_without_rgb_value(self):
        self.template['color_slots'] = {'5': 'navigation'}
        report = plan(self.source, self.template, self.profile, 4, with_colors=True)
        self.assertEqual(report['rows'][0]['after_color_slot'], 5)
        apply(self.source, report)

    def test_color_purpose_requires_one_valid_template_slot(self):
        self.template['color_slots'] = {'5': 'navigation', '6': 'navigation'}
        report = plan(self.source, self.template, self.profile, 4, with_colors=True)
        self.assertIn('exactly one', report['rows'][0]['unsupported'])

    def test_keys_only_preserves_colors(self):
        self.template['color_slots'] = {'5': 'navigation'}
        before = copy.deepcopy(self.source)
        report = plan(self.source, self.template, self.profile, 4, with_keys=True, with_colors=False)
        apply(self.source, report)
        self.assertEqual(model(self.source)[1]['colormap.map'], model(before)[1]['colormap.map'])
        self.assertNotEqual(model(self.source)[1]['keymap.custom'], model(before)[1]['keymap.custom'])

    def test_colors_only_does_not_require_a_shortcut_or_change_keys(self):
        self.template['bindings'][0]['shortcuts'] = {}
        self.template['color_slots'] = {'5': 'navigation'}
        before = copy.deepcopy(self.source)
        report = plan(self.source, self.template, self.profile, 4, with_keys=False, with_colors=True)
        self.assertEqual(len(report['rows']), 1)
        self.assertNotIn('before_keycode', report['rows'][0])
        apply(self.source, report)
        self.assertEqual(model(self.source)[1]['keymap.custom'], model(before)[1]['keymap.custom'])
        self.assertNotEqual(model(self.source)[1]['colormap.map'], model(before)[1]['colormap.map'])

    def test_fill_empty_skips_occupied_key_and_color(self):
        self.template['color_slots'] = {'5': 'navigation'}
        before = copy.deepcopy(self.source)
        report = plan(self.source, self.template, self.profile, 1, fill_empty=True)
        self.assertTrue(report['rows'][0]['skipped_occupied'])
        apply(self.source, report)
        self.assertEqual(self.source, before)

    def test_replace_layer_clears_unlisted_keys_and_restores_baseline_lighting(self):
        from apply_template import reset_layer
        baseline = copy.deepcopy(self.source)
        arrays = model(self.source)[1]
        arrays['keymap.custom'][3*80+10] = 4
        arrays['colormap.map'][3*178+10] = 5
        for name in ('keymap.custom', 'colormap.map'):
            self.source['virtual'][name]['data'] = ' '.join(map(str, arrays[name]))
        reset_layer(self.source, baseline, 4, True, True)
        report = plan(self.source, self.template, self.profile, 4, with_colors=False)
        apply(self.source, report)
        after = model(self.source)[1]
        self.assertEqual(after['keymap.custom'][3*80+10], 65535)
        self.assertEqual(after['colormap.map'][3*178+10], 15)
        self.assertEqual(after['keymap.custom'][3*80+34], 4118)


if __name__ == '__main__':
    unittest.main()
