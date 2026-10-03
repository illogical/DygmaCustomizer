import copy
import unittest

from copy_l1_numbers_to_l4 import copy_numbers


def sample_layout():
    keys = [65535] * (80 * 4)
    colors = [15] * (4 * 70)
    for digit, position in enumerate((1, 2, 3, 4, 5, 10, 11, 12, 13, 14)):
        keys[position] = 30 + digit
    for led in (1, 2, 3, 4, 5, 36, 37, 38, 39, 40):
        colors[led] = 4
    return {
        "device": {
            "info": {"product": "Defy"},
            "keyboard": {
                "left": [[0, 1, 2, 3, 4, 5, 6]],
                "ledsLeft": list(range(35)),
                "right": [[9, 10, 11, 12, 13, 14, 15]],
                "ledsRight": list(range(35, 70)),
            },
        },
        "virtual": {
            "keymap.custom": {"data": " ".join(map(str, keys)), "eraseable": True},
            "colormap.map": {"data": " ".join(map(str, colors)), "eraseable": True},
        },
    }


class CopyNumbersTest(unittest.TestCase):
    def test_copies_only_number_keys_and_their_leds(self):
        layout = sample_layout()
        original = copy.deepcopy(layout)
        copied = copy_numbers(layout)
        self.assertEqual(len(copied), 10)
        before_keys = list(map(int, original["virtual"]["keymap.custom"]["data"].split()))
        after_keys = list(map(int, layout["virtual"]["keymap.custom"]["data"].split()))
        before_colors = list(map(int, original["virtual"]["colormap.map"]["data"].split()))
        after_colors = list(map(int, layout["virtual"]["colormap.map"]["data"].split()))
        self.assertEqual([i for i in range(len(before_keys)) if before_keys[i] != after_keys[i]],
                         [241, 242, 243, 244, 245, 250, 251, 252, 253, 254])
        self.assertEqual([i for i in range(len(before_colors)) if before_colors[i] != after_colors[i]],
                         [211, 212, 213, 214, 215, 246, 247, 248, 249, 250])
        self.assertEqual(after_keys[:240], before_keys[:240])

    def test_rejects_nonblank_destination_without_changes(self):
        layout = sample_layout()
        keys = layout["virtual"]["keymap.custom"]["data"].split()
        keys[241] = "4"
        layout["virtual"]["keymap.custom"]["data"] = " ".join(keys)
        original = copy.deepcopy(layout)
        with self.assertRaisesRegex(ValueError, "not blank"):
            copy_numbers(layout)
        self.assertEqual(layout, original)


if __name__ == "__main__":
    unittest.main()
