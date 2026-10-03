import copy
import unittest

from customize_trans_key import CMD_S, customize


def sample_backup():
    keys = [4] * 160
    keys[80] = 65535
    keys[81] = 65535
    colors = [0] * 4
    colors[2] = 1  # First transparent key is already green.
    return {
        "neuron": {
            "layers": [{"id": 0}, {"id": 1}],
            "device": {
                "info": {"product": "Defy"},
                "RGBWMode": True,
                "keyboard": {
                    "left": [[0, 1]],
                    "ledsLeft": [0, 1],
                    "right": [],
                    "ledsRight": [],
                },
            },
        },
        "backup": [
            {"command": "keymap.custom", "data": " ".join(map(str, keys))},
            {"command": "colormap.map", "data": " ".join(map(str, colors))},
            {"command": "palette", "data": "255 0 0 0 0 254 24 0"},
            {"command": "settings.defaultLayer", "data": "0"},
        ],
    }


class CustomizeTransKeyTest(unittest.TestCase):
    def test_changes_one_transparent_key_and_its_led_only(self):
        backup = sample_backup()
        original = copy.deepcopy(backup)

        self.assertEqual(customize(backup, 2), (1, 1, 0, 1))
        old_keys = original["backup"][0]["data"].split()
        new_keys = backup["backup"][0]["data"].split()
        old_colors = original["backup"][1]["data"].split()
        new_colors = backup["backup"][1]["data"].split()
        self.assertEqual([i for i, pair in enumerate(zip(old_keys, new_keys)) if pair[0] != pair[1]], [81])
        self.assertEqual(new_keys[81], str(CMD_S))
        self.assertEqual([i for i, pair in enumerate(zip(old_colors, new_colors)) if pair[0] != pair[1]], [3])
        self.assertEqual(new_colors[3], "1")
        self.assertEqual(backup["backup"][2:], original["backup"][2:])

    def test_explicit_non_transparent_key_is_rejected_without_changes(self):
        backup = sample_backup()
        original = copy.deepcopy(backup)
        with self.assertRaisesRegex(ValueError, "not a physical transparent key"):
            customize(backup, 2, key_index=2)
        self.assertEqual(backup, original)

    def test_virtual_file_uses_the_same_key_and_color_commands(self):
        backup = sample_backup()
        virtual = {
            "device": backup["neuron"]["device"],
            "virtual": {entry["command"]: {"data": entry["data"], "eraseable": True}
                        for entry in backup["backup"]},
        }
        self.assertEqual(customize(virtual, 2), (1, 1, 0, 1))
        self.assertEqual(virtual["virtual"]["keymap.custom"]["data"].split()[81], str(CMD_S))
        self.assertEqual(virtual["virtual"]["colormap.map"]["data"].split()[3], "1")


if __name__ == "__main__":
    unittest.main()
