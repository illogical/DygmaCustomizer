#!/usr/bin/env python3
"""Read a Defy virtual JSON and locate current keys and manifest proposals."""

import argparse
import copy
import json
import re
from pathlib import Path

from apply_template import PLAIN, MODIFIER_OFFSETS, VERIFIED_DEVICE_SOURCE, plan
from defy import KEYS, model
from resolve_template import read_json, resolve


ROOT = Path(__file__).resolve().parents[1]
HID_NAMES = {
    40: 'Enter', 41: 'Esc', 42: 'Backspace', 46: 'Equals', 47: 'Left Bracket',
    48: 'Right Bracket', 49: 'Backslash', 51: 'Semicolon', 52: 'Quote',
    55: 'Period', 56: 'Slash',
}
CODE_NAMES = {code: name for name, code in PLAIN.items()}
CODE_NAMES.update(HID_NAMES)
CODE_NAMES.update({source[2]: name.replace('-', ' ').title()
                   for name, source in VERIFIED_DEVICE_SOURCE.items()})
MODIFIER_NAMES = sorted(
    ((offset, '+'.join(name for name in ('Ctrl', 'Alt', 'Cmd', 'Shift') if name in modifiers))
     for modifiers, offset in MODIFIER_OFFSETS.items()),
    reverse=True,
)
LAYER_ACTIONS = {'one-shot-layer', 'layer-lock', 'layer-shift', 'move-to-layer'}


def output_name(code):
    """Decode only outputs already named by this project's key tables."""
    if code == 65535:
        return 'Transparent'
    if code in CODE_NAMES:
        return CODE_NAMES[code]
    for offset, modifier in MODIFIER_NAMES:
        base = CODE_NAMES.get(code - offset)
        if base and code - offset in PLAIN.values():
            return modifier + '+' + base
    return None


def geometry(doc):
    keyboard = doc['device']['keyboard']
    positions = {}
    for side in ('left', 'right'):
        rows = keyboard[side]
        for row_number, row in enumerate(rows, 1):
            for column, index in enumerate(row, 1):
                if type(index) is not int or not 0 <= index < KEYS or index in positions:
                    raise ValueError('Defy geometry has a duplicate or invalid key index')
                positions[index] = (side, row_number, column)
    if not positions:
        raise ValueError('Defy geometry has no physical key positions')
    return keyboard, positions


def neighbor_labels(keyboard, l1, side, row_number, column):
    row = keyboard[side][row_number - 1]
    # Thumb columns follow the fan's numbering, which differs from screen order.
    if row_number == 5:
        order = ([1, 2, 3, 4, 8, 7, 6, 5] if side == 'left'
                 else [4, 3, 2, 1, 5, 6, 7, 8])
        group = order[:4] if column in order[:4] else order[4:]
        neighbors = [group[i] for i in (group.index(column) - 1, group.index(column) + 1)
                     if 0 <= i < len(group)]
        nearby = [(f'adjacent thumb c{c}', row[c - 1]) for c in neighbors if c <= len(row)]
    else:
        nearby = []
        for c, direction in ((column - 1, 'left'), (column + 1, 'right')):
            if 1 <= c <= len(row):
                nearby.append((direction, row[c - 1]))
        for r, direction in ((row_number - 1, 'above'), (row_number + 1, 'below')):
            if 1 <= r <= min(4, len(keyboard[side])) and column <= len(keyboard[side][r - 1]):
                nearby.append((direction, keyboard[side][r - 1][column - 1]))
    return '; '.join(f'{direction}: L1 {output_name(l1[index]) or "keycode " + str(l1[index])}'
                     for direction, index in nearby) or 'no adjacent key in this row'


def action_index(doc, manifest, profile, template_loader, positions):
    if manifest is None:
        return [], []
    if profile is None or template_loader is None:
        raise ValueError('A manifest needs its machine profile and template loader')
    if manifest.get('schema_version') != 1 or not isinstance(manifest.get('layers'), list):
        raise ValueError('Expected a version 1 PC manifest with layers')
    _, arrays, count, _, _, _ = model(doc)
    keys = arrays['keymap.custom']
    resolved_profile = copy.deepcopy(profile)
    resolved_profile['layer_targets'] = {
        **profile.get('layer_targets', {}), **manifest.get('layer_targets', {})}
    actions, notes = [], []
    for entry in manifest['layers']:
        number = entry['layer']
        if type(number) is not int or not 1 <= number <= count:
            raise ValueError(f'Manifest layer {number!r} is absent from source')
        template = template_loader(entry['template'])
        try:
            resolved = resolve(template, profile['os'], resolved_profile, doc)
            report = plan(doc, template, resolved_profile, number,
                          with_keys=True, with_colors=False, source=doc)
        except (ValueError, KeyError, TypeError) as error:
            notes.append(f'L{number} {entry["template"]}: {error}')
            continue
        bindings = {row['id']: row for row in resolved['bindings']}
        for row in report['rows']:
            index = row['position_index']
            actual = keys[(number - 1) * KEYS + index]
            expected = row.get('after_keycode')
            binding = bindings[row['id']]
            action = binding.get('bazecor_action') or {}
            unsupported = row.get('unsupported')
            if action.get('type') == 'device-command':
                verified = VERIFIED_DEVICE_SOURCE.get(action.get('command'))
                if verified:
                    # Applying a copied command needs its original source key.
                    # Looking one up only needs the already verified code.
                    expected, unsupported = verified[2], None
            status = ('unverified' if unsupported or expected is None else
                      'confirmed' if expected == actual else 'mismatch')
            side, row_number, column = positions[index]
            actions.append({
                'id': f'{template["id"]}.{row["id"]}', 'name': row['name'],
                'layer': number, 'position_id': f'defy:{side}:r{row_number}:c{column}',
                'key_index': index, 'status': status, 'actual_keycode': actual,
                'expected_keycode': expected, 'shortcut': binding.get('shortcut'),
                'bazecor_action': binding.get('bazecor_action'),
                'reason': unsupported or (
                    f'JSON has {actual}; manifest expects {expected}' if status == 'mismatch' else None),
            })
        for action_id, reason in report['skipped']:
            actions.append({'id': f'{template["id"]}.{action_id}', 'name': action_id,
                            'layer': number, 'status': 'unverified', 'reason': reason})
        notes.extend(resolved['warnings'])
    return actions, notes


