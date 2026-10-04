#!/usr/bin/env python3
"""Inspect or safely edit a Defy virtual JSON. Layer arguments use displayed L1-L10."""
import argparse
import copy
import json
from collections import Counter
from pathlib import Path

from customize_trans_key import command_entry, numbers

KEYS = 80
FIXTURE_RIGHT_ROWS = [list(range(9, 16)), list(range(25, 32)),
                      list(range(41, 48))]
FIXTURE_RIGHT_LEDS = list(range(35, 56))


def model(doc):
    if doc.get('device', {}).get('info', {}).get('product') != 'Defy' or 'virtual' not in doc:
        raise ValueError('Expected a Defy virtual JSON')
    entries = {name: command_entry(doc, name) for name in ('keymap.custom', 'colormap.map', 'palette')}
    arrays = {name: numbers(entry, name) for name, entry in entries.items()}
    keys, colors, palette = (arrays[n] for n in entries)
    if len(keys) % KEYS or not keys:
        raise ValueError('Invalid Defy keymap length')
    layers = len(keys) // KEYS
    if len(colors) % layers:
        raise ValueError('Invalid colormap length')
    leds = len(colors) // layers
    width = 4 if doc['device'].get('RGBWMode') else 3
    if len(palette) % width or not palette:
        raise ValueError('Invalid palette length')
    slots = len(palette) // width
    if any(not 0 <= slot < slots for slot in colors):
        raise ValueError('Colormap references a missing palette slot')
    return entries, arrays, layers, leds, width, slots


def layer(n, count):
    if not 1 <= n <= count:
        raise ValueError(f'Layer must be L1-L{count}')
    return n - 1


def led_map(doc):
    keyboard = doc['device']['keyboard']
    mapping = {}
    for side in ('left', 'right'):
        rows = keyboard[side]
        keys = [key for row in rows for key in row]
        leds = keyboard['leds' + side.capitalize()]
        # The L8 fixture paints the first two right rows and anchors the third
        # row's final key at LED 55. Those rows each have seven keys and LEDs.
        # The right thumb row still has one more key than remaining LEDs.
        if side == 'right':
            proven_rows = (rows[:3] if rows[:3] == FIXTURE_RIGHT_ROWS
                           and leds[:21] == FIXTURE_RIGHT_LEDS else rows[:1])
            keys = [key for row in proven_rows for key in row]
            leds = leds[:len(keys)]
        if len(keys) != len(leds):
            raise ValueError(f'{side} key/LED mapping is ambiguous')
        mapping.update(zip(keys, leds))
    return mapping


