#!/usr/bin/env python3
"""Resolve one named layer template for an OS/profile; print a preview, never edit Bazecor."""

import argparse
import json
import re
from pathlib import Path

from customize_trans_key import command_entry, numbers

OS_NAMES = ('macos', 'windows', 'linux')


def read_json(path):
    with path.open(encoding='utf-8') as file:
        return json.load(file)


def l1_positions(source):
    device = source.get('device') or source.get('neuron', {}).get('device', {})
    if device.get('info', {}).get('product') != 'Defy':
        raise ValueError('L1 source must identify a Defy')
    all_keys = numbers(command_entry(source, 'keymap.custom'), 'keymap.custom')
    if len(all_keys) < 80 or len(all_keys) % 80:
        raise ValueError('L1 source has an invalid Defy keymap length')
    keys = all_keys[:80]
    result = {}
    for index, code in enumerate(keys):
        if 4 <= code <= 29:
            label = chr(ord('A') + code - 4)
        elif 30 <= code <= 38:
            label = str(code - 29)
        elif code == 39:
            label = '0'
        else:
            continue
        result.setdefault(label, []).append(index)
    return result


def physical_position(source, position_id):
    match = re.fullmatch(r'defy:(left|right):r([1-9][0-9]*):c([1-9][0-9]*)', position_id)
    if not match:
        raise ValueError(f'Invalid Defy position ID: {position_id}')
    side, row, column = match.group(1), int(match.group(2)), int(match.group(3))
    device = source.get('device') or source.get('neuron', {}).get('device', {})
    try:
        return device['keyboard'][side][row - 1][column - 1]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError(f'Position ID absent from source geometry: {position_id}') from error


def expand_shortcut(shortcut, profile):
    if isinstance(shortcut, list):
        if not shortcut:
            raise ValueError('Shortcut sequence is empty')
        return [expand_shortcut(step, profile) for step in shortcut]
    if not isinstance(shortcut, str):
        raise ValueError('Shortcut must be a chord or sequence of chords')
    parts = shortcut.split('+')
    if any(not part for part in parts):
        raise ValueError(f'Invalid shortcut: {shortcut}')
    if 'Hyper' in parts:
        modifiers = profile.get('hyper_modifiers')
        if not modifiers:
            raise ValueError('Hyper shortcut requires profile.hyper_modifiers')
        if parts.count('Hyper') != 1:
            raise ValueError('Hyper may occur only once')
        parts = [part for token in parts for part in (modifiers if token == 'Hyper' else [token])]
    return '+'.join(parts)


