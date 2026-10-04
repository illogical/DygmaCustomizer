# DygmaCustomizer

Tools and guidance for customizing Dygma keyboards through Bazecor, starting with the Defy. The virtual-keyboard workflow has been checked with a transparent key set to **Cmd+S** and green, and L1's number keys and colors copied to L4. A connected Defy workflow will follow when a keyboard is available.

## Purpose and scope

This repository is a reusable starting point for Defy customization on macOS, Windows, or Linux. The current file workflow uses virtual Defy JSON. When a keyboard is connected, a backup and Bazecor compatibility check will precede applying changes to it. `AGENTS.md` and the [project skill](.agents/skills/edit-dygma-defy/SKILL.md) guide agent work; [CUSTOMIZATION_GUIDE.md](CUSTOMIZATION_GUIDE.md) translates requests into Bazecor features. Reusable actions belong in `templates/`, machine settings in `profiles/`, and layer assignments in a PC initialization manifest. `PERSONALIZATION.md`, when present, is optional private notes rather than a required parallel specification. Confirm actual host shortcuts before encoding them.

Dygma calls the temporary held behavior **Layer Shift**, the toggle behavior **Layer Lock**, and the next-keypress behavior **One Shot Layer**. Dygma describes a One Shot Layer key as shifting on hold and moving to the layer on double tap as well. Templates and manifests describe proposed behavior; a preview or virtual file alone does not change a connected keyboard.

## Start with templates

1. Choose a preserved Defy virtual JSON as the source. The files in `examples/` demonstrate the format; use a fresh export for a particular computer. Give the agent the source path, computer/OS, desired layer actions, and any physical positions in L1 terms. For example: “Using `examples/VirtualDefy.json` and `profiles/windows.example.json`, preview `templates/gaming-fps.json` on a fresh layer; keep Esc as Esc and leave activation undecided.”
2. Select or add a named template in `templates/`. Each action has a stable physical `position_id` plus an L1 label hint. Put reusable OS shortcuts and semantic color categories there. Copy a tracked `profiles/*.example.json` to a private `*.local.json` for installed apps and host-specific shortcut overrides. Check those shortcuts on the computer.
3. Use `scripts/resolve_template.py` for a one-template cheat sheet, then `scripts/apply_template.py preview` for one layer. For a whole PC, copy a `profiles/*-init.example.json` manifest to a private `*.init.local.json`, set its `profile`, displayed layer numbers, navigation roles, and template entries, then use `scripts/apply_template_set.py preview`. Preview is read-only and reports collisions, skipped actions, unverified encodings, and color mapping issues.
4. Choose layer access and a return path before applying. Put Layer Shift, Layer Lock, or One Shot Layer triggers on the base layer as intended; a locked layer needs a route back to L1, while a held Layer Shift returns on release. A One Shot destination generally keeps the trigger position Transparent. The current `layer-navigation.json`, `rare-layer-access.json`, and `layer-return.json` show how to compose these actions with app layers. Keep Esc available where the app or game uses it. Verify the trigger and return encodings in the current Bazecor UI before writing them.
5. When every requested action is supported and the preview is ready, apply to a **distinct output JSON**, compare the changed keys and LEDs, and inspect it in Bazecor through Keyboard Manager → **Use existing virtual keyboard**. Bazecor Save writes the selected virtual file. To change a connected Defy later, export its current backup first, check model/firmware compatibility, then apply and test through Bazecor; loading a virtual JSON alone does not update hardware.

## Reusable JSON command

`scripts/defy.py` reads a Defy **virtual** JSON and writes a distinct output for edits. Displayed layer numbers start at 1; physical positions use underlying indices 0–79, normally identified by the L1 label. Run `inspect` first to see all 16 palette RGB(W) values and their per-layer usage counts. The counts show use, not semantic meaning; record purpose categories in templates and map them to palette slots in each PC manifest.

