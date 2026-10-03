---
name: edit-dygma-defy
description: Plan and edit Dygma Defy Bazecor configurations using L1 physical-position references, verified JSON transformations, and separate virtual and connected-keyboard workflows.
---

# Edit Dygma Defy configurations

Work in the DygmaCustomizer project. Start with the JSON file the user names; if none is named, identify the latest verified source and state that choice. Never infer that the virtual keyboard's state matches a connected Defy.

Read `CUSTOMIZATION_GUIDE.md` for choosing a Bazecor feature from natural language. Use virtual files now and a separately verified Bazecor backup/apply workflow when a physical Defy is connected.

For reusable named layers, read `templates/README.md`, the selected template, and a machine profile. `scripts/resolve_template.py` previews one template for macOS, Windows, or Linux; its output is an intent/cheat-sheet manifest, not Bazecor JSON. Resolve L1 labels against the chosen source and check application availability and host shortcuts before encoding.

## Interpret the request

- Layer names in requests are displayed numbers: L1 is stored layer index 0, L4 is index 3.
- Treat an L1 key assignment as a *position reference*, not necessarily as the assignment to copy. “Put `1` on L4” means find the physical position of `1` on L1, then assign `1` there on L4. “Make the L1 `1` position green on L4” changes that position's L4 light, not L1.
- Before editing, inspect the actual source: an L1 label can be duplicated, changed, transparent, or represented by a special keycode. Resolve ambiguity with the user rather than picking an arbitrary position. For non-obvious labels, confirm the keycode against the Bazecor UI or source definitions.
- Determine whether the user wants assignments, colors, or both. Preserve unspecified aspects and other layers.
- Describe layer activation precisely: Layer Shift is active while held; Layer Lock toggles; One Shot Layer applies to the next keypress. A Combo Key can express a key plus modifiers; macros handle sequences/delays. Confirm UI behavior for a proposed trigger before editing its raw keycode.
- Read `PERSONALIZATION.md` if present. It contains user-specific intentions; `PERSONALIZATION.example.md` helps a new user make their own. Preserve cross-platform actions as intent and map their actual shortcuts per OS.
- For macros, ask only for missing behavior that affects implementation: ordered events, delays, app/OS, and repeat behavior. For Superkeys, map requested Tap, Hold, Tap & Hold, 2Tap, and 2Tap & Hold gestures. Leave unspecified gestures unused. Check Dygma's action restrictions and timing options.

## Work with the file

- Prefer the virtual-keyboard JSON path demonstrated here. The working snapshots are in `examples/`, and the tested transformation scripts are in `scripts/`. Confirm the device product is `Defy` and that the `virtual` object has `keymap.custom`, `colormap.map`, and `palette` command entries with space-separated integer `data`. A normal backup uses a different container; do not assume an untested import or transfer path.
- In the tested Defy virtual files, `keymap.custom` contains 80 key positions per layer and `65535` means transparent. Derive the actual layer count from the keymap length and check it before indexing. `colormap.map` stores palette-slot numbers in layer-sized LED blocks; derive LEDs per layer from its total length and the layer count. Verify the requested target layer and all offsets are in range.
- Physical key positions and LEDs are distinct. Use `device.keyboard` to map them. The proven number-row operation maps the first row of `left`/`right` to the corresponding first row of `ledsLeft`/`ledsRight`. The left-side full arrays align. The source has 36 right-side key positions but 35 right-side LEDs, so **do not zip the full right-side arrays or guess a right-side LED** outside a verified row mapping. Investigate Bazecor's mapping or ask for a UI check if a requested position falls there.
- Reuse palette slots for existing colors. Do not alter `palette` when only applying an existing color. `scripts/copy_l1_numbers_to_l4.py` is the proven example for copying L1 assignments and matching colors to another layer; `scripts/customize_trans_key.py` is the proven example for assigning Cmd+S and an existing green to one transparent key. These are narrow examples, not generic editors: inspect their preconditions before adapting them.
- `scripts/defy.py inspect` lists palette RGB(W) slots and use counts. Its copy/move/color commands work on virtual JSON and refuse to overwrite outputs. `copy-keys --colors` supports the verified left-side and right top-row mappings; `set-color --led` is available after checking a different right-side LED in Bazecor. `set-palette` refuses a used slot without `--replace` because every referencing LED changes. A full layer copy/move copies its entire keymap and LED map; moving also clears the source. Do not assume a layer move should rewrite layer-switch keys, default-layer settings, macros, or names.
- Keep semantic color purposes in `PERSONALIZATION.md`; inspect existing usage before assigning a slot. Palette RGB(W) values are global, while colormap slot assignments are per layer. Check color visibility in Bazecor because device rendering and lighting mode can differ.
- Inspect `macros.map`, `superkeys.map`, key references, and related timing commands before changing them. The current scripts do not encode macros or Superkeys. Create a minimal Bazecor example and compare saved commands, then add a reusable script with focused checks if the encoding is confirmed. Names may be stored separately from keyboard data.
- Preserve the complete JSON structure and all unrelated commands. Write a new, descriptively named output file; refuse an existing output path. In particular, leave the user's source and the previously verified outputs untouched.

## Verify and hand off

- Compare input and output at the parsed `keymap.custom` and `colormap.map` integer positions. Confirm only the requested key and/or LED offsets changed, plus any explicitly requested metadata. Check that the JSON still parses and that command lengths are unchanged. Add or run focused tests for any new transformation, then run `python3 -m unittest discover -s scripts -p 'test_*.py' -v` if scripts changed.
- Report the source/output filenames, displayed layers, L1 reference labels, physical positions, LED positions where relevant, and what was preserved. Say which parts were verified in code and which still need a Bazecor visual check.
- For a virtual file, load through Bazecor Keyboard Manager → **Use existing virtual keyboard**, then inspect the target layer in Layout Editor. Bazecor's Save action writes to the selected virtual JSON file. Preferences → Backups → Export Backup may say “No backup found” for virtual keyboards because that searches automatic backups instead. For a connected Defy, first export its current configuration and confirm the device model and firmware. Apply and test through Bazecor, then preserve a verified backup; do not treat virtual loading as a hardware update.
