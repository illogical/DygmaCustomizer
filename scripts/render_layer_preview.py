#!/usr/bin/env python3
"""Render a proposed Defy layer from one template or a PC manifest as SVG."""

import argparse
import copy
import html
import json
import math
from pathlib import Path

from apply_template import plan
from defy import KEYS, led_map, model
from resolve_template import l1_positions, physical_position, read_json, resolve

ROOT = Path(__file__).resolve().parents[1]
CELL_W, CELL_H, GAP = 174, 118, 14
SIDE_W = 7 * (CELL_W + GAP) - GAP
LEFT_X, RIGHT_X = 70, 70 + SIDE_W + 200
TOP_Y = 245
WIDTH = RIGHT_X + SIDE_W + LEFT_X
THUMB_TOP_Y = TOP_Y + 4 * (CELL_H + GAP) + 20
THUMB_BOTTOM_Y = THUMB_TOP_Y + CELL_H + GAP + 8
FOOT_Y = THUMB_BOTTOM_Y + CELL_H + 45

# Illustrative swatches, intentionally independent of the source RGB(W) values.
PURPOSE_COLORS = {
    'activation': '#aa8cf1', 'app': '#57d4bd', 'system': '#f2a66b',
    'navigation': '#76b7f4', 'search': '#e8c76f', 'run': '#95d886',
    'destructive': '#ef8189', 'workspace': '#b19af2', 'capture': '#e6a6dc',
    'create': '#8fd5a5', 'view': '#8cc9df', 'session': '#d5ac89',
    'mode': '#b6b8ee', 'movement': '#7fd7ce', 'action': '#e2b38d',
    'quick-slot': '#dcc479', 'modifier': '#b1a4ef', 'menu': '#86bce5',
    'transform': '#d5a5e8', 'mesh': '#a3cf92',
}
FALLBACK_COLORS = ('#78bfd5', '#d1b77b', '#b2d18e', '#c4a9df', '#e4a8aa')


def esc(value):
    return html.escape(str(value), quote=True)


def label_for_code(code):
    if code == 65535:
        return 'Transparent'
    if 4 <= code <= 29:
        return chr(65 + code - 4)
    if 30 <= code <= 38:
        return str(code - 29)
    if code == 39:
        return '0'
    return {40: 'Enter', 41: 'Esc', 42: 'Backspace', 43: 'Tab',
            44: 'Space', 45: '-', 46: '=', 47: '[', 48: ']',
            49: '\\', 51: ';', 52: "'", 54: ',', 55: '.',
            56: '/'}.get(code, f'code {code}')


def short_action(row):
    if (row.get('bazecor_action') or {}).get('type') == 'transparent':
        return 'Pass through'
    name = row['name']
    return name[7:] if name.startswith('Launch ') else name


def title_lines(title, max_chars=17, max_lines=3):
    """Fit a key title; SVG tooltips keep its complete wording."""
    words = []
    for word in title.split():
        words.extend(word[i:i + max_chars] for i in range(0, len(word), max_chars))
    lines = []
    for word in words:
        if lines and len(lines[-1]) + 1 + len(word) <= max_chars:
            lines[-1] += ' ' + word
        else:
            lines.append(word)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:max_chars - 1].rstrip() + '…'
    return lines or ['']


def key_origin(side, row_number, column, base_x):
    if row_number < 5:
        return base_x + (column - 1) * (CELL_W + GAP), TOP_Y + (row_number - 1) * (CELL_H + GAP)
    # Bazecor thumb IDs run around each fan, not left-to-right by index.
    # Screenshot: left top c1..c4, bottom c8..c5; right top c5..c8, bottom c4..c1.
    if side == 'left':
        screen_column, y = (column - 1, THUMB_TOP_Y) if column <= 4 else (8 - column, THUMB_BOTTOM_Y)
        return LEFT_X + 3 * (CELL_W + GAP) + screen_column * (CELL_W + GAP), y
    screen_column, y = (column - 5, THUMB_TOP_Y) if column >= 5 else (4 - column, THUMB_BOTTOM_Y)
    return RIGHT_X - 50 + screen_column * (CELL_W + GAP), y