```sh
python3 scripts/defy.py inspect examples/VirtualDefy.json
python3 scripts/defy.py copy-keys INPUT.json OUTPUT.json --source 1 --target 4 --positions 1 2 3 --colors
python3 scripts/defy.py copy-layer INPUT.json OUTPUT.json --source 1 --target 4
python3 scripts/defy.py move-layer INPUT.json OUTPUT.json --source 4 --target 5 --clear-slot 15
python3 scripts/defy.py set-color INPUT.json OUTPUT.json --target 4 --position 1 --slot 4
python3 scripts/defy.py set-color INPUT.json OUTPUT.json --target 4 --led 36 --slot 4
python3 scripts/defy.py set-palette INPUT.json OUTPUT.json --slot 14 --channels 20 80 255 0
```

The examples show syntax; choose actual paths, positions, and colors after inspecting the source. `copy-keys` copies assignments and optionally matching LED slots. A whole-layer copy copies all 80 key positions and that layer's full LED map; move then clears the source keys to transparent and source LEDs to the requested slot. Existing destination assignments require `--replace`. Changing a used palette slot also requires `--replace` because every LED referring to that slot will change. This command does not rewrite layer-switch keys, macros, default-layer settings, or names; review those when moving a layer. For per-key color edits, the fixture supports the left half and the first three right rows; the third right row follows the contiguous seven-key/seven-LED geometry anchored by its final colored key. Check that row visually in Bazecor. Use `--led` only after checking lower right-side LEDs in Bazecor.

## Named layer templates and machine profiles

[`templates/README.md`](templates/README.md) defines the template format. A template holds stable action names, proposed L1 positions, semantic color categories, and default shortcuts by OS. A profile records one computer's OS, installed apps, and shortcut overrides. A PC manifest lists the template/layer pairs, logical navigation targets, and optional palette-slot meanings. This keeps VS Code's action names and positions portable while allowing Mac, Windows, and Linux to send the shortcuts each host expects. Machine-specific `*.local.json` profiles and manifests are ignored by Git; tracked `*.example.json` files show their structure. Optional `PERSONALIZATION.md` notes can record unresolved personal preferences without duplicating the templates.

```sh
python3 scripts/resolve_template.py templates/vscode.json --os macos --source-json examples/VirtualDefy.json
python3 scripts/resolve_template.py templates/vscode.json --os windows --source-json examples/VirtualDefy.json
python3 scripts/resolve_template.py templates/app-launcher.json --profile profiles/macbook-pro-m5.local.json --source-json examples/VirtualDefy.json
python3 scripts/resolve_template.py templates/omarchy.json --profile profiles/omarchy.example.json --source-json examples/VirtualDefy.json
```

The resolver previews **one template** as a Markdown cheat sheet, or a structured manifest with `--format json`. A template can be a handful of keys merged into an existing layer. Its `position_id` gives a physical Defy half/row/column, including thumb keys; the L1 label remains an easy conversational hint. With `--source-json`, the resolver derives the current key index, warns when a letter or number label changed, and reports when a special-key mnemonic cannot be confirmed from the raw keycode. It reports actions whose apps or shortcuts are absent from the profile. It does not choose the layer where a template is applied, create a Bazecor configuration, or check that a host shortcut actually works. The first VS Code proposal places file search on L1 `F`, settings on `S`, references on `R`, back/forward on adjacent `J`/`K`, and build/debug on `B`/`D`.

For a visual, labeled layer proposal, render one template or every template assigned to a manifest layer with Python's standard library:

```sh
python3 scripts/render_layer_preview.py examples/VirtualDefy.json --template templates/app-launcher.json --profile profiles/macbook-pro-m5.local.json --layer 4 --output /tmp/app-launcher-only.svg
python3 scripts/render_layer_preview.py examples/VirtualDefy.json profiles/macbook-pro-m5-init.local.json --layer 4 --output docs/app-launcher-macbook-pro-m5-L4-centered.svg
```

