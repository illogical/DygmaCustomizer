#!/usr/bin/env python3
"""Copy L1's number row and matching LED colors to L4 in a virtual Defy."""

import argparse
import json
from pathlib import Path

from customize_trans_key import KEYS_PER_LAYER, TRANSPARENT, command_entry, numbers


NUMBER_KEYCODES = set(range(30, 40))  # HID 1–0.
TARGET_LAYER = 3  # Displayed L4; stored layers are zero-indexed.


def top_row_leds(keyboard):
    """Map only the top row, where Defy's key and LED lists align."""
    mapping = {}
    for side in ("left", "right"):
        keys = keyboard[side][0]
        leds = keyboard["leds" + side.capitalize()][: len(keys)]
        if len(keys) != len(leds):
            raise ValueError(f"{side} top-row keys and LEDs do not align")
        mapping.update(zip(keys, leds))
    return mapping


def copy_numbers(layout):
    if "virtual" not in layout or layout.get("device", {}).get("info", {}).get("product") != "Defy":
        raise ValueError("Expected a Defy virtual keyboard JSON file")
    key_entry = command_entry(layout, "keymap.custom")
    color_entry = command_entry(layout, "colormap.map")
    keys = numbers(key_entry, "keymap.custom")
    colors = numbers(color_entry, "colormap.map")
    if len(keys) % KEYS_PER_LAYER or len(keys) // KEYS_PER_LAYER <= TARGET_LAYER:
        raise ValueError("Keymap does not contain L4 in the expected Defy format")
    layer_count = len(keys) // KEYS_PER_LAYER
    if len(colors) % layer_count:
        raise ValueError("Colormap length does not match the layer count")
    leds_per_layer = len(colors) // layer_count
    position_to_led = top_row_leds(layout["device"]["keyboard"])

    number_positions = {}
    for position, code in enumerate(keys[:KEYS_PER_LAYER]):
        if code in NUMBER_KEYCODES:
            if code in number_positions:
                raise ValueError(f"L1 has duplicate number keycode {code}")
            number_positions[code] = position
    if set(number_positions) != NUMBER_KEYCODES:
        raise ValueError("L1 must contain exactly one key for each number 1–0")
    if any(position not in position_to_led for position in number_positions.values()):
        raise ValueError("A number key is outside the top row LED map")

    for position in number_positions.values():
        target_offset = TARGET_LAYER * KEYS_PER_LAYER + position
        if keys[target_offset] != TRANSPARENT:
            raise ValueError(f"L4 key position {position} is not blank")
        led = position_to_led[position]
        if not 0 <= led < leds_per_layer:
            raise ValueError(f"LED {led} is outside the per-layer colormap")

    for code in sorted(NUMBER_KEYCODES):
        position = number_positions[code]
        led = position_to_led[position]
        keys[TARGET_LAYER * KEYS_PER_LAYER + position] = code
        colors[TARGET_LAYER * leds_per_layer + led] = colors[led]
    key_entry["data"] = " ".join(map(str, keys))
    color_entry["data"] = " ".join(map(str, colors))
    return [(code, number_positions[code], position_to_led[number_positions[code]])
            for code in sorted(NUMBER_KEYCODES)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Existing Defy virtual keyboard JSON")
    parser.add_argument("output", type=Path, help="New virtual keyboard JSON to load")
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("Input and output must be different files")
        with args.input.open(encoding="utf-8") as source:
            layout = json.load(source)
        copied = copy_numbers(layout)
        with args.output.open("x", encoding="utf-8") as destination:
            json.dump(layout, destination, indent=2, ensure_ascii=False)
            destination.write("\n")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.exit(1, f"Error: {error}\n")

    print(f"Created {args.output}")
    print("Copied L1 numbers and colors to L4:")
    for code, position, led in copied:
        label = str(code - 29) if code <= 38 else "0"
        print(f"  {label}: key position {position}, LED {led}")


if __name__ == "__main__":
    main()