def shortcut_text(row, profile):
    shortcut = row.get('shortcut')
    if shortcut:
        if isinstance(shortcut, list):
            return ' → '.join(shortcut)
        prefix = '+'.join(profile.get('hyper_modifiers', [])) + '+'
        return 'Hyper+' + shortcut[len(prefix):] if prefix != '+' and shortcut.startswith(prefix) else shortcut
    action = row.get('bazecor_action') or {}
    return {'transparent': 'Pass through', 'device-command': 'Device command'}.get(
        action.get('type'), action.get('type', ''))


def svg_text(x, y, value, size, color, weight=400):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-weight="{weight}">{esc(value)}</text>')


def category_color(category):
    return PURPOSE_COLORS.get(category, FALLBACK_COLORS[sum(map(ord, category)) % len(FALLBACK_COLORS)])


def binding_index(source, binding, positions):
    position_id = binding.get('position_id')
    if position_id:
        index = physical_position(source, position_id)
        if not 0 <= index < KEYS:
            raise ValueError(f'Position ID outside Defy keymap: {position_id}')
        return index
    label = binding['position_l1']
    indices = positions.get(label, [])
    if len(indices) != 1:
        raise ValueError(f'L1 label {label} is missing or ambiguous in source')
    return indices[0]


def checked_led_map(source, manifest):
    mapping = led_map(source)
    overrides = manifest.get('verified_leds', {})
    if not isinstance(overrides, dict):
        raise ValueError('manifest.verified_leds must be an object')
    _, _, _, led_count, _, _ = model(source)
    for key, led in overrides.items():
        if not isinstance(key, str) or not key.isdecimal() or type(led) is not int:
            raise ValueError('Invalid verified LED mapping')
        index = int(key)
        if not 0 <= index < KEYS or not 0 <= led < led_count:
            raise ValueError('Verified LED mapping is out of range')
        if index in mapping and mapping[index] != led:
            raise ValueError('Verified LED mapping conflicts with source geometry')
        if led in mapping.values() and mapping.get(index) != led:
            raise ValueError('Verified LED mapping reuses another key LED')
        mapping[index] = led
    if len(set(mapping.values())) != len(mapping):
        raise ValueError('Verified LED mappings reuse an LED')
    return mapping