Open the SVG in a browser. It draws each Defy physical position in a centered, roomy two-half schematic, including two rows of thumb keys, with its L1 reference, proposed action, and resolved shortcut; unassigned positions show the current source layer. Borders use a standard **illustrative purpose palette**, not measured LED RGB(W). Actions mapped to the same palette slot share one preview color, and the legend shows slot-to-purpose meanings. A dashed border means the LED position is unverified; an amber dot points to an issue in the companion Markdown report. The command writes `OUTPUT.md` beside `OUTPUT.svg` by default; use `--report PATH.md` to choose another location. The report lists skipped actions, unsupported encodings, occupied keys, missing slots, template conflicts, and manual checks. Both outputs are proposals; neither changes Bazecor JSON or a keyboard. The script refuses to replace either existing output path. `--policy override` or `--policy fill-empty` changes how overlapping proposed positions are depicted; strict is the default. The [centered L4 diagram](docs/app-launcher-macbook-pro-m5-L4-centered.svg) and [issue report](docs/app-launcher-macbook-pro-m5-L4-centered.md) combine App Launcher and device controls from the Mac manifest.

Additional samples: [`templates/tmux.json`](templates/tmux.json) proposes pane navigation with prefix sequences; [`templates/blender-modeling.json`](templates/blender-modeling.json) and [`templates/blender-view.json`](templates/blender-view.json) separate modeling from Numpad-based viewport control. Their layouts and colors are proposals. Tmux sequences need verified macro handling in Bazecor, and Blender depends on the selected keymap and viewport context. See `templates/README.md` for the rationale and source links.

[`templates/macos-navigation.json`](templates/macos-navigation.json) proposes a small macOS navigation group for desktops, apps, windows, and screenshots. The local Mac profile overrides desktop and screenshot actions with the user's reported shortcuts. Apple's documented defaults are linked in `templates/README.md`.

[`templates/gaming-fps.json`](templates/gaming-fps.json) and [`templates/gaming-rpg.json`](templates/gaming-rpg.json) propose separate Windows gaming layers with left-hand WASD, number slots, modifiers, and Space, plus occasional right-hand arrow and Enter controls. RPG moves inventory and map outputs to the L1 `T` and `G` positions. Their amber/violet identity colors are proposals only; palette slots, activation, and return behavior are undecided. Resolve with `profiles/windows.example.json` and the chosen source before previewing. Several special-key outputs need Bazecor fixtures before the applier can write the full templates; see `templates/README.md`.

To inspect and then apply a partial template to a displayed layer number:

```sh
python3 scripts/apply_template.py preview examples/VirtualDefy.json templates/macos-navigation.json --target 4 --profile profiles/macbook-pro-m5.local.json
python3 scripts/apply_template.py apply INPUT.json TEMPLATE.json --target 4 --profile PROFILE.json
```

Preview and apply include key assignments and mapped colors by default. Use `--keys-only` to preserve LED colors or `--colors-only` to preserve key assignments. Occupied keys stop an apply by default. `--fill-empty` skips an occupied key and its color; `--override` replaces assignments only at template positions; `--replace-layer --baseline CLEAN.json` clears the target layer's selected aspects before applying: keys become transparent (`65535`), and lighting returns to the clean baseline. `--allow-skipped` on the single-template command omits actions without usable host shortcuts. Color application checks slot existence; RGB(W) values are not required.

For the MacBook Pro M5, `profiles/macbook-pro-m5-init.local.json` is the initialization manifest and references `profiles/macbook-pro-m5.local.json` as its machine profile. Follow the [virtual preview and deferred-key guide](docs/macbook-pro-m5-virtual-preview.md). It explains the one remaining manual action, the required LED calibration, and the commands to create a combined output. The manifest reuses existing palette slots and leaves the global RGBW palette unchanged.

For a fresh Defy virtual JSON on this Mac, preview the initialization manifest. It includes navigation on L1, device controls on the primary layer, and return controls where a layer can remain locked:

```sh
python3 scripts/apply_template_set.py preview examples/VirtualDefy.json profiles/macos-init.example.json --keys-only --override
python3 scripts/apply_template_set.py apply INPUT.json PC-MANIFEST.json --keys-only --override --output OUTPUT.json
```