def resolve(template, os_name, profile=None, source=None):
    profile = profile or {}
    if template.get('schema_version') != 1 or not template.get('id') or not isinstance(template.get('bindings'), list):
        raise ValueError('Expected template schema version 1 with id and bindings')
    if os_name not in OS_NAMES or os_name not in template.get('platforms', []):
        raise ValueError(f'Template {template["id"]} does not support {os_name}')
    if profile:
        if profile.get('schema_version') != 1 or profile.get('os') != os_name:
            raise ValueError('Profile schema or OS does not match')
        required_environment = template.get('environment')
        if required_environment and profile.get('environment') != required_environment:
            raise ValueError(f'Template requires {required_environment}')
    elif template.get('environment'):
        raise ValueError('An environment-specific template requires a matching profile')

    positions = l1_positions(source) if source else None
    index_labels = {index: label for label, indices in (positions or {}).items() for index in indices}
    seen_ids, seen_locations = set(), set()
    rows, skipped, warnings = [], [], []
    overrides = profile.get('shortcut_overrides', {})
    available_apps = set(profile.get('available_apps', []))
    for binding in template['bindings']:
        action_id = binding['id']
        label = binding['position_l1']
        position_id = binding.get('position_id')
        location = position_id or label
        if action_id in seen_ids or location in seen_locations:
            raise ValueError(f'Duplicate action or L1 position: {action_id} / {label}')
        seen_ids.add(action_id)
        seen_locations.add(location)
        index = None
        if positions is not None:
            if position_id:
                index = physical_position(source, position_id)
                if not 0 <= index < 80:
                    raise ValueError(f'Position ID outside Defy keymap: {position_id}')
                current_label = index_labels.get(index, f'keycode:{numbers(command_entry(source, "keymap.custom"), "keymap.custom")[index]}')
                if current_label != label:
                    warnings.append(f'{action_id}: L1 label changed from {label} to {current_label} at {position_id}')
            else:
                if len(positions.get(label, [])) != 1:
                    raise ValueError(f'L1 label {label} is missing or ambiguous in source')
                index = positions[label][0]
        required_app = binding.get('requires_app')
        if profile and required_app and required_app not in available_apps:
            skipped.append((action_id, f'{required_app} absent from profile.available_apps'))
            continue
        shortcut = overrides.get(f'{template["id"]}.{action_id}', binding.get('shortcuts', {}).get(os_name))
        if not shortcut:
            skipped.append((action_id, f'no {os_name} shortcut'))
            continue
        row = {'id': action_id, 'name': binding['name'], 'l1_label': label,
               'color_category': binding['color_category'],
               'shortcut': expand_shortcut(shortcut, profile)}
        if position_id:
            row['position_id'] = position_id
        if index is not None:
            row['position_index'] = index
            row['current_l1_label'] = index_labels.get(index, f'keycode:{numbers(command_entry(source, "keymap.custom"), "keymap.custom")[index]}')
        if required_app and not profile:
            row['app_status'] = 'installation unverified'
        rows.append(row)
    return {'template': template['id'], 'name': template['name'], 'os': os_name,
            'profile': profile.get('id'), 'activation': template.get('activation'),
            'source': template.get('source'), 'bindings': rows, 'skipped': skipped,
            'warnings': warnings}


def markdown(result):
    title = result['name'] + ' — ' + result['os']
    if result['profile']:
        title += ' / ' + result['profile']
    lines = [f'# {title}', '', 'Proposed layer; no Bazecor JSON or keyboard changed.', '']
    activation = result['activation'] or {}
    lines += [f'Activation: {activation.get("mode", "unspecified")}; L1 trigger: {activation.get("trigger_l1") or "to choose"}.', '']
    lines += ['| L1 hint | Position ID | Index | Action | Shortcut / sequence | Color category |', '| --- | --- | ---: | --- | --- | --- |']
    for row in result['bindings']:
        shortcut = row['shortcut']
        display = ' → '.join(shortcut) if isinstance(shortcut, list) else shortcut
        lines.append(f'| {row["l1_label"]} | {row.get("position_id", "—")} | {row.get("position_index", "—")} | {row["name"]} | {display} | {row["color_category"]} |')
    if result['warnings']:
        lines += ['', 'Position notes:']
        lines += [f'- {warning}' for warning in result['warnings']]
    if result['skipped']:
        lines += ['', 'Skipped:']
        lines += [f'- {action}: {reason}' for action, reason in result['skipped']]
    if result['source']:
        lines += ['', f'Shortcut source: {result["source"]}']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('template', type=Path)
    parser.add_argument('--os', choices=OS_NAMES)
    parser.add_argument('--profile', type=Path)
    parser.add_argument('--source-json', type=Path, help='Check L1 labels and show physical indices from a Defy JSON')
    parser.add_argument('--format', choices=('markdown', 'json'), default='markdown')
    args = parser.parse_args()
    try:
        profile = read_json(args.profile) if args.profile else None
        os_name = args.os or (profile or {}).get('os')
        if not os_name:
            raise ValueError('Provide --os or --profile')
        result = resolve(read_json(args.template), os_name, profile,
                         read_json(args.source_json) if args.source_json else None)
        print(json.dumps(result, indent=2) if args.format == 'json' else markdown(result))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