def collect(source, manifest, profile, layer_number, template_loader, policy='strict'):
    _, arrays, layer_count, _, _, slots = model(source)
    if not 1 <= layer_number <= layer_count:
        raise ValueError(f'L{layer_number} is absent from source')
    if policy not in ('strict', 'override', 'fill-empty'):
        raise ValueError(f'Unknown preview policy: {policy}')
    entries = [entry for entry in manifest['layers'] if entry['layer'] == layer_number]
    if not entries:
        raise ValueError(f'L{layer_number} is absent from manifest')
    local_profile = copy.deepcopy(profile)
    local_profile['layer_targets'] = {**profile.get('layer_targets', {}), **manifest.get('layer_targets', {})}
    positions = l1_positions(source)
    leds = checked_led_map(source, manifest)
    target = arrays['keymap.custom'][(layer_number - 1)*KEYS:layer_number*KEYS]
    proposed, all_items, notes, names = {}, [], [], []
    for entry in entries:
        template = copy.deepcopy(template_loader(entry['template']))
        names.append(template['name'])
        template['color_slots'] = entry.get('color_slots', template.get('color_slots', {}))
        resolved = resolve(template, local_profile['os'], local_profile, source)
        report = plan(source, template, local_profile, layer_number, with_colors=False, source=source)
        report_rows = {row['id']: row for row in report['rows']}
        resolved_rows = {row['id']: row for row in resolved['bindings']}
        skipped = dict(resolved['skipped'])
        notes.extend(report['warnings'])
        for binding in template['bindings']:
            index = binding_index(source, binding, positions)
            raw = report_rows.get(binding['id'], {})
            resolved_row = resolved_rows.get(binding['id'], {})
            category = binding['color_category']
            slot_map = template['color_slots']
            if not isinstance(slot_map, dict):
                raise ValueError('template.color_slots must be an object')
            matches = [int(slot) for slot, purpose in slot_map.items()
                       if purpose == category and str(slot).isdecimal() and 0 <= int(slot) < slots]
            slot = matches[0] if len(matches) == 1 else None
            problems = []
            if binding['id'] in skipped:
                problems.append('Skipped: ' + skipped[binding['id']])
            if raw.get('unsupported'):
                problems.append('Unsupported: ' + raw['unsupported'])
            if slot is None:
                problems.append('Palette slot unset or invalid')
            led_unverified = index not in leds
            if led_unverified:
                problems.append('LED position unverified')
            occupied = target[index] != 65535 and target[index] != raw.get('after_keycode')
            if occupied and policy == 'strict':
                problems.append('Occupied source key')
            if occupied and policy == 'fill-empty':
                problems.append('Skipped: occupied source key')
            item = {'id': binding['id'], 'template': template['id'], 'name': binding['name'],
                    'l1_label': binding['position_l1'], 'position_index': index,
                    'color_category': category, 'slot': slot,
                    'shortcut': resolved_row.get('shortcut'),
                    'bazecor_action': resolved_row.get('bazecor_action', binding.get('bazecor_action')),
                    'led_unverified': led_unverified, 'problems': problems}
            all_items.append(item)
            if index in proposed:
                previous = proposed[index]
                if policy == 'override':
                    previous['problems'].append('Replaced by later template: ' + item['name'])
                    proposed[index] = item
                    item['other_actions'] = [previous['name']]
                elif policy == 'fill-empty':
                    item['problems'].append('Skipped: position already proposed by ' + previous['name'])
                    previous.setdefault('other_actions', []).append(item['name'])
                else:
                    problem = 'Template conflict: ' + previous['name'] + ' / ' + item['name']
                    previous['problems'].append(problem)
                    item['problems'].append(problem)
                    previous.setdefault('other_actions', []).append(item['name'])
            else:
                proposed[index] = item
    slot_purposes = {}
    for item in all_items:
        if item['slot'] is not None:
            slot_purposes.setdefault(item['slot'], [])
            if item['color_category'] not in slot_purposes[item['slot']]:
                slot_purposes[item['slot']].append(item['color_category'])
    slot_colors = {slot: category_color(purposes[0]) for slot, purposes in slot_purposes.items()}
    for slot, purposes in slot_purposes.items():
        if len(purposes) > 1:
            notes.append(f'Slot {slot} has conflicting purposes: ' + ', '.join(purposes))
    for item in all_items:
        item['color'] = slot_colors[item['slot']] if item['slot'] is not None else category_color(item['color_category'])
    return {'items': proposed, 'all_items': all_items, 'notes': notes, 'names': names,
            'profile': local_profile, 'target': target, 'slot_purposes': slot_purposes,
            'slot_colors': slot_colors}


def report_lines(data):
    return [(item, problem) for item in data['all_items'] for problem in item['problems']]


def md_cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def render_report(data, source_path, selection_path, profile_path, layer_number):
    """Record blockers and checks separately from the visual diagram."""
    issues = report_lines(data)
    lines = [f'# L{layer_number} Defy preview report', '',
             'This is a proposed layout. No Bazecor JSON or keyboard was changed.', '',
             f'- Source: `{source_path}`', f'- Template or manifest: `{selection_path}`',
             f'- Profile: `{profile_path}`',
             f'- Actions: {len(data["all_items"])}',
             f'- Action issues: {len(issues)}', '',
             '## Blockers and manual checks', '']
    if issues:
        lines += ['| L1 position | Action | Issue |', '| --- | --- | --- |']
        for item, problem in issues:
            lines.append(f'| {md_cell(item["l1_label"])} (`{item["position_index"]}`) | '
                         f'{md_cell(item["template"] + "." + item["id"])} | {md_cell(problem)} |')
    else:
        lines.append('None identified by the script.')
    if data['notes']:
        lines += ['', '## Position and palette notes', '']
        lines += [f'- {note}' for note in data['notes']]
    lines += ['', 'Check host shortcuts and the intended behavior in Bazecor before applying a virtual configuration.']
    return '\n'.join(lines) + '\n'


