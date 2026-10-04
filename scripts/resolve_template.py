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


def resolve_bazecor_action(action, profile, layer_count=None):
    """Resolve logical layer names while leaving unverified encodings declarative."""
    if not isinstance(action, dict) or not isinstance(action.get('type'), str):
        raise ValueError('bazecor_action must be an object with a type')
    resolved = dict(action)
    action_type = action['type']
    if action_type == 'transparent':
        return resolved
    if action_type in ('one-shot-layer', 'layer-lock', 'layer-shift'):
        target = action.get('target')
        targets = profile.get('layer_targets', {})
        if not isinstance(targets, dict) or target not in targets:
            raise ValueError(f'bazecor_action target {target!r} is missing from profile.layer_targets')
        target_layer = targets[target]
        if type(target_layer) is not int or not 1 <= target_layer <= 10:
            raise ValueError(f'profile.layer_targets.{target} must be a displayed layer from L1 to L10')
        if layer_count is not None and target_layer > layer_count:
            raise ValueError(f'profile.layer_targets.{target} targets L{target_layer}, absent from source')
        resolved['target_layer'] = target_layer
    elif action_type == 'superkey':
        gestures = action.get('gestures')
        if not isinstance(gestures, dict) or not gestures:
            raise ValueError('superkey action needs a nonempty gestures object')
        resolved_gestures = {}
        for gesture, subaction in gestures.items():
            if gesture not in ('tap', 'hold', 'tap_hold', 'double_tap', 'double_tap_hold'):
                raise ValueError(f'unsupported Superkey gesture: {gesture}')
            if not isinstance(subaction, dict) or subaction.get('type') not in ('layer-lock', 'layer-shift'):
                raise ValueError(f'Superkey gesture {gesture} must specify a layer-lock or layer-shift action')
            resolved_gestures[gesture] = resolve_bazecor_action(subaction, profile, layer_count)
        resolved['gestures'] = resolved_gestures
    elif action_type == 'device-command':
        if not isinstance(action.get('command'), str) or not action['command']:
            raise ValueError('device-command action needs a command name')
    else:
        raise ValueError(f'unsupported bazecor_action type: {action_type}')
    return resolved


def resolve(template, os_name, profile=None, source=None, include_without_shortcut=False):
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
    layer_count = None
    if source:
        source_keys = numbers(command_entry(source, 'keymap.custom'), 'keymap.custom')
        layer_count = len(source_keys) // 80
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
                if index in index_labels and current_label != label:
                    warnings.append(f'{action_id}: L1 label changed from {label} to {current_label} at {position_id}')
                elif index not in index_labels:
                    known_labels = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                    if label in known_labels:
                        warnings.append(f'{action_id}: L1 label {label} is not decoded at {position_id} ({current_label})')
                    else:
                        warnings.append(f'{action_id}: cannot confirm mnemonic {label!r} from {position_id} ({current_label})')
            else:
                if len(positions.get(label, [])) != 1:
                    raise ValueError(f'L1 label {label} is missing or ambiguous in source')
                index = positions[label][0]
        required_app = binding.get('requires_app')
        if profile and required_app and required_app not in available_apps:
            skipped.append((action_id, f'{required_app} absent from profile.available_apps'))
            continue
        shortcut = overrides.get(f'{template["id"]}.{action_id}', binding.get('shortcuts', {}).get(os_name))
        action = binding.get('bazecor_action')
        if not shortcut and action is None and not include_without_shortcut:
            skipped.append((action_id, f'no {os_name} shortcut'))
            continue
        row = {'id': action_id, 'name': binding['name'], 'l1_label': label,
               'color_category': binding['color_category'],
               'shortcut': expand_shortcut(shortcut, profile) if shortcut else None}
        if action is not None:
            row['bazecor_action'] = resolve_bazecor_action(action, profile, layer_count)
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
            'source': template.get('source'), 'color_slots': template.get('color_slots', {}),
            'bindings': rows, 'skipped': skipped,
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
        if isinstance(shortcut, list):
            display = ' → '.join(shortcut)
        elif shortcut:
            display = shortcut
        else:
            action = row.get('bazecor_action', {})
            action_type = action.get('type', 'Bazecor action')
            if action_type == 'superkey':
                display = '; '.join(
                    f'{gesture}: {gesture_action["type"]} L{gesture_action["target_layer"]}'
                    for gesture, gesture_action in action['gestures'].items()
                )
            elif 'target_layer' in action:
                display = f'{action_type} L{action["target_layer"]}'
            elif action_type == 'device-command':
                display = action['command']
            else:
                display = action_type
        lines.append(f'| {row["l1_label"]} | {row.get("position_id", "—")} | {row.get("position_index", "—")} | {row["name"]} | {display} | {row["color_category"]} |')
    if result['color_slots']:
        lines += ['', 'Color purposes:']
        lines += [f'- Slot {slot}: {purpose}' for slot, purpose in result['color_slots'].items()]
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