def inspect_layout(doc, manifest=None, profile=None, template_loader=None):
    """Return a complete positional inventory and cross-checked action index."""
    _, arrays, count, _, _, _ = model(doc)
    keyboard, positions = geometry(doc)
    keys = arrays['keymap.custom']
    l1 = keys[:KEYS]
    actions, notes = action_index(doc, manifest, profile, template_loader, positions)
    by_position = {}
    access = {}
    for action in actions:
        if action['status'] == 'confirmed' and 'key_index' in action:
            by_position.setdefault((action['layer'], action['key_index']), []).append(action)
            control = action.get('bazecor_action') or {}
            if control.get('type') in LAYER_ACTIONS:
                access.setdefault(control['target_layer'], []).append(action)
    rows = []
    for number in range(1, count + 1):
        for index in sorted(positions):
            side, row_number, column = positions[index]
            code = keys[(number - 1) * KEYS + index]
            l1_label = output_name(l1[index]) or f'keycode {l1[index]}'
            entries = access.get(number, [])
            instructions = [
                f"From L{a['layer']}, {a['bazecor_action']['type']} to L{number} "
                f"at {a['position_id']}" for a in entries
            ]
            rows.append({
                'layer': number, 'side': side, 'row': row_number, 'column': column,
                'key_index': index, 'position_id': f'defy:{side}:r{row_number}:c{column}',
                'l1_label': l1_label, 'keycode': code, 'output': output_name(code),
                'landmark': f'{side} half, ' + (
                    f'thumb cluster, column {column}' if row_number == 5 else
                    f'row {row_number}, column {column}'),
                'nearby': neighbor_labels(keyboard, l1, side, row_number, column),
                'actions': [a['id'] for a in by_position.get((number, index), [])],
                'access': ('L1' if number == 1 else
                           '; '.join(instructions) if instructions else 'No verified entry in manifest'),
            })
    return {'layers': count, 'positions': rows, 'actions': actions, 'notes': notes,
            'source_kind': 'virtual Defy JSON'}


def search(inventory, query):
    needle = re.sub(r'[^a-z0-9]+', ' ', query.casefold()).strip()
    if not needle:
        raise ValueError('Query must contain letters or digits')
    def normalized(value):
        return re.sub(r'[^a-z0-9]+', ' ', str(value).casefold()).strip()
    def matches(value):
        return needle in normalized(value)
    def matches_output(value):
        words = normalized(value)
        return bool(re.search(r'(?<![a-z0-9])' + re.escape(needle) + r'(?![a-z0-9])', words))
    action_matches = [a for a in inventory['actions']
                      if matches(a['id']) or matches(a['name']) or matches(a.get('shortcut') or '')]
    matched_ids = {a['id'] for a in action_matches if a['status'] == 'confirmed'}
    confirmed = [row for row in inventory['positions']
                 if matches_output(row['output'] or '') or any(a in matched_ids for a in row['actions'])]
    proposed = [a for a in action_matches if a['status'] != 'confirmed']
    return {'query': query, 'confirmed_matches': confirmed, 'proposed_matches': proposed,
            'notes': inventory['notes'],
            'coverage_note': 'Unknown keycodes and unsupported manifest actions cannot prove purpose or absence.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('configuration', type=Path, help='Current Defy virtual JSON to inspect')
    parser.add_argument('--manifest', type=Path, help='PC manifest for purpose names')
    parser.add_argument('--profile', type=Path, help='Override profile path in manifest')
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--query', help='Search key outputs and manifest action names')
    choice.add_argument('--inventory', action='store_true', help='List every physical position on every layer')
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    args = parser.parse_args()
    if args.profile and not args.manifest:
        parser.error('--profile requires --manifest')
    try:
        doc = read_json(args.configuration)
        manifest = read_json(args.manifest) if args.manifest else None
        profile_path = args.profile or (ROOT / manifest['profile'] if manifest else None)
        profile = read_json(profile_path) if profile_path else None
        inventory = inspect_layout(doc, manifest, profile,
                                   lambda path: read_json(ROOT / path) if manifest else None)
        result = inventory if args.inventory else search(inventory, args.query)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.error(str(error))
    if args.format == 'json':
        print(json.dumps(result, indent=2))
        return
    rows = result['positions'] if args.inventory else result['confirmed_matches']
    for row in rows:
        print(f"L{row['layer']} {row['position_id']} (index {row['key_index']}), "
              f"L1 {row['l1_label']}: {row['output'] or 'unknown code ' + str(row['keycode'])}")
        print(f"  {row['landmark']}; {row['nearby']}; access: {row['access']}")
        if row['actions']:
            print('  Confirmed purposes: ' + ', '.join(row['actions']))
    if not args.inventory:
        for action in result['proposed_matches']:
            print(f"{action['status'].upper()} L{action['layer']} {action.get('position_id', 'unknown position')}: "
                  f"{action['name']} ({action['reason']})")
        if not rows:
            print('No confirmed match in the selected JSON and verified purpose mapping.')
        print(result['coverage_note'])
    for note in result['notes']:
        print('Note: ' + note)


if __name__ == '__main__':
    main()
