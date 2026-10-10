#!/usr/bin/env python3
"""Draw stored physical Defy layers from a preserved Bazecor device backup."""

import argparse
import hashlib
import html
import json
from pathlib import Path

from customize_trans_key import command_entry, numbers
from defy import KEYS, led_map
from query_layout import output_name
from render_layer_preview import CELL_H, CELL_W, FOOT_Y, LEFT_X, RIGHT_X, WIDTH, key_origin


def backup_data(doc):
    if 'backup' not in doc or doc.get('neuron', {}).get('device', {}).get('info', {}).get('product') != 'Defy':
        raise ValueError('Expected a Defy device backup')
    device = doc['neuron']['device']
    commands = {name: numbers(command_entry(doc, name), name)
                for name in ('keymap.custom', 'colormap.map', 'palette')}
    keys, colors, palette = (commands[name] for name in commands)
    layers = doc['neuron']['layers']
    if len(keys) != len(layers) * KEYS or not layers or len(colors) % len(layers):
        raise ValueError('Backup layer lengths are inconsistent')
    led_count = len(colors) // len(layers)
    width = 4 if device.get('RGBWMode') else 3
    if len(palette) % width or not palette:
        raise ValueError('Invalid palette length')
    slots = len(palette) // width
    if any(not 0 <= slot < slots for slot in colors):
        raise ValueError('Colormap references a missing palette slot')
    geometry = device['keyboard']
    indices = [index for side in ('left', 'right') for row in geometry[side] for index in row]
    if len(indices) != 71 or len(set(indices)) != 71 or any(not 0 <= i < KEYS for i in indices):
        raise ValueError('Expected 71 distinct physical Defy positions')
    # The existing geometry helper verifies only the right LEDs established by fixtures.
    mapping = led_map({'device': device})
    return keys, colors, palette, width, led_count, layers, geometry, mapping


def key_name(code, superkeys):
    if code == 0:
        return 'No Key'
    if 53980 <= code < 53980 + len(superkeys):
        entry = next((item for item in superkeys if item.get('id') == code - 53980), None)
        if entry:
            return 'Superkey ' + entry['name'].strip()
    return output_name(code) or f'Code {code}'


def swatch(palette, width, slot):
    channels = palette[slot * width:(slot + 1) * width]
    white = channels[3] if width == 4 else 0
    return '#' + ''.join(f'{min(255, channel + white):02x}' for channel in channels[:3])


def diagram(doc, layer_number, source_name, source_sha):
    keys, colors, palette, width, led_count, layers, geometry, mapping = backup_data(doc)
    if not 1 <= layer_number <= len(layers):
        raise ValueError('Layer is absent from backup')
    layer_name = layers[layer_number - 1]['name']
    l1 = keys[:KEYS]
    start = (layer_number - 1) * KEYS
    used = set()
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{FOOT_Y + 136}" viewBox="0 0 {WIDTH} {FOOT_Y + 136}" role="img" aria-label="Saved Defy L{layer_number} {html.escape(layer_name, quote=True)}">',
             '<style>text{font-family:Inter,Arial,sans-serif}</style>',
             f'<rect width="{WIDTH}" height="{FOOT_Y + 136}" fill="#101725"/>',
             f'<text x="70" y="78" fill="#f4f7ff" font-size="40" font-weight="700">L{layer_number} · {html.escape(layer_name)}</text>',
             f'<text x="70" y="116" fill="#aab9d1" font-size="19">{html.escape(source_name)} · SHA-256 {source_sha[:12]}</text>',
             '<text x="70" y="153" fill="#fbbf75" font-size="18">Stored keycodes · palette colors approximated on screen · dashed border means LED mapping unverified</text>',
             '<text x="70" y="213" fill="#9aafcc" font-size="19" font-weight="700">LEFT HALF</text>',
             f'<text x="{RIGHT_X}" y="213" fill="#9aafcc" font-size="19" font-weight="700">RIGHT HALF</text>']
    for side, base_x in (('left', LEFT_X), ('right', RIGHT_X)):
        for row_number, row in enumerate(geometry[side], 1):
            for column, index in enumerate(row, 1):
                x, y = key_origin(side, row_number, column, base_x)
                code = keys[start + index]
                name = key_name(code, doc['neuron'].get('superkeys', []))
                l1_name = key_name(l1[index], doc['neuron'].get('superkeys', []))
                led = mapping.get(index)
                slot = colors[(layer_number - 1) * led_count + led] if led is not None else None
                if slot is not None:
                    used.add(slot)
                stroke = swatch(palette, width, slot) if slot is not None else '#738396'
                position = f'defy:{side}:r{row_number}:c{column}'
                details = f'{position} | L1 {l1_name} | L{layer_number} {name} ({code})'
                if slot is not None:
                    details += f' | LED {led}, palette slot {slot}'
                else:
                    details += ' | LED mapping unverified'
                dash = ' stroke-dasharray="7 5"' if led is None else ''
                parts.append(f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" rx="15" fill="#263244" stroke="{stroke}" stroke-width="4"{dash}><title>{html.escape(details)}</title></rect>')
                parts.append(f'<text x="{x+10}" y="{y+23}" fill="#b9c8d9" font-size="14">L1 {html.escape(l1_name[:19])}</text>')
                shown = name if len(name) <= 19 else name[:18] + '…'
                parts.append(f'<text x="{x+10}" y="{y+66}" fill="#f4f8fb" font-size="19" font-weight="650">{html.escape(shown)}</text>')
                parts.append(f'<text x="{x+10}" y="{y+104}" fill="#90a5bb" font-size="13">code {code}' + (f' · slot {slot}' if slot is not None else '') + '</text>')
    parts.append(f'<text x="70" y="{FOOT_Y}" fill="#b9c8d9" font-size="18">Palette slots shown: {", ".join(map(str, sorted(used)))} · exact RGBW values remain in the backup</text>')
    parts.append(f'<text x="70" y="{FOOT_Y+35}" fill="#b9c8d9" font-size="18">Transparent means pass through; No Key is a stored keycode. Unknown commands retain their numeric code.</text>')
    parts.append(f'<text x="70" y="{FOOT_Y+70}" fill="#b9c8d9" font-size="18">This is a saved backup snapshot; it does not prove the device is currently connected or unchanged.</text>')
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--layers', type=int, nargs='+', required=True)
    args = parser.parse_args()
    raw = args.backup.read_bytes()
    doc = json.loads(raw)
    outputs = [(args.output_dir / f'silver-defy-20261010-L{n}.svg',
                diagram(doc, n, args.backup.name, hashlib.sha256(raw).hexdigest())) for n in args.layers]
    if any(path.exists() for path, _ in outputs):
        parser.error('Output already exists')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path, content in outputs:
        path.write_text(content, encoding='utf-8')
        print(path)


if __name__ == '__main__':
    main()
