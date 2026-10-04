import copy
import unittest

from apply_template import apply, plan
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
        template = read_json(ROOT / 'templates/macos-navigation.json')
        report = plan(self.source, template, self.profile, 4)
        self.assertTrue(any(row.get('unsupported') for row in report['rows']))
        self.assertTrue(any(action == 'open_finder' for action, _ in report['skipped']))
        with self.assertRaisesRegex(ValueError, 'Skipped actions'):
            apply(self.source, report)
        with self.assertRaisesRegex(ValueError, 'Unsupported actions'):
            apply(self.source, report, allow_skipped=True)

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