The Mac example manifest maps `primary` to L4 app launcher, `secondary` to L5 VS Code, `tertiary` to L6 macOS navigation, and `base` to L1; L7 is unused. Multiple entries can target one layer and compose in order. `--only-layer N` selects every entry for that displayed layer. The applier can copy Battery Level (`54108`) and Bluetooth Pairing (`54109`) from their verified L1 positions to L4. The L8 fixture and Bazecor code tables support the One Shot Layer L4, Move to L1, Hyper, VS Code, and macOS navigation chord encodings. The requested Superkey gestures still need a saved example. `--defer-unsupported` leaves its keycode unchanged and marks its verified LED red; it refuses an output if that LED is unmapped. Other configured right-side keys can be applied without changing their unverified LEDs.

To revise just L5 in an existing configuration, update L5's template in the manifest, then run:

```sh
python3 scripts/apply_template_set.py preview CURRENT.json PC-MANIFEST.json --only-layer 5 --replace-layer --baseline CLEAN.json
python3 scripts/apply_template_set.py apply CURRENT.json PC-MANIFEST.json --only-layer 5 --replace-layer --baseline CLEAN.json --output UPDATED.json
```

Other layers are preserved. Navigation and return templates describe the selected One Shot Layer, Layer Shift, and Layer Lock behavior. The applier supports the verified One Shot Layer L4 code and blocks other unverified layer actions. No command changes a connected keyboard.

## Bazecor capabilities relevant to this project

Bazecor supports per-layer layouts, per-key lighting, macros, Superkeys, Combo Keys, mouse/media keys, and layer controls. Some functions depend on firmware and device model, so confirm exact encoding in Bazecor before writing raw keycodes. A virtual keyboard can be configured without a connected Defy. Names for layers, macros, and Superkeys may live in Bazecor/backups instead of the keyboard or virtual file; keep meaningful names in templates and preserve a named backup.

For future macro, layer-trigger, device-command, and Superkey work, first capture the desired action and trigger in a template and its target in the PC manifest. A shortcut is appropriate for one key with modifiers; a macro is for ordered events or delays; a Superkey assigns distinct actions to tap, hold, tap and hold, double tap, or double tap and hold. Dygma limits which actions fit each gesture. Compare a small current Bazecor example with a preserved source before adding an encoder. Bazecor can export a single layer or a full backup; a full backup includes macros and Superkeys, while names are stored in Bazecor/backups rather than on the keyboard.

The included virtual snapshot has 10 layers, 80 keymap positions per layer, 178 LED entries per layer, and 16 RGBW palette slots. Those are properties of this snapshot, not a promise that every Defy or Bazecor export has the same sizes. The command derives the layer, LED, and palette counts from each input and rejects unexpected structure. Lighting has a global palette and a per-layer map of slot references. If one palette slot changes, its color changes everywhere that slot is used. Bazecor can also store macros and Superkeys, but their serialized formats need separate validation before this project edits them directly.