def render(source, manifest, profile, layer_number, template_loader, policy='strict', prepared=None):
    data = prepared or collect(source, manifest, profile, layer_number, template_loader, policy)
    items, target, local_profile = data['items'], data['target'], data['profile']
    categories_without_slots = sorted({item['color_category'] for item in data['all_items'] if item['slot'] is None})
    legend = [(f'Slot {slot}: ' + ', '.join(purposes), data['slot_colors'][slot])
              for slot, purposes in sorted(data['slot_purposes'].items())]
    legend += [(f'{category}: slot unset', category_color(category)) for category in categories_without_slots]
    legend_y = FOOT_Y + 130
    height = legend_y + math.ceil(len(legend) / 3) * 36 + 36
    keyboard = source['device']['keyboard']
    l1 = model(source)[1]['keymap.custom'][:KEYS]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
             f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Proposed Defy L{layer_number} layer preview">',
             '<style>text{font-family:Inter,Arial,sans-serif}.key{rx:15;stroke-width:3}</style>',
             f'<rect width="{WIDTH}" height="{height}" fill="#101725"/>',
             svg_text(70, 78, f'L{layer_number} · ' + ' + '.join(data['names']), 40, '#f4f7ff', 700),
             svg_text(70, 116, f'{manifest["id"]} · {profile["id"]}', 20, '#aab9d1'),
             svg_text(70, 152, 'Proposed diagram · preview colors · source JSON and keyboard unchanged', 20, '#fbbf75'),
             svg_text(LEFT_X, 213, 'LEFT HALF', 19, '#9aafcc', 700),
             svg_text(RIGHT_X, 213, 'RIGHT HALF', 19, '#9aafcc', 700)]
    for side, base_x in (('left', LEFT_X), ('right', RIGHT_X)):
        for row_number, indices in enumerate(keyboard[side], 1):
            for column, index in enumerate(indices, 1):
                x, y = key_origin(side, row_number, column, base_x)
                item = items.get(index)
                fill, stroke = ('#263747', item['color']) if item else ('#1b2434', '#42536b')
                if not item and target[index] != 65535:
                    fill, stroke = '#30354c', '#8b9db9'
                position_id = f'defy:{side}:r{row_number}:c{column}'
                description = item['name'] if item else label_for_code(target[index])
                notes = item['problems'] + item.get('other_actions', []) if item else []
                tooltip = position_id + ': ' + description + ('; ' + '; '.join(notes) if notes else '')
                dash = '7 5' if item and item['led_unverified'] else 'none'
                parts.append(f'<rect class="key" x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" '
                             f'fill="{fill}" stroke="{stroke}" stroke-dasharray="{dash}">'
                             f'<title>{esc(tooltip)}</title></rect>')
                hint = item['l1_label'] if item else label_for_code(l1[index])
                parts.append(svg_text(x + 11, y + 22, 'L1 ' + hint[:18], 15, '#b9c8d9', 600))
                if item:
                    lines = title_lines(short_action(item))
                    title_size, title_y, title_step = (18, 52, 22) if len(lines) <= 2 else (15, 44, 18)
                    for line_number, line in enumerate(lines):
                        parts.append(svg_text(x + 11, y + title_y + line_number*title_step,
                                              line, title_size, '#f4f8fb', 650))
                    shortcut = shortcut_text(item, local_profile)
                    parts.append(svg_text(x + 11, y + 103, shortcut[:17] + ('…' if len(shortcut) > 17 else ''),
                                          14, '#8ce4e8'))
                    if item['problems']:
                        parts.append(f'<circle cx="{x + CELL_W - 12}" cy="{y + 12}" r="6" fill="#fbbf75"/>')
                else:
                    parts.append(svg_text(x + 11, y + 60,
                                          label_for_code(target[index]) if target[index] != 65535 else '—',
                                          19, '#afbdd0'))
                    parts.append(svg_text(x + 11, y + 104, 'Current L' + str(layer_number), 13, '#7588a2'))
    parts += [svg_text(70, FOOT_Y, 'Colored borders: illustrative purpose groups', 18, '#9fe6c5', 600),
              svg_text(620, FOOT_Y, 'Dashed: LED position unverified', 18, '#ffca8d', 600),
              svg_text(1110, FOOT_Y, 'Amber dot: see Markdown report', 18, '#ffca8d', 600),
              svg_text(70, FOOT_Y + 36, 'Hyper = ' + ' + '.join(profile.get('hyper_modifiers', [])) +
                       ' · Shortcuts come from the machine profile', 17, '#aab9d1'),
              svg_text(70, FOOT_Y + 70,
                       f'{len(data["all_items"])} template actions · {len(report_lines(data)) + len(data["notes"])} report items · no Bazecor JSON created',
                       17, '#aab9d1'),
              svg_text(70, legend_y - 18, 'Preview colors by purpose and palette slot', 18, '#f4f7ff', 700)]
    for number, (label, color) in enumerate(legend):
        col, row = number % 3, number // 3
        x, y = 70 + col * 790, legend_y + row * 36
        parts.append(f'<rect x="{x}" y="{y - 15}" width="20" height="20" rx="5" fill="{color}"/>')
        parts.append(svg_text(x + 31, y, label, 16, '#cdd8e8'))
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('manifest', type=Path, nargs='?', help='PC manifest (legacy positional form)')
    parser.add_argument('--template', type=Path, help='Render one template instead of a manifest')
    parser.add_argument('--profile', type=Path, help='Required with --template; optional manifest override')
    parser.add_argument('--layer', type=int, required=True, help='Displayed layer number')
    parser.add_argument('--policy', choices=('strict', 'override', 'fill-empty'), default='strict')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, help='Markdown issue report; defaults to the SVG stem plus .md')
    args = parser.parse_args()
    try:
        if (args.manifest is None) == (args.template is None):
            raise ValueError('Provide exactly one PC manifest or --template')
        if args.template and not args.profile:
            raise ValueError('--template requires --profile')
        report_path = args.report or args.output.with_suffix('.md')
        if args.output == report_path:
            raise ValueError('SVG and Markdown report paths must differ')
        for path in (args.output, report_path):
            if path.exists():
                raise ValueError(f'Output already exists: {path}')
        source = read_json(args.source)
        if args.template:
            template = read_json(args.template)
            manifest = {'id': template['id'], 'layers': [{'layer': args.layer, 'template': str(args.template)}]}
            loader = lambda _path: template
            profile_path = args.profile
        else:
            manifest = read_json(args.manifest)
            loader = lambda path: read_json(ROOT / path)
            profile_path = args.profile or ROOT / manifest['profile']
        profile = read_json(profile_path)
        data = collect(source, manifest, profile, args.layer, loader, args.policy)
        svg = render(source, manifest, profile, args.layer, loader, args.policy, prepared=data)
        report = render_report(data, args.source, args.template or args.manifest, profile_path, args.layer)
        created = []
        try:
            for path, content in ((args.output, svg), (report_path, report)):
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('x', encoding='utf-8') as file:
                    created.append(path)
                    file.write(content)
        except OSError:
            for path in created:
                path.unlink(missing_ok=True)
            raise
        print(args.output)
        print(report_path)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
