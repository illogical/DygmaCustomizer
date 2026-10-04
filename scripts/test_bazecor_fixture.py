"""Check the preserved Bazecor L8 example against its untouched virtual source."""

import unittest
from pathlib import Path

from resolve_template import read_json


ROOT = Path(__file__).resolve().parents[1]


class BazecorFixtureTest(unittest.TestCase):
    def test_l8_example_changes_only_the_recorded_keys_and_led_slots(self):
        source = read_json(ROOT / 'examples/VirtualDefy.json')
        fixture = read_json(ROOT / 'examples/VirtualDefy-L8-fixtures.json')
        self.assertEqual(source.keys(), fixture.keys())
        self.assertEqual({k: v for k, v in source.items() if k != 'virtual'},
                         {k: v for k, v in fixture.items() if k != 'virtual'})
        self.assertEqual(source['virtual'].keys(), fixture['virtual'].keys())

        expected_keys = dict(zip(range(594, 599),
                                 [49164, 17498, 17496, 53980, 6916]))
        expected_leds = dict(zip(range(1246, 1261), range(15)))
        expected_leds.update(zip(range(1281, 1288), [6, 5, 4, 3, 2, 1, 0]))
        expected_leds.update(zip(range(1288, 1295), [13, 12, 11, 10, 9, 8, 7]))
        expected_leds[1301] = 14
        expected = {'keymap.custom': expected_keys, 'colormap.map': expected_leds}

        for command, old_entry in source['virtual'].items():
            new_entry = fixture['virtual'][command]
            self.assertEqual({k: v for k, v in old_entry.items() if k != 'data'},
                             {k: v for k, v in new_entry.items() if k != 'data'})
            old_values = old_entry['data'].split()
            new_values = new_entry['data'].split()
            self.assertEqual(len(old_values), len(new_values), command)
            changes = {index: int(new)
                       for index, (old, new) in enumerate(zip(old_values, new_values))
                       if old != new}
            self.assertEqual(changes, expected.get(command, {}), command)