Primary references: [Dygma Defy configuration](https://dygma.com/pages/defy-configuration), [Dygma Superkeys guide](https://support.dygma.com/hc/en-us/articles/22652130341277-How-to-configure-Superkeys), [Bazecor repository](https://github.com/Dygmalab/Bazecor), and [Bazecor FOCUS API](https://github.com/Dygmalab/Bazecor/blob/development/FOCUS_API.md).

## Working with an agent

Start a Codex project or chat rooted in this directory so it discovers `AGENTS.md` and the project-scoped `edit-dygma-defy` skill. Ask the agent to select or create a template, name the source JSON and machine profile, preview the target layer or PC manifest, and report any unsupported encoding before applying. For example: “On L4, put the L1 `1` through `0` keys and their colors at the same positions; preview against `examples/VirtualDefy.json` first.” State how the layer is entered and exited. The agent should create a new output JSON only when ready, verify its precise changes, and tell you which file to load in Bazecor. If an L1 label is ambiguous, provide another location cue or confirm the intended key in the UI.

`AGENTS.md` holds short rules that apply to all work in this project. `.agents/skills/edit-dygma-defy/SKILL.md` holds the focused Bazecor editing workflow. `scripts/defy.py` handles supported key, layer, and color operations; the older scripts remain checked examples. Configuration snapshots live in `examples/`. Add or adapt scripts when a repeated transformation warrants it.

## Existing virtual example

`scripts/customize_trans_key.py` reads a Bazecor **virtual keyboard file** or standard backup, changes one **left-half** transparent key on Layer 2, and writes a **new** JSON file. It chooses a transparent key whose LED is not already green when possible. It preserves every other key, color, and setting in the input. It will refuse to overwrite an existing output file. This example stays on the left because the current Defy configuration lists one more right-side key position than right-side LEDs; their pairing needs further investigation.

Requirements: Python 3; no third-party packages. This version is for Bazecor's Defy JSON format, with 80 key positions per layer. The generated layout has not yet been tested on a connected keyboard.

## Try it in Bazecor

The source is `examples/VirtualDefy.json`. The script leaves it untouched and creates `examples/VirtualDefy-green-cmd-s.json`. In this source, the selected test key is on Layer 2 at underlying key position 67 (left half), with LED 30.

1. Go to Bazecor's Keyboard Manager and choose **Use existing virtual keyboard** (the option for loading a virtual keyboard from a JSON file).
2. Select `/Users/matt/dev/projects/DygmaCustomizer/examples/VirtualDefy-green-cmd-s.json`.
3. Open Layer 2 in the Layout Editor. Inspect the key and its green lighting. If you do more editing inside Bazecor, its Save action will update the selected virtual JSON file.
4. To return to the source state, load `examples/VirtualDefy.json` using the same virtual keyboard picker.

To generate another copy from the same source, run:

   ```sh
   cd /Users/matt/dev/projects/DygmaCustomizer
   python3 scripts/customize_trans_key.py examples/VirtualDefy.json examples/another-test.json
   ```

The script prints the chosen layer, key position, LED number, and color slot. Choose an unused output filename each time.

## L1 number row on L4

`scripts/copy_l1_numbers_to_l4.py` uses L1 as a reference: it finds the ten number keys (1–0), then copies their key assignments and matching LED color slots to those same positions on L4. It checks that the L4 destination keys are transparent before changing anything.

The current result is `examples/VirtualDefy-L4-numbers.json`, generated from `examples/VirtualDefy-green-cmd-s.json`. Load it through **Use existing virtual keyboard** in Bazecor's Keyboard Manager, then inspect L4. The previous Cmd+S test on L2 remains in this file.

To regenerate with a different source or output name:

```sh
python3 scripts/copy_l1_numbers_to_l4.py examples/VirtualDefy-green-cmd-s.json examples/another-l4-test.json
```

The L1-reference convention and its safety checks are now captured in the project skill.

To target a particular transparent key on the left half, add `--layer N --key-index P`. `N` is the displayed layer number (1–10); `P` is Bazecor's underlying key position (0–79). The script rejects a position that is not a left-side physical transparent key on that layer.

Bazecor's **Preferences → Backups → Export Backup** searches the automatic backup folder. Virtual keyboards save their state to their own JSON file instead, so Export can show “No backup found” even when the virtual keyboard exists. The script writes a separate virtual JSON file; loading that file through the Keyboard Manager is the step that makes Bazecor show the changes. Before applying changes to a connected Defy, export and preserve its current configuration, then verify the appropriate Bazecor import/apply flow for its firmware.

## Format notes

Bazecor stores key assignments in `keymap.custom`, lighting assignments in `colormap.map`, and RGB/RGBW colors in `palette`. A virtual file has these under `virtual`; a backup has them under `backup`. `65535` is a transparent key. `4118` is the Bazecor keycode for OS/GUI + S, which maps to Cmd+S on macOS. The key and LED position lists inside the Defy configuration connect each physical key to its light.

References: [Bazecor FOCUS API](https://github.com/Dygmalab/Bazecor/blob/development/FOCUS_API.md), [Bazecor letter keycodes](https://github.com/Dygmalab/Bazecor/blob/development/src/api/keymap/db/letters.ts), and [Dygma's backup instructions](https://support.dygma.com/hc/en-us/articles/28094167317405-One-half-of-my-keyboard-doesn-t-turn-on).
