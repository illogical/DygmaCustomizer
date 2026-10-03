#!/usr/bin/env python3
"""Preview or apply a partial named template to a Defy virtual JSON layer."""

import argparse
import copy
import json
from pathlib import Path

from customize_trans_key import command_entry
from defy import KEYS, led_map, model, layer
from resolve_template import read_json, resolve

TRANSPARENT = 65535

# Plain USB HID keys already used by Defy keymaps. Modifier combos need a
# Bazecor-made fixture; the only confirmed combo in this project is Cmd+S.
PLAIN = {chr(65 + i): 4 + i for i in range(26)}
PLAIN.update({str(i): 29 + i for i in range(1, 10)})
PLAIN['0'] = 39
PLAIN.update({'Tab': 43, 'Space': 44, 'Minus': 45, 'Grave': 53,
              'Left': 80, 'Right': 79, 'Up': 82, 'Down': 81})
ENCODED = {'Cmd+S': 4118}


def encode(chord):
    if isinstance(chord, list):
        raise ValueError('ordered sequence needs a Bazecor-verified macro')
    if chord in ENCODED:
        return ENCODED[chord]
    if chord in PLAIN:
        return PLAIN[chord]
    raise ValueError(f'{chord} needs a Bazecor-verified keycode')


def color_slot(template, category, palette, width):
    slots = template.get('color_slots', {})
    if not isinstance(slots, dict):
        raise ValueError('template.color_slots must map slot IDs to purpose names')
    matches = [slot for slot, purpose in slots.items() if purpose == category]
    if len(matches) != 1:
        raise ValueError(f'color category {category} needs exactly one template.color_slots entry')
    try:
        slot = int(matches[0])
    except (TypeError, ValueError) as error:
        raise ValueError(f'color category {category} has invalid slot') from error
    if not 0 <= slot < len(palette) // width:
        raise ValueError(f'color category {category} has invalid slot {slot}')
    return slot


def plan(doc, template, profile, target, with_keys=True, with_colors=True):
    entries, arrays, count, leds, width, _ = model(doc)
    target_index = layer(target, count)
    result = resolve(template, profile['os'], profile, doc,
                     include_without_shortcut=with_colors and not with_keys)
    keys, colors, palette = (arrays[name] for name in entries)
    mapping = led_map(doc) if with_colors else {}
    rows = []
    used_indices = set()
    for binding in result['bindings']:
        index = binding['position_index']
        if not 0 <= index < KEYS:
            raise ValueError(f'Invalid key position: {index}')
        if index in used_indices:
            raise ValueError(f'Template maps two actions to physical index {index}')
        used_indices.add(index)
        offset = target_index * KEYS + index
        row = {'id': binding['id'], 'name': binding['name'],
               'position_id': binding.get('position_id'), 'position_index': index,
               'l1_label': binding['l1_label'], 'color_category': binding['color_category']}
        if with_keys:
            row['shortcut'] = binding['shortcut']
            row['before_keycode'] = keys[offset]
            try:
                row['after_keycode'] = encode(binding['shortcut'])
            except ValueError as error:
                row['unsupported'] = str(error)
        if with_colors:
            try:
                if index not in mapping:
                    raise ValueError('key has no verified LED mapping')
                led = mapping[index]
                if not 0 <= led < leds:
                    raise ValueError('LED is outside the layer colormap')
                row['led_index'] = led
                row['before_color_slot'] = colors[target_index*leds+led]
                row['after_color_slot'] = color_slot(template, binding['color_category'], palette, width)
            except ValueError as error:
                row['unsupported'] = '; '.join(filter(None, [row.get('unsupported'), str(error)]))
        row['collision'] = (with_keys and keys[offset] != TRANSPARENT
                            and keys[offset] != row.get('after_keycode'))
        rows.append(row)
    return {'template': template['id'], 'target_layer': target, 'rows': rows,
            'skipped': result['skipped'], 'warnings': result['warnings'],
            'with_keys': with_keys, 'with_colors': with_colors}


