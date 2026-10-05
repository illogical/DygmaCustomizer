# Glove80 configuration research

Researched 2026-10-04 for the [Glove80 Revision 2 product variant](https://www.moergo.com/collections/glove80-keyboards/products/ship-from-usa-glove80-ergonomic-keyboard-revision-2-with-silent-switches-travel-case?variant=51890653004049). This is a documentation review, not a tested configuration or flash. The linked storefront page was inaccessible to the research browser; the configuration findings below come from MoErgo's documentation and source repositories.

## Answer for this project

The Glove80 is a better candidate for source-driven agent customization than our current Defy/Bazecor virtual-JSON workflow. It runs MoErgo's fork of the open-source ZMK firmware, and MoErgo publishes both the [firmware source](https://github.com/moergo-sc/zmk) and [configuration templates](https://github.com/moergo-sc/glove80-zmk-config). ZMK documents named keycodes and behaviors, so an agent can edit a text keymap, check its diff, and build firmware without discovering opaque Bazecor integer encodings. This is an assessment of the *firmware/configuration path*; the account-based MoErgo Layout Editor is a separate web service, and I found no official claim that its service source is open. [MoErgo's ZMK appendix](https://docs.moergo.com/glove80-user-guide/appendix-zmk/) identifies the fork and traditional build path; [ZMK's keycode reference](https://zmk.dev/docs/keymaps/list-of-keycodes) and [behavior reference](https://zmk.dev/docs/keymaps/behaviors) document the keymap language.

The main tradeoff is deployment. A changed keymap must be compiled to `.uf2` firmware and loaded onto **both halves** through USB bootloader drives. It is not a live remap. With an attached keyboard and host filesystem access, an agent could prepare and validate the files, identify the correct bootloader volumes, and copy the firmware. Someone must put each half in bootloader mode; a reliable physical power-on key combination is documented. A remote agent with no attached Glove80 cannot flash or test the hardware. [MoErgo's loading instructions](https://docs.moergo.com/glove80-user-guide/customizing-key-layout/) give the right-then-left USB procedure and recovery entry method.

## Configuration paths

| Path | Source to edit | Build | Exchange with agent | Practical limit |
| --- | --- | --- | --- | --- |
| [MoErgo Layout Editor](https://docs.moergo.com/layout-editor-guide/introduction/) | Web layout in a MoErgo account | Editor produces one `.uf2` for both halves | Export `.keymap` DTSI or enable experimental JSON backup/import | Requires account and web service; [daily and weekly build limits](https://docs.moergo.com/layout-editor-guide/building-firmware/); JSON format may change |
| [MoErgo Nix configuration template](https://github.com/moergo-sc/glove80-zmk-config) | Versioned ZMK keymap and config files | GitHub Actions or local build tooling | Git repository; normal text diffs | Requires build dependencies or GitHub workflow; produced `glove80.uf2` goes to both halves |
| [MoErgo West configuration template](https://github.com/moergo-sc/glove80-zmk-config-west) | Versioned ZMK keymap and config files | GitHub Actions or West toolchain | Git repository; normal text diffs | Its build gives distinct `glove80_lh-zmk.uf2` and `glove80_rh-zmk.uf2`; match each file to its half |

The editor's [export/import guide](https://docs.moergo.com/layout-editor-guide/advanced-usage-export-import/) explicitly says `.keymap` export supports local compilation and that JSON export can support automated keycode replacement. JSON backup/import must be enabled under **Local Backup and Restore** and is marked experimental, with no guarantee of future import compatibility. This offers a manual export/import route, but the source repository route can eliminate the repeated GUI round trip once a suitable baseline is established.

## Keycodes and behavior expressiveness

ZMK keymaps bind behaviors to positions. Examples from its documentation include `&kp A` for a key press, `&kp LG(S)` for GUI+S, `&mo 1` for a momentary layer, and separate behaviors for toggle and sticky layers. ZMK layers are numbered from zero in source order. [Key press](https://zmk.dev/docs/keymaps/behaviors/key-press), [modifiers](https://zmk.dev/docs/keymaps/modifiers), [layer behaviors](https://zmk.dev/docs/keymaps/behaviors/layers), and [macros](https://zmk.dev/docs/keymaps/behaviors/macros) are documented with examples. Complex sequences still need explicit behavior and timing review, and the actual host/app shortcut must still be verified. The chosen MoErgo firmware version and any Glove80-specific features should be pinned and built before assuming upstream ZMK examples work unchanged.

MoErgo's editor also exposes macros, hold-taps, combos, advanced configuration, and custom ZMK Device-Tree snippets. These can be exported as `.keymap` text for inspection. [Layout editing guide](https://docs.moergo.com/layout-editor-guide/layout-editing/) and [custom Device-Tree guide](https://docs.moergo.com/layout-editor-guide/advanced-usage-custom-device-tree/).

## Individual key lighting

The linked silent-switch product is advertised with [80 RGB LEDs, one beneath each key](https://www.moergo.com/products/ship-from-usa-glove80-ergonomic-keyboard-revision-2-with-silent-switches-travel-case). That is hardware capability, not a promise that the stock software provides Defy-style per-key color assignments. [MoErgo's RGB guide](https://docs.moergo.com/glove80-user-guide/rgb/) documents effect, brightness, hue, saturation, and speed controls; it does not document fixed colors per key. The Layout Editor's [key decorations](https://docs.moergo.com/layout-editor-guide/layout-editing/) change how keys appear in the *editor*, not the physical LEDs.

A [community Glove80 ZMK configuration and fork](https://github.com/darknao/glove80-zmk-config) does document a per-layer/per-key RGB effect with one color binding per position, named or hex colors, and optional status-dependent colors. This appears technically capable of Defy-like purpose colors, but it requires that custom firmware, configuration, a build, and flashing both halves. It is outside the documented stock MoErgo lighting controls and has not been tested in this project. It may consume substantial battery power when continuously lit, especially wirelessly. The future skill should pin and test the chosen lighting fork before promising this feature.

## How a first agent-assisted experiment would work

1. Choose a known-good Glove80 baseline: clone MoErgo's template or export the current editor layout as `.keymap`; save the original and record keyboard/firmware version. Do not assume a downloaded factory layout matches the user's installed firmware.
2. Make one small key or layer change in a distinct Git branch/file. Use ZMK's documented identifiers, inspect the exact position mapping, and preserve the bootloader entry and base-layer return paths.
3. Build with the matching MoErgo toolchain, preferably in CI or a pinned local environment. Check compiler output, resulting firmware filenames, and a source diff before loading.
4. Connect each half in turn, enter bootloader mode, and copy the correct `.uf2` to the matching USB mass-storage drive. MoErgo recommends the physical power-on bootloader method. Its guide also recommends a configuration reset and re-pairing after firmware-version or advanced-configuration changes. Keep a known-good firmware and another keyboard available during experiments. [Flash procedure](https://docs.moergo.com/glove80-user-guide/customizing-key-layout/).
5. Verify the behavior on the actual host and keyboard, including both halves, layer return, modifier chords, and any timing-sensitive macros. A successful compile and file copy alone do not establish that a shortcut behaves as intended.

## What this answers and what remains untested

**I can likely prepare, edit, diff, and build Glove80 keymaps more directly than Bazecor virtual JSON.** The published source and ZMK references reduce the unknown-keycode problem. I could potentially perform the USB file-copy portion of flashing on a computer that exposes the attached bootloader drives to my tools. The physical bootloader step and hands-on functional verification remain part of each experiment. No Glove80, editor account, exported baseline, local toolchain, or bootloader volume was available in this research, so no build or flash was tested.

A future Glove80-specific agent skill should first establish a reproducible baseline fixture, stable physical position IDs, exact firmware/toolchain version, build validation, half-specific flash checks, rollback steps, and a distinction between compiled firmware and verified on-device behavior. It should use ZMK names and syntax instead of reusing Defy/Bazecor serialization assumptions.
