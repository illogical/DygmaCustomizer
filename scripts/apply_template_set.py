#!/usr/bin/env python3
"""Preview or apply a PC manifest of Defy templates to one virtual JSON."""

import argparse
import copy
import json
from pathlib import Path

from apply_template import apply, plan, print_report, reset_layer
from customize_trans_key import command_entry
from defy import KEYS, led_map, model
from resolve_template import read_json

ROOT = Path(__file__).resolve().parents[1]


def compose(source, baseline, manifest, profile, load_template, only_layer=None,
            with_keys=True, with_colors=True, policy='strict', defer_unsupported=False):
    if manifest.get('schema_version') != 1 or not manifest.get('id') or not isinstance(manifest.get('layers'), list) or not manifest['layers']:
        raise ValueError('Expected manifest schema version 1 with id and nonempty layers')
    if policy not in ('strict', 'fill-empty', 'override', 'replace-layer'):
        raise ValueError(f'Unknown apply policy: {policy}')
    if policy == 'fill-empty' and not with_keys:
        raise ValueError('fill-empty requires key assignments')
    if defer_unsupported and not (with_keys and with_colors):
        raise ValueError('Deferred preview requires keys and colors')
    model(source)
    verified_leds = manifest.get('verified_leds', {})
    if not isinstance(verified_leds, dict):
        raise ValueError('manifest.verified_leds must map key indices to LED indices')
    mapping = {}
    for key, led in verified_leds.items():
        if not isinstance(key, str) or not key.isdecimal() or type(led) is not int:
            raise ValueError('Invalid verified LED mapping')
        mapping[int(key)] = led
    _, _, _, led_count, _, slot_count = model(source)
    known_leds = led_map(source)
    for key, led in mapping.items():
        if not 0 <= key < KEYS or not 0 <= led < led_count:
            raise ValueError('Verified LED mapping is out of range')
        if key in known_leds and known_leds[key] != led:
            raise ValueError('Verified LED mapping conflicts with source geometry')
        if led in known_leds.values() and known_leds.get(key) != led:
            raise ValueError('Verified LED mapping reuses another key LED')
    red_slot = manifest.get('deferred_red_slot')
    if defer_unsupported and (type(red_slot) is not int or not 0 <= red_slot < slot_count):
        raise ValueError('Manifest needs a valid deferred_red_slot')
    if policy == 'replace-layer':
        model(baseline)
    layer_targets = manifest.get('layer_targets', {})
    if not isinstance(layer_targets, dict):
        raise ValueError('manifest.layer_targets must map logical destinations to displayed layers')
    profile = copy.deepcopy(profile)
    profile_targets = profile.get('layer_targets', {})
    if not isinstance(profile_targets, dict):
        raise ValueError('profile.layer_targets must map logical destinations to displayed layers')
    profile['layer_targets'] = {**profile_targets, **layer_targets}
    selected = []
    for entry in manifest['layers']:
        if not isinstance(entry, dict) or type(entry.get('layer')) is not int or not isinstance(entry.get('template'), str) or not entry['template']:
            raise ValueError('Each manifest layer needs an integer layer and template path')
        number = entry['layer']
        if only_layer is None or only_layer == number:
            selected.append(entry)
    if not selected:
        raise ValueError(f'Layer L{only_layer} is not listed in manifest')

    reports = []
    blockers = []
    output = copy.deepcopy(source)
    reset_layers = set()
    for entry in selected:
        number = entry['layer']
        try:
            template = copy.deepcopy(load_template(entry['template']))
            if 'color_slots' in entry:
                template['color_slots'] = entry['color_slots']
            if policy == 'replace-layer' and number not in reset_layers:
                reset_layer(output, baseline, number, with_keys, with_colors)
                reset_layers.add(number)
            report = plan(output, template, profile, number, with_keys, with_colors,
                          fill_empty=(policy == 'fill-empty'), source=source,
                          led_overrides=mapping if defer_unsupported else None,
                          allow_unmapped_colors=defer_unsupported)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            blockers.append(f'L{number} {entry["template"]}: {error}')
            continue
        reports.append(report)
        prefix = f'L{number} {template["id"]}'
        blockers += [f'{prefix}: skipped {action}: {reason}' for action, reason in report['skipped']]
        deferred = []
        for row in report['rows']:
            if not row.get('unsupported') or row.get('skipped_occupied'):
                continue
            if defer_unsupported and with_keys and 'after_keycode' not in row:
                if 'led_index' not in row:
                    blockers.append(f'{prefix}: deferred {row["id"]} has no verified LED mapping')
                else:
                    row['deferred'] = True
                    deferred.append(row)
            else:
                blockers.append(f'{prefix}: unsupported {row["id"]}: {row["unsupported"]}')
        if policy == 'strict':
            blockers += [f'{prefix}: occupied {row["id"]} at index {row["position_index"]}'
                         for row in report['rows'] if row['collision']]
        report_blocked = (
            bool(report['skipped']) or
            any(row.get('unsupported') and not row.get('deferred') and not row.get('skipped_occupied') for row in report['rows']) or
            any(row.get('unsupported') and 'led_index' not in row for row in report['rows']) or
            (policy == 'strict' and any(row['collision'] for row in report['rows']))
        )
        if not report_blocked:
            ready = {**report, 'rows': [row for row in report['rows'] if not row.get('deferred')]}
            if ready['rows']:
                apply(output, ready, override=(policy == 'override'))
            if deferred:
                entry = command_entry(output, 'colormap.map')
                colors = model(output)[1]['colormap.map']
                for row in deferred:
                    colors[(number - 1) * led_count + row['led_index']] = red_slot
                entry['data'] = ' '.join(map(str, colors))
    if blockers:
        return None, reports, blockers
    return output, reports, []


