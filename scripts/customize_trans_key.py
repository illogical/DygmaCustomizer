#!/usr/bin/env python3
"""Change one transparent Defy key in a Bazecor virtual keyboard or backup."""

import argparse
import json
from pathlib import Path
import sys


TRANSPARENT = 65535
CMD_S = 4096 + 22  # Bazecor OS/GUI modifier + HID keycode for S.
KEYS_PER_LAYER = 80


def command_entry(layout, name):
    if "virtual" in layout:
        entry = layout["virtual"].get(name)
    else:
        matches = [entry for entry in layout["backup"] if entry.get("command") == name]
        entry = matches[0] if len(matches) == 1 else None
    if not isinstance(entry, dict) or not isinstance(entry.get("data"), str):
        raise ValueError(f"Expected one {name} command with string data")
    return entry


def numbers(entry, name):
    try:
        return [int(value) for value in entry["data"].split()]
    except ValueError as error:
        raise ValueError(f"{name} contains a nonnumeric value") from error


def green_palette_slot(palette, rgbw):
    width = 4 if rgbw else 3
    if len(palette) % width:
        raise ValueError("Palette length is not a multiple of its color width")
    colors = [palette[index : index + width] for index in range(0, len(palette), width)]
    greens = [
        (index, color)
        for index, color in enumerate(colors)
        if color[1] >= 80 and color[1] > color[0] + 40 and color[1] > color[2] + 40
    ]
    if not greens:
        raise ValueError("No existing green color found in the backup palette")
    return max(greens, key=lambda item: (item[1][1], -item[1][0] - item[1][2]))[0]


def physical_key_led_pairs(keyboard):
    # The Defy backup lists 36 right-side key positions but only 35 right LEDs.
    # Use the left side for this first experiment, where the arrays align.
    positions = [position for row in keyboard["left"] for position in row]
    leds = keyboard["ledsLeft"]
    if len(positions) != len(leds):
        raise ValueError("Left key positions and LEDs do not match")
    pairs = list(zip(positions, leds))
    if len({position for position, _ in pairs}) != len(pairs):
        raise ValueError("Duplicate physical key positions")
    return pairs


def customize(layout, layer, key_index=None):
    if "virtual" in layout:
        device = layout["device"]
    elif "backup" in layout:
        device = layout["neuron"]["device"]
    else:
        raise ValueError("Expected a Bazecor virtual keyboard or backup JSON file")
    if device.get("info", {}).get("product") != "Defy":
        raise ValueError("This script accepts only Defy configurations")
    key_entry = command_entry(layout, "keymap.custom")
    color_entry = command_entry(layout, "colormap.map")
    palette_entry = command_entry(layout, "palette")
    keys = numbers(key_entry, "keymap.custom")
    colors = numbers(color_entry, "colormap.map")
    palette = numbers(palette_entry, "palette")
    if len(keys) % KEYS_PER_LAYER:
        raise ValueError("Unexpected keymap length for the Defy layers")
    layer_count = len(keys) // KEYS_PER_LAYER
    if "backup" in layout and layer_count != len(layout["neuron"]["layers"]):
        raise ValueError("Keymap length does not match the backup layers")
    if not 1 <= layer <= layer_count:
        raise ValueError(f"Layer must be between 1 and {layer_count}")

    if len(colors) % layer_count:
        raise ValueError("Colormap length does not match the layer count")
    leds_per_layer = len(colors) // layer_count
    green_slot = green_palette_slot(palette, device.get("RGBWMode", False))

    candidates = []
    for position, led in physical_key_led_pairs(device["keyboard"]):
        if not 0 <= position < KEYS_PER_LAYER or not 0 <= led < leds_per_layer:
            raise ValueError("Physical key position or LED is outside the backup map")
        key_offset = (layer - 1) * KEYS_PER_LAYER + position
        color_offset = (layer - 1) * leds_per_layer + led
        if keys[key_offset] == TRANSPARENT:
            candidates.append((position, led, key_offset, color_offset))

    if key_index is not None:
        candidates = [candidate for candidate in candidates if candidate[0] == key_index]
        if not candidates:
            raise ValueError(f"Key position {key_index} is not a physical transparent key on layer {layer}")
    else:
        # Prefer a visible change when a transparent key is already green.
        candidates.sort(key=lambda candidate: colors[candidate[3]] == green_slot)
    if not candidates:
        raise ValueError(f"No physical transparent keys found on layer {layer}")

    position, led, key_offset, color_offset = candidates[0]
    previous_color = colors[color_offset]
    keys[key_offset] = CMD_S
    colors[color_offset] = green_slot
    key_entry["data"] = " ".join(map(str, keys))
    color_entry["data"] = " ".join(map(str, colors))
    return position, led, previous_color, green_slot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Bazecor virtual keyboard or backup JSON")
    parser.add_argument("output", type=Path, help="New JSON file to load into Bazecor")
    parser.add_argument("--layer", type=int, default=2, help="Displayed layer number (default: 2)")
    parser.add_argument("--key-index", type=int, help="Specific physical key index, 0–79")
    args = parser.parse_args()

    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("Input and output must be different files")
        with args.input.open(encoding="utf-8") as source:
            layout = json.load(source)
        position, led, old_color, green_slot = customize(layout, args.layer, args.key_index)
        with args.output.open("x", encoding="utf-8") as destination:
            json.dump(layout, destination, indent=2, ensure_ascii=False)
            destination.write("\n")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.exit(1, f"Error: {error}\n")

    print(f"Created {args.output}")
    print(f"Layer {args.layer}, key position {position}, LED {led}: Trans → Cmd+S; "
          f"color slot {old_color} → existing green slot {green_slot}")


if __name__ == "__main__":
    main()
