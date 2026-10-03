import copy
import unittest
from types import SimpleNamespace

from defy import edit, model
from test_copy_l1_numbers_to_l4 import sample_layout


class DefyCommandTest(unittest.TestCase):
    def layout(self):
        doc = sample_layout()
        doc['device']['RGBWMode'] = True
        doc['device']['keyboard']['ledsLeft'] = list(range(7))
        doc['virtual']['palette'] = {'data': ' '.join(['0'] * 60 + ['1', '2', '3', '4'])}
        return doc

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


if __name__ == '__main__':
    unittest.main()
