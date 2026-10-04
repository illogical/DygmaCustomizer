import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from defy import edit, led_map, model
from resolve_template import read_json
from test_copy_l1_numbers_to_l4 import sample_layout

ROOT = Path(__file__).resolve().parents[1]


class DefyCommandTest(unittest.TestCase):
    def test_saved_l8_colors_confirm_right_first_three_rows(self):
        source = read_json(ROOT / 'examples/VirtualDefy.json')
        fixture = read_json(ROOT / 'examples/VirtualDefy-L8-fixtures.json')
        mapping = led_map(source)
        colors = model(fixture)[1]['colormap.map'][7 * 178:8 * 178]
        self.assertEqual([(mapping[key], colors[mapping[key]]) for key in (27, 28, 30)],
                         [(44, 11), (45, 10), (47, 8)])
        self.assertEqual((mapping[47], colors[mapping[47]]), (55, 14))
        self.assertEqual([mapping[key] for key in (42, 43, 44, 45)], [50, 51, 52, 53])
        self.assertNotIn(58, mapping)  # Lower right rows need confirmation.

        altered = copy.deepcopy(source)
        altered['device']['keyboard']['right'][1][2] = 99
        self.assertNotIn(27, led_map(altered))

    def layout(self):
        doc = sample_layout()
        doc['device']['RGBWMode'] = True
        doc['device']['keyboard']['ledsLeft'] = list(range(7))
        doc['virtual']['palette'] = {'data': ' '.join(['0'] * 60 + ['1', '2', '3', '4'])}
        return doc

    def run_edit(self, doc, action, **options):
        edit(doc, SimpleNamespace(action=action, **options))

    def occupied_l2(self):
        doc = self.layout()
        keys = model(doc)[1]['keymap.custom']
        keys[81] = 99
        doc['virtual']['keymap.custom']['data'] = ' '.join(map(str, keys))
        return doc

    def assert_rejected_unchanged(self, doc, message, action, **options):
        original = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, message):
            self.run_edit(doc, action, **options)
        self.assertEqual(doc, original)

    def test_copy_selected_keys_and_colors(self):
        doc = self.layout()
        before = copy.deepcopy(doc)
        edit(doc, SimpleNamespace(action='copy-keys', source=1, target=4,
                                  positions=[1, 10], colors=True, replace=False))
        keys = model(doc)[1]['keymap.custom']
        colors = model(doc)[1]['colormap.map']
        self.assertEqual((keys[241], keys[250]), (30, 35))
        self.assertEqual((colors[211], colors[246]), (4, 4))
        self.assertEqual(doc['virtual']['palette'], before['virtual']['palette'])

    def test_copy_keys_without_colors_and_with_replace(self):
        doc = self.layout()
        keys = model(doc)[1]['keymap.custom']
        keys[241] = 99
        doc['virtual']['keymap.custom']['data'] = ' '.join(map(str, keys))
        before_colors = doc['virtual']['colormap.map']['data']
        self.assert_rejected_unchanged(doc, 'not transparent', 'copy-keys',
                                       source=1, target=4, positions=[1], colors=False, replace=False)
        self.run_edit(doc, 'copy-keys', source=1, target=4,
                      positions=[1], colors=False, replace=True)
        self.assertEqual(model(doc)[1]['keymap.custom'][241], 30)
        self.assertEqual(doc['virtual']['colormap.map']['data'], before_colors)

    def test_copy_keys_rejects_invalid_positions_and_unmapped_colors(self):
        for positions, message in (([], 'unique'), ([1, 1], 'unique'),
                                   ([-1], 'unique'), ([80], 'unique')):
            with self.subTest(positions=positions):
                self.assert_rejected_unchanged(self.layout(), message, 'copy-keys',
                                               source=1, target=4, positions=positions,
                                               colors=False, replace=False)
        self.assert_rejected_unchanged(self.layout(), 'verified LED', 'copy-keys',
                                       source=1, target=4, positions=[70], colors=True,
                                       replace=False)

    def test_copy_layer_copies_all_keys_and_leds(self):
        doc = self.layout()
        before = copy.deepcopy(doc)
        self.run_edit(doc, 'copy-layer', source=1, target=4, replace=False)
        arrays = model(doc)[1]
        original = model(before)[1]
        self.assertEqual(arrays['keymap.custom'][240:320], original['keymap.custom'][:80])
        self.assertEqual(arrays['colormap.map'][210:280], original['colormap.map'][:70])
        self.assertEqual(arrays['keymap.custom'][:240], original['keymap.custom'][:240])
        self.assertEqual(doc['virtual']['palette'], before['virtual']['palette'])

    def test_copy_layer_requires_distinct_unoccupied_destination(self):
        self.assert_rejected_unchanged(self.layout(), 'must differ', 'copy-layer',
                                       source=1, target=1, replace=False)
        self.assert_rejected_unchanged(self.occupied_l2(), 'assigned keys', 'copy-layer',
                                       source=1, target=2, replace=False)
        self.assert_rejected_unchanged(self.layout(), 'Layer must', 'copy-layer',
                                       source=0, target=4, replace=False)

    def test_copy_layer_replace_allows_occupied_destination(self):
        doc = self.occupied_l2()
        self.run_edit(doc, 'copy-layer', source=1, target=2, replace=True)
        arrays = model(doc)[1]
        self.assertEqual(arrays['keymap.custom'][80:160], arrays['keymap.custom'][:80])
        self.assertEqual(arrays['colormap.map'][70:140], arrays['colormap.map'][:70])

    def test_move_layer_copies_then_clears_source(self):
        doc = self.layout()
        original = model(doc)[1]
        source_keys = original['keymap.custom'][:80]
        source_colors = original['colormap.map'][:70]
        self.run_edit(doc, 'move-layer', source=1, target=4, replace=False, clear_slot=15)
        arrays = model(doc)[1]
        self.assertEqual(arrays['keymap.custom'][240:320], source_keys)
        self.assertEqual(arrays['colormap.map'][210:280], source_colors)
        self.assertEqual(arrays['keymap.custom'][:80], [65535] * 80)
        self.assertEqual(arrays['colormap.map'][:70], [15] * 70)

    def test_move_layer_rejects_bad_clear_slot_and_occupied_destination(self):
        self.assert_rejected_unchanged(self.layout(), 'Clear slot', 'move-layer',
                                       source=1, target=4, replace=False, clear_slot=16)
        self.assert_rejected_unchanged(self.occupied_l2(), 'assigned keys', 'move-layer',
                                       source=1, target=2, replace=False, clear_slot=15)

    def test_set_color_by_position_and_led(self):
        doc = self.layout()
        original = copy.deepcopy(doc)
        self.run_edit(doc, 'set-color', target=4, position=1, led=None, slot=5)
        self.run_edit(doc, 'set-color', target=4, position=None, led=69, slot=6)
        colors = model(doc)[1]['colormap.map']
        before = model(original)[1]['colormap.map']
        self.assertEqual([i for i, pair in enumerate(zip(before, colors)) if pair[0] != pair[1]],
                         [211, 279])
        self.assertEqual((colors[211], colors[279]), (5, 6))
        self.assertEqual(doc['virtual']['keymap.custom'], original['virtual']['keymap.custom'])

    def test_set_color_rejects_missing_or_duplicate_position_and_bad_bounds(self):
        for position, led, slot, message in ((None, None, 4, 'exactly one'),
                                             (1, 1, 4, 'exactly one'),
                                             (None, 70, 4, 'LED out'),
                                             (None, -1, 4, 'LED out'),
                                             (1, None, 16, 'Palette slot')):
            with self.subTest(position=position, led=led, slot=slot):
                self.assert_rejected_unchanged(self.layout(), message, 'set-color',
                                               target=4, position=position, led=led, slot=slot)

    def test_rejects_ambiguous_right_led_without_mutation(self):
        doc = self.layout()
        original = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, 'verified LED'):
            edit(doc, SimpleNamespace(action='set-color', target=4, position=70,
                                      led=None, slot=4))
        self.assertEqual(doc, original)

    def test_used_palette_slot_requires_replace(self):
        doc = self.layout()
        original = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, 'in use'):
            edit(doc, SimpleNamespace(action='set-palette', slot=4,
                                      channels=[1, 2, 3, 4], replace=False))
        self.assertEqual(doc, original)

    def test_set_palette_unused_slot_and_replace_used_slot(self):
        doc = self.layout()
        before = copy.deepcopy(doc)
        self.run_edit(doc, 'set-palette', slot=14, channels=[9, 8, 7, 6], replace=False)
        self.run_edit(doc, 'set-palette', slot=4, channels=[5, 6, 7, 8], replace=True)
        palette = model(doc)[1]['palette']
        self.assertEqual(palette[56:60], [9, 8, 7, 6])
        self.assertEqual(palette[16:20], [5, 6, 7, 8])
        self.assertEqual(doc['virtual']['keymap.custom'], before['virtual']['keymap.custom'])
        self.assertEqual(doc['virtual']['colormap.map'], before['virtual']['colormap.map'])

    def test_set_palette_rejects_invalid_channels_and_slot(self):
        for slot, channels in ((16, [1, 2, 3, 4]), (14, [1, 2, 3]),
                               (14, [1, 2, 3, 256]), (14, [-1, 2, 3, 4])):
            with self.subTest(slot=slot, channels=channels):
                self.assert_rejected_unchanged(self.layout(), 'Expected valid slot',
                                               'set-palette', slot=slot,
                                               channels=channels, replace=False)

    def test_model_rejects_invalid_virtual_layout(self):
        for mutate, message in (
            (lambda d: d['device']['info'].update(product='Other'), 'Defy virtual'),
            (lambda d: d['virtual']['keymap.custom'].update(data='1 2'), 'keymap length'),
            (lambda d: d['virtual']['colormap.map'].update(data='1'), 'colormap length'),
            (lambda d: d['virtual']['palette'].update(data='1 2 3'), 'palette length'),
            (lambda d: d['virtual']['colormap.map'].update(data='16 ' + d['virtual']['colormap.map']['data']), 'colormap length'),
        ):
            doc = self.layout()
            mutate(doc)
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                model(doc)

    def test_cli_inspect_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.json'
            source.write_text(json.dumps(self.layout()))
            inspect = subprocess.run([sys.executable, str(ROOT / 'scripts/defy.py'),
                                      'inspect', str(source)], capture_output=True, text=True)
            self.assertEqual(inspect.returncode, 0, inspect.stderr)
            self.assertIn('L1:', inspect.stdout)
            before = source.read_bytes()
            command = [sys.executable, str(ROOT / 'scripts/defy.py'), 'copy-layer',
                       str(source), str(source), '--source', '1', '--target', '4']
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn('Input and output must differ', rejected.stderr)
            self.assertEqual(source.read_bytes(), before)

    def test_cli_creates_distinct_output_with_only_requested_change(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.json'
            output = Path(folder) / 'output.json'
            source.write_text(json.dumps(self.layout()))
            command = [sys.executable, str(ROOT / 'scripts/defy.py'), 'set-color',
                       str(source), str(output), '--target', '4', '--led', '69', '--slot', '6']
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(model(json.loads(output.read_text()))[1]['colormap.map'][279], 6)
            self.assertEqual(json.loads(source.read_text()), self.layout())
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 1)
            self.assertIn('File exists', rejected.stderr)

    def test_cli_argument_variants_change_only_expected_commands(self):
        variants = (
            ('copy-keys', ['--source', '1', '--target', '4', '--positions', '1', '10', '--colors'],
             {'keymap.custom', 'colormap.map'}, self.layout),
            ('copy-layer', ['--source', '1', '--target', '2', '--replace'],
             {'keymap.custom', 'colormap.map'}, self.occupied_l2),
            ('move-layer', ['--source', '1', '--target', '4', '--clear-slot', '14'],
             {'keymap.custom', 'colormap.map'}, self.layout),
            ('set-color', ['--target', '4', '--position', '1', '--slot', '5'],
             {'colormap.map'}, self.layout),
            ('set-palette', ['--slot', '14', '--channels', '9', '8', '7', '6'],
             {'palette'}, self.layout),
            ('set-palette', ['--slot', '4', '--channels', '9', '8', '7', '6', '--replace'],
             {'palette'}, self.layout),
        )
        for action, arguments, expected, source_doc in variants:
            with self.subTest(action=action, arguments=arguments), tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / 'source.json'
                output = Path(folder) / 'output.json'
                source.write_text(json.dumps(source_doc()))
                before = json.loads(source.read_text())
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/defy.py'),
                                         action, str(source), str(output), *arguments],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                after = json.loads(output.read_text())
                changed = {name for name in ('keymap.custom', 'colormap.map', 'palette')
                           if before['virtual'][name]['data'] != after['virtual'][name]['data']}
                self.assertEqual(changed, expected)
                probe = copy.deepcopy(before)
                for name in changed:
                    probe['virtual'][name]['data'] = after['virtual'][name]['data']
                self.assertEqual(probe, after)
                self.assertEqual(json.loads(source.read_text()), before)


if __name__ == '__main__':
    unittest.main()