def verify_changes(source, output, layers):
    probe = copy.deepcopy(source)
    _, before, count, leds, _, _ = model(source)
    _, after, after_count, after_leds, _, _ = model(output)
    if (count, leds) != (after_count, after_leds):
        raise ValueError('Output layer dimensions changed')
    for name, stride in (('keymap.custom', KEYS), ('colormap.map', leds)):
        for index, (old, new) in enumerate(zip(before[name], after[name])):
            if old != new and index // stride + 1 not in layers:
                raise ValueError(f'Unexpected {name} change outside selected layers')
        command_entry(probe, name)['data'] = command_entry(output, name)['data']
    if probe != output:
        raise ValueError('Unexpected JSON change outside keymap and colormap')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for name in ('preview', 'apply'):
        cmd = sub.add_parser(name)
        cmd.add_argument('input', type=Path)
        cmd.add_argument('manifest', type=Path)
        cmd.add_argument('--profile', type=Path, help='Override profile path in manifest')
        cmd.add_argument('--only-layer', type=int, help='Update only this displayed layer')
        features = cmd.add_mutually_exclusive_group()
        features.add_argument('--keys-only', action='store_true')
        features.add_argument('--colors-only', action='store_true')
        policies = cmd.add_mutually_exclusive_group()
        policies.add_argument('--fill-empty', action='store_true')
        policies.add_argument('--override', action='store_true')
        policies.add_argument('--replace-layer', action='store_true')
        cmd.add_argument('--baseline', type=Path, help='Clean export required with --replace-layer')
        cmd.add_argument('--defer-unsupported', action='store_true',
                         help='Leave unknown keycodes unchanged and mark their verified LEDs red')
        if name == 'apply':
            cmd.add_argument('--output', type=Path, help='Distinct output path')
    args = parser.parse_args()
    try:
        manifest = read_json(args.manifest)
        profile_path = args.profile or (ROOT / manifest['profile'])
        profile = read_json(profile_path)
        source = read_json(args.input)
        if args.replace_layer != bool(args.baseline):
            raise ValueError('--replace-layer requires --baseline, and --baseline requires --replace-layer')
        baseline = read_json(args.baseline) if args.baseline else source
        policy = ('fill-empty' if args.fill_empty else 'override' if args.override else
                  'replace-layer' if args.replace_layer else 'strict')
        output_doc, reports, blockers = compose(
            source, baseline, manifest, profile,
            lambda path: read_json(ROOT / path), args.only_layer,
            with_keys=not args.colors_only, with_colors=not args.keys_only,
            policy=policy, defer_unsupported=args.defer_unsupported)
        for report in reports:
            print_report(report)
        if blockers:
            print(f'Blocked: {len(blockers)} issue(s); no output created')
            for reason in blockers:
                print(f'  {reason}')
            if args.action == 'apply':
                return 1
            return 0
        deferred = [(report['target_layer'], row) for report in reports
                    for row in report['rows'] if row.get('deferred')]
        for number, row in deferred:
            print(f"  DEFERRED L{number} {row['id']} at {row['position_id']}: "
                  f"{row['unsupported']}; LED {row['led_index']} → slot {manifest['deferred_red_slot']}")
        print(f'Ready: {len(deferred)} deferred action(s) marked red' if deferred else
              'Ready: all requested layers can be applied')
        if args.action == 'preview':
            return 0
        output = args.output or args.input.with_name(f'{args.input.stem}-{manifest["id"]}.json')
        if output.resolve() in (args.input.resolve(), args.manifest.resolve()):
            raise ValueError('Output must differ from input and manifest')
        verify_changes(source, output_doc, {report['target_layer'] for report in reports})
        with output.open('x', encoding='utf-8') as file:
            json.dump(output_doc, file, indent=2, ensure_ascii=False)
            file.write('\n')
        print(f'Created {output}')
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
