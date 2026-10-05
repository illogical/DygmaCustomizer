import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from render_layer_preview import (CELL_W, LEFT_X, RIGHT_X, WIDTH, collect,
                                  collect_current, key_origin, render, title_lines)


ROOT = Path(__file__).resolve().parents[1]


class RenderLayerPreviewTest(unittest.TestCase):
    def test_renders_physical_positions_and_flags_unverified_led(self):
        source = json.loads((ROOT / 'examples/VirtualDefy.json').read_text())
        unchanged = json.dumps(source, sort_keys=True)
        manifest = {'id': 'test', 'layers': [{'layer': 4, 'template': 'sample'}]}
        profile = {'id': 'mac-test', 'schema_version': 1, 'os': 'macos',
                   'available_apps': [], 'hyper_modifiers': ['Ctrl', 'Alt', 'Cmd', 'Shift']}
        template = {'schema_version': 1, 'id': 'sample', 'name': 'Sample',
                    'platforms': ['macos'], 'color_slots': {'1': 'app'},
                    'bindings': [
                        {'id': 'left', 'name': 'Launch Example', 'position_l1': 'A',
                         'position_id': 'defy:left:r3:c2', 'color_category': 'app',
                         'shortcuts': {'macos': 'Hyper+A'}},
                        {'id': 'right', 'name': 'Launch Other', 'position_l1': 'N',
                         'position_id': 'defy:right:r4:c2', 'color_category': 'app',
                         'shortcuts': {'macos': 'Hyper+N'}}]}
        svg = render(source, manifest, profile, 4, lambda _: template)
        ET.fromstring(svg)
        self.assertIn('defy:left:r3:c2: Launch Example', svg)
        self.assertIn('defy:right:r4:c2: Launch Other; LED position unverified', svg)
        self.assertIn('Hyper+A', svg)
        self.assertIn('stroke="#57d4bd"', svg)
        self.assertIn('stroke-dasharray="7 5"', svg)
        self.assertEqual(json.dumps(source, sort_keys=True), unchanged)

    def test_thumb_cluster_has_two_rows_in_screenshot_order(self):
        left_top = [key_origin('left', 5, column, 70) for column in range(1, 5)]
        left_bottom = [key_origin('left', 5, column, 70) for column in range(8, 4, -1)]
        right_top = [key_origin('right', 5, column, RIGHT_X) for column in range(5, 9)]
        right_bottom = [key_origin('right', 5, column, RIGHT_X) for column in range(4, 0, -1)]
        for row in (left_top, left_bottom, right_top, right_bottom):
            self.assertEqual(sorted(x for x, _ in row), [x for x, _ in row])
            self.assertEqual(len({y for _, y in row}), 1)
        self.assertGreater(left_bottom[0][1], left_top[0][1])
        self.assertGreater(right_bottom[0][1], right_top[0][1])

    def test_visual_studio_code_fits_two_title_lines(self):
        self.assertEqual(title_lines('Visual Studio Code'), ['Visual Studio', 'Code'])
        self.assertLessEqual(len(title_lines('A very long key title with many words')), 3)

    def test_shared_slot_color_and_conflicting_purpose_note(self):
        source = json.loads((ROOT / 'examples/VirtualDefy.json').read_text())
        manifest = {'id': 'pair', 'layers': [
            {'layer': 4, 'template': 'one', 'color_slots': {'1': 'app'}},
            {'layer': 4, 'template': 'two', 'color_slots': {'1': 'system'}}]}
        profile = {'id': 'test', 'schema_version': 1, 'os': 'macos'}
        def template(name, action, position):
            return {'schema_version': 1, 'id': name, 'name': name, 'platforms': ['macos'],
                    'bindings': [{'id': action, 'name': action, 'position_l1': position,
                                  'color_category': 'app' if name == 'one' else 'system',
                                  'shortcuts': {'macos': position}}]}
        templates = {'one': template('one', 'first', 'A'), 'two': template('two', 'second', 'B')}
        data = collect(source, manifest, profile, 4, lambda path: templates[path])
        self.assertEqual({item['color'] for item in data['all_items']}, {'#57d4bd'})
        self.assertIn('Slot 1 has conflicting purposes: app, system', data['notes'])

    def test_missing_slot_and_occupied_source_are_visible(self):
        source = json.loads((ROOT / 'examples/VirtualDefy.json').read_text())
        manifest = {'id': 'single', 'layers': [{'layer': 1, 'template': 'one'}]}
        profile = {'id': 'test', 'schema_version': 1, 'os': 'macos'}
        template = {'schema_version': 1, 'id': 'one', 'name': 'One', 'platforms': ['macos'],
                    'bindings': [{'id': 'action', 'name': 'New action', 'position_l1': 'A',
                                  'color_category': 'create', 'shortcuts': {'macos': 'B'}}]}
        svg = render(source, manifest, profile, 1, lambda _: template)
        self.assertIn('Palette slot unset or invalid', svg)
        self.assertIn('Occupied source key', svg)
        self.assertIn('create: slot unset', svg)

    def test_same_position_conflict_is_reported(self):
        source = json.loads((ROOT / 'examples/VirtualDefy.json').read_text())
        manifest = {'id': 'pair', 'layers': [{'layer': 4, 'template': name}
                                           for name in ('one', 'two')]}
        profile = {'id': 'test', 'schema_version': 1, 'os': 'macos'}
        def template(name):
            return {'schema_version': 1, 'id': name, 'name': name, 'platforms': ['macos'],
                    'bindings': [{'id': name, 'name': name, 'position_l1': 'A',
                                  'color_category': 'app', 'shortcuts': {'macos': 'A'}}]}
        svg = render(source, manifest, profile, 4, lambda name: template(name))
        self.assertIn('Template conflict: one / two', svg)

    def test_cli_accepts_template_and_manifest_and_refuses_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = ROOT / 'examples/VirtualDefy.json'
            profile = ROOT / 'profiles/macos.example.json'
            template = ROOT / 'templates/app-launcher.json'
            script = ROOT / 'scripts/render_layer_preview.py'
            single = folder / 'single.svg'
            common = [sys.executable, str(script), str(source), '--layer', '4']
            first = subprocess.run(common + ['--template', str(template), '--profile', str(profile),
                                             '--output', str(single)], capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            ET.parse(single)
            self.assertIn('Skipped:', single.read_text())
            report = single.with_suffix('.md')
            self.assertTrue(report.exists())
            self.assertIn('## Blockers and manual checks', report.read_text())
            self.assertIn('Skipped:', report.read_text())
            self.assertNotIn('Preview notes and blockers', single.read_text())
            again = subprocess.run(common + ['--template', str(template), '--profile', str(profile),
                                             '--output', str(single)], capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            manifest = ROOT / 'profiles/macos-init.example.json'
            composed = folder / 'composed.svg'
            second = subprocess.run(common[:3] + [str(manifest), '--layer', '4',
                                                '--output', str(composed)], capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            root = ET.parse(composed).getroot()
            namespace = {'s': 'http://www.w3.org/2000/svg'}
            bounds = [(float(rect.attrib['x']), float(rect.attrib['y']),
                       float(rect.attrib['width']), float(rect.attrib['height']))
                      for rect in root.findall("s:rect[@class='key']", namespace)]
            self.assertEqual(len(bounds), 71)
            self.assertGreater(CELL_W, 150)
            self.assertEqual(min(x for x, _, _, _ in bounds), LEFT_X)
            self.assertEqual(float(root.attrib['width']) - max(x + w for x, _, w, _ in bounds), LEFT_X)
            self.assertEqual(WIDTH, float(root.attrib['width']))
            self.assertTrue(all(0 <= x and 0 <= y and x + w <= float(root.attrib['width'])
                                and y + h <= float(root.attrib['height']) for x, y, w, h in bounds))

    def test_existing_report_prevents_svg_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            svg, report = folder / 'preview.svg', folder / 'preview.md'
            report.write_text('keep this report')
            command = [sys.executable, str(ROOT / 'scripts/render_layer_preview.py'),
                       str(ROOT / 'examples/VirtualDefy.json'), '--template',
                       str(ROOT / 'templates/app-launcher.json'), '--profile',
                       str(ROOT / 'profiles/macos.example.json'), '--layer', '4', '--output', str(svg)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(svg.exists())
            self.assertEqual(report.read_text(), 'keep this report')

    def test_current_mode_shows_only_assignments_present_in_json(self):
        source = json.loads((ROOT / 'profiles/macbook-pro-m5-L6-navigation.local.json').read_text())
        manifest = json.loads((ROOT / 'profiles/macbook-pro-m5-init.local.json').read_text())
        profile = json.loads((ROOT / 'profiles/macbook-pro-m5.local.json').read_text())
        load = lambda path: json.loads((ROOT / path).read_text())
        data = collect_current(source, manifest, profile, 6, load)
        self.assertEqual(len(data['items']), 7)
        self.assertEqual(len(data['missing']), 6)
        svg = render(source, manifest, profile, 6, load, prepared=data, current=True)
        ET.fromstring(svg)
        self.assertIn('Next desktop', svg)
        self.assertNotIn('defy:left:r2:c5: Play / pause', svg)
        self.assertIn('7 recognized assigned actions', svg)

    def test_current_cli_renders_actual_file_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            svg = Path(directory) / 'before.svg'
            command = [sys.executable, str(ROOT / 'scripts/render_layer_preview.py'),
                       str(ROOT / 'profiles/macbook-pro-m5-L6-navigation.local.json'),
                       str(ROOT / 'profiles/macbook-pro-m5-init.local.json'), '--current',
                       '--layer', '6', '--output', str(svg)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            ET.parse(svg)
            report = svg.with_suffix('.md').read_text()
            self.assertIn('Recognized assigned actions: 7', report)
            self.assertIn('Manifest actions absent or different: 6', report)


if __name__ == '__main__':
    unittest.main()