def apply(doc, report, override=False, allow_skipped=False):
    if not report['rows']:
        raise ValueError('No template actions are available to apply')
    if report['skipped'] and not allow_skipped:
        raise ValueError('Skipped actions: ' + ', '.join(action for action, _ in report['skipped']) + '; use --allow-skipped')
    blocked = [row for row in report['rows'] if row.get('unsupported')]
    if blocked:
        raise ValueError('Unsupported actions: ' + ', '.join(row['id'] for row in blocked))
    collisions = [row for row in report['rows'] if row['collision']]
    if collisions and not override:
        raise ValueError('Occupied positions: ' + ', '.join(f"{row['id']}@{row['position_index']}" for row in collisions) + '; use --override')
    entries, arrays, _, leds, _, _ = model(doc)
    target = report['target_layer'] - 1
    for row in report['rows']:
        if report['with_keys']:
            arrays['keymap.custom'][target*KEYS+row['position_index']] = row['after_keycode']
        if report['with_colors']:
            arrays['colormap.map'][target*leds+row['led_index']] = row['after_color_slot']
    changed = []
    if report['with_keys']:
        changed.append('keymap.custom')
    if report['with_colors']:
        changed.append('colormap.map')
    for name in changed:
        entries[name]['data'] = ' '.join(map(str, arrays[name]))


def print_report(report):
    print(f"{report['template']} → L{report['target_layer']}: {len(report['rows'])} proposed keys")
    for row in report['rows']:
        status = ('UNSUPPORTED: ' + row['unsupported']) if row.get('unsupported') else ('COLLISION' if row['collision'] else 'ready')
        key_change = (f"{row['before_keycode']} → {row.get('after_keycode', '?')}"
                      if 'before_keycode' in row else 'keys unchanged')
        print(f"  {row['id']} at {row['position_id'] or row['l1_label']} (index {row['position_index']}): "
              f"{key_change}  {status}")
        if 'after_color_slot' in row:
            print(f"    LED {row['led_index']}: slot {row['before_color_slot']} → {row['after_color_slot']} ({row['color_category']})")
    for action, reason in report['skipped']:
        print(f'  SKIPPED {action}: {reason}')
    for warning in report['warnings']:
        print(f'  WARNING {warning}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for name in ('preview', 'apply'):
        cmd = sub.add_parser(name)
        cmd.add_argument('input', type=Path)
        cmd.add_argument('template', type=Path)
        cmd.add_argument('--target', type=int, required=True, help='Displayed layer number, starting at 1')
        cmd.add_argument('--profile', type=Path, required=True)
        feature_group = cmd.add_mutually_exclusive_group()
        feature_group.add_argument('--keys-only', action='store_true', help='Apply key assignments and preserve LED colors')
        feature_group.add_argument('--colors-only', action='store_true', help='Apply LED colors and preserve key assignments')
        if name == 'apply':
            cmd.add_argument('--output', type=Path, help='Default: INPUT-LN-TEMPLATE.json')
            cmd.add_argument('--override', action='store_true', help='Replace occupied key assignments')
            cmd.add_argument('--allow-skipped', action='store_true', help='Apply remaining actions when profile omits others')
    args = parser.parse_args()
    try:
        original = read_json(args.input)
        template = read_json(args.template)
        profile = read_json(args.profile)
        with_keys = not args.colors_only
        with_colors = not args.keys_only
        report = plan(original, template, profile, args.target, with_keys, with_colors)
        print_report(report)
        if args.action == 'preview':
            return
        output = args.output or args.input.with_name(f'{args.input.stem}-L{args.target}-{template["id"]}.json')
        if output.resolve() == args.input.resolve():
            raise ValueError('Input and output must differ')
        doc = copy.deepcopy(original)
        apply(doc, report, args.override, args.allow_skipped)
        probe = copy.deepcopy(original)
        changed = []
        if with_keys:
            changed.append('keymap.custom')
        if with_colors:
            changed.append('colormap.map')
        for name in changed:
            command_entry(probe, name)['data'] = command_entry(doc, name)['data']
        if probe != doc:
            raise ValueError('Unexpected JSON change')
        if len(model(doc)[1]['keymap.custom']) != len(model(original)[1]['keymap.custom']):
            raise ValueError('Keymap length changed')
        with output.open('x', encoding='utf-8') as file:
            json.dump(doc, file, indent=2, ensure_ascii=False)
            file.write('\n')
        print(f'Created {output}')
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