def edit(doc, args):
    entries, arrays, count, leds, width, slots = model(doc)
    keys, colors, palette = (arrays[n] for n in entries)
    operation = args.action
    if operation in ('copy-keys', 'copy-layer', 'move-layer'):
        src, dst = layer(args.source, count), layer(args.target, count)
        if src == dst:
            raise ValueError('Source and destination layers must differ')
        if operation == 'copy-keys':
            positions = args.positions
            if not positions or len(set(positions)) != len(positions) or any(not 0 <= p < KEYS for p in positions):
                raise ValueError('Give unique key positions from 0 to 79')
            mapping = led_map(doc) if args.colors else {}
            if args.colors and any(p not in mapping for p in positions):
                raise ValueError('A requested key has no verified LED mapping; copy keys without colors')
            for p in positions:
                if not args.replace and keys[dst*KEYS+p] != 65535:
                    raise ValueError(f'L{args.target} position {p} is not transparent; use --replace')
            for p in positions:
                keys[dst*KEYS+p] = keys[src*KEYS+p]
                if args.colors:
                    led = mapping[p]
                    colors[dst*leds+led] = colors[src*leds+led]
        else:
            if operation == 'move-layer' and not 0 <= args.clear_slot < slots:
                raise ValueError('Clear slot out of range')
            dst_keys = keys[dst*KEYS:(dst+1)*KEYS]
            if not args.replace and any(k != 65535 for k in dst_keys):
                raise ValueError(f'L{args.target} has assigned keys; use --replace')
            keys[dst*KEYS:(dst+1)*KEYS] = keys[src*KEYS:(src+1)*KEYS]
            colors[dst*leds:(dst+1)*leds] = colors[src*leds:(src+1)*leds]
            if operation == 'move-layer':
                keys[src*KEYS:(src+1)*KEYS] = [65535]*KEYS
                colors[src*leds:(src+1)*leds] = [args.clear_slot]*leds
    elif operation == 'set-color':
        target = layer(args.target, count)
        if not 0 <= args.slot < slots:
            raise ValueError('Palette slot out of range')
        if (args.position is None) == (args.led is None):
            raise ValueError('Specify exactly one of --position or --led')
        if args.position is not None:
            mapping = led_map(doc)
            if args.position not in mapping:
                raise ValueError('Position has no verified LED mapping; use --led after Bazecor check')
            led = mapping[args.position]
        else:
            led = args.led
        if not 0 <= led < leds:
            raise ValueError('LED out of range')
        colors[target*leds+led] = args.slot
    elif operation == 'set-palette':
        if not 0 <= args.slot < slots or len(args.channels) != width or any(not 0 <= x <= 255 for x in args.channels):
            raise ValueError(f'Expected valid slot and {width} channels (0-255)')
        if args.slot in colors and not args.replace:
            raise ValueError('Slot is in use; --replace changes every key using it')
        palette[args.slot*width:(args.slot+1)*width] = args.channels
    for name, array in arrays.items():
        entries[name]['data'] = ' '.join(map(str, array))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    inspect = sub.add_parser('inspect', help='Show palette RGB(W) values and slot usage by layer')
    inspect.add_argument('input', type=Path)
    for action in ('copy-keys', 'copy-layer', 'move-layer', 'set-color', 'set-palette'):
        p = sub.add_parser(action)
        p.add_argument('input', type=Path)
        p.add_argument('output', type=Path)
        if action in ('copy-keys', 'copy-layer', 'move-layer'):
            p.add_argument('--source', type=int, required=True)
            p.add_argument('--target', type=int, required=True)
            p.add_argument('--replace', action='store_true')
        if action == 'copy-keys':
            p.add_argument('--positions', nargs='+', type=int, required=True)
            p.add_argument('--colors', action='store_true')
        if action == 'move-layer':
            p.add_argument('--clear-slot', type=int, default=15)
        if action == 'set-color':
            p.add_argument('--target', type=int, required=True)
            p.add_argument('--position', type=int)
            p.add_argument('--led', type=int)
            p.add_argument('--slot', type=int, required=True)
        if action == 'set-palette':
            p.add_argument('--slot', type=int, required=True)
            p.add_argument('--channels', nargs='+', type=int, required=True)
            p.add_argument('--replace', action='store_true')
    args = parser.parse_args()
    try:
        if hasattr(args, 'output') and args.input.resolve() == args.output.resolve():
            raise ValueError('Input and output must differ')
        with args.input.open(encoding='utf-8') as file:
            original = json.load(file)
        doc = copy.deepcopy(original)
        entries, arrays, count, leds, width, slots = model(doc)
        if args.action == 'inspect':
            colors, palette = arrays['colormap.map'], arrays['palette']
            for slot in range(slots):
                usage = [Counter(colors[i*leds:(i+1)*leds])[slot] for i in range(count)]
                print(f'{slot:2}: {palette[slot*width:(slot+1)*width]}  total={sum(usage)}  ' +
                      ' '.join(f'L{i+1}:{n}' for i,n in enumerate(usage) if n))
            return
        edit(doc, args)
        # Check the exact set of JSON fields changed before creating a file.
        changed = [name for name in ('keymap.custom', 'colormap.map', 'palette')
                   if command_entry(original, name)['data'] != command_entry(doc, name)['data']]
        probe = copy.deepcopy(original)
        for name in changed:
            command_entry(probe, name)['data'] = command_entry(doc, name)['data']
        if probe != doc:
            raise ValueError('Unexpected JSON change')
        with args.output.open('x', encoding='utf-8') as file:
            json.dump(doc, file, indent=2, ensure_ascii=False)
            file.write('\n')
        print(f'Created {args.output}; changed: {", ".join(changed) or "nothing"}')
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
