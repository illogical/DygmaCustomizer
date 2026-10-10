# Silver Defy: saved configuration snapshot

This is the latest **saved** Silver Defy configuration found in the supplied backup folder on 2026-10-10. It does not establish that the keyboard is connected now or that its live state is unchanged.

- Automatic backup: `/Users/matt/Drive/Drive/Configs/Dygma/Defy/95945fa4d4f54769/20261010135117-Silver Defy.json` (SHA-256 `756798932b4faf0608866adcc75336a0521160861f0d369c7b3611181b636c0e`)
- Manual export: `/Users/matt/Drive/Drive/Configs/Dygma/2026-08-10_03.json` (SHA-256 `79a124db1f7975986af486a88adff4ec407af348bde68cf5b78d8a58bb97b764`)
- The two files parse to identical JSON. Their byte hashes differ because the formatting differs. Device name: **Silver Defy**; product: **Defy wireless**; Bazecor export version: **v2.2.1**.

## Current layer diagrams

Each SVG shows all 71 physical positions with its L1 reference label, the layer's stored output or numeric code, and a border derived from its saved palette slot where the LED mapping is verified. Hover over a key for the stable `defy:side:rN:cN` position ID and exact keycode. A dashed border means the key-to-LED mapping is unverified. The diagrams represent saved data; they do not test host shortcuts, Superkey gestures, or actual LED appearance.

| Layer | Saved name | Assigned physical keys | Diagram |
| --- | --- | ---: | --- |
| L1 | L1 | 64 | [L1 base layout](silver-defy-20261010-L1.svg) |
| L2 | Arrows & Numbers | 35 | [L2 arrows and numbers](silver-defy-20261010-L2.svg) |
| L3 | Multimedia | 28 | [L3 multimedia](silver-defy-20261010-L3.svg) |
| L4 | App Launcher | 14 | [L4 app launcher](silver-defy-20261010-L4.svg) |
| L5 | L5 | 0 | [L5](silver-defy-20261010-L5.svg) |
| L6 | L6 | 0 | [L6](silver-defy-20261010-L6.svg) |
| L7 | L7 | 0 | [L7](silver-defy-20261010-L7.svg) |
| L8 | L8 | 5 | [L8](silver-defy-20261010-L8.svg) |
| L9 | L9 | 0 | [L9](silver-defy-20261010-L9.svg) |
| L10 | L10 | 0 | [L10](silver-defy-20261010-L10.svg) |

“Assigned” excludes stored `No Key` (0) and `Transparent` (65535). All 71 physical L5, L6, L7, L9, and L10 key positions are transparent. L9 nevertheless has lighting assignments in slots 3, 6, and 15. The keyboard data has 80 serialized key slots and 178 LED slots per layer; those counts must not be mistaken for physical key counts.

## Findings for project planning

- The default layer is stored as index 0 (displayed L1). L1 contains eight references to named Superkeys A, S, D, F, J, K, L, and `;`. L8 references the ninth, named “Space & Hold Cmd.” The backup has nine Superkey definitions and zero named macros. The names and references alone do not verify gesture behavior; inspect their saved maps and Bazecor before editing them.
- L2 stores arrow keys on the L1 S/D/F and E positions, plus a number-pad cluster on the right half. Several other outputs remain numeric in the diagrams because the project's decoder has not verified their names.
- L3 stores media previous/next, play/pause, volume up/down, and mute. It also stores Battery Level (`54108`) at the L1 right top-row outer position (`defy:right:r1:c7`) and Bluetooth Pairing (`54109`) at the L1 right `-` position (`defy:right:r2:c7`).
- L4 stores 11 four-modifier letter chords at L1 E, T, A, S, D, F, Z, C, V, B, and N positions, plus three other nontransparent commands. The backup identifies the layer as “App Launcher,” but it does not identify which applications respond to these chords. Match them against current host shortcuts before giving them app names.
- L8 has five nontransparent keys at L1 S, D, F, G, and Ctrl+Shift+C positions. Its lighting uses all 16 palette slots. The purpose of this unnamed layer is unverified.
- The saved RGBW palette has 16 slots. Slot 15 is `[0, 0, 0, 0]`. The backup has 71 physical key positions, while the existing fixture-backed mapping covers 56 key-to-LED pairs. The remaining 15 positions, mostly lower right, need Bazecor inspection before making per-key lighting claims or edits.
- The repository's `examples/VirtualDefy.json` is a separate virtual example, with a different device description. Do not treat it or the proposed Mac/Omarchy manifests as the current hardware configuration. Use the identified backup above for questions about this saved physical device state.

No input backup, manual export, virtual JSON, or connected keyboard was changed to make these diagrams.
