# Bazecor fixtures for the Mac Defy manifest

Use `examples/VirtualDefy.json` as the preserved comparison source for `profiles/macbook-pro-m5-init.local.json`. Bazecor saved the user's virtual configuration at `/Users/matt/Dygma/Backups/VirtualDefy.json`; its current L8 example is preserved as `examples/VirtualDefy-L8-fixtures.json` for repeatable checks. Bazecor's Save action updates its selected virtual JSON; Preferences → Backups → Export Backup can report no backup for a virtual keyboard. A physical Defy is not needed to compare virtual JSON, but is needed later to confirm behavior on hardware. Keep each source intact and save the next example under a distinct name.

The saved file identifies a Defy with ten layers, 80 key positions per layer, 178 LED entries per layer, and 16 RGBW palette slots. Against the preserved source, only five L8 `keymap.custom` values and 30 L8 `colormap.map` values changed semantically. `palette`, `superkeys.map`, `macros.map`, device geometry, and other layers are unchanged; Bazecor only normalized whitespace in `palette` and `keymap.onlyCustom`.

## What the current L8 save establishes

| L8 position (L1 reference) | Key index | Saved code | Bazecor code-table meaning |
| --- | ---: | ---: | --- |
| Left r3:c3 (`S`) | 34 | `49164` | One Shot Layer L4 |
| Left r3:c4 (`D`) | 35 | `17498` | Move to Layer L7 |
| Left r3:c5 (`F`) | 36 | `17496` | Move to Layer L5 |
| Left r3:c6 (`G`) | 37 | `53980` | Reference to existing Superkey 1 |
| Left r3:c7 (`keycode:17152`) | 38 | `6916` | Hyper+A (`6912` modifier offset + HID `A` code `4`) |

The saved L7/L5 samples are Bazecor **Move to layer** codes. That table renders a lock icon; Bazecor also has a separate **Lock layer to** table. The remaining decision is whether the Mac layout should stay on a layer until an explicit L1 return, as these samples demonstrate, or toggle back when the trigger is tapped again. Assigning `53980` did not change `superkeys.map`, so this save does not define the requested Superkey gestures. [One Shot](https://github.com/Dygmalab/Bazecor/blob/development/src/api/keymap/db/oneshot.tsx), [layer actions](https://github.com/Dygmalab/Bazecor/blob/development/src/api/keymap/db/layerswitch.tsx), [Superkey references](https://github.com/Dygmalab/Bazecor/blob/development/src/api/keymap/db/superkeys.ts), [modifiers](https://github.com/Dygmalab/Bazecor/blob/development/src/api/keymap/db/modifiers.ts).

L8 LED offsets `0–14` now use slots `0–14` in order on the left. On the right, LED offsets `35–41` use slots `6,5,4,3,2,1,0`; `42–48` use `13,12,11,10,9,8,7`; and `55` uses `14`. These assignments confirm the first two right rows and anchor the final key of the third row. `scripts/defy.py` now maps the first three seven-key right rows to their seven-LED segments. Its third-row mapping follows the contiguous row geometry from that anchor and should be checked visually in Bazecor. The eight-key right thumb row has only seven LEDs, so do not zip the full right-side arrays. The Mac manifest still lacks verified LEDs for right r4:c2 and right thumb r5:c1, c2, c4, c7, and c8. A distinct one-position color save or a position-to-slot list from Bazecor can establish each missing mapping. No RGBW values need to be created: the source already contains the palette.

## Corrected device controls

The preserved L1 source has **Battery Level** at `defy:right:r5:c2`, key index `73`, code `54108`, and **Bluetooth Pairing** at `defy:right:r5:c1`, index `72`, code `54109`. Bazecor defines those codes in its [battery](https://github.com/Dygmalab/Bazecor/blob/development/src/hw/battery.ts) and [Bluetooth](https://github.com/Dygmalab/Bazecor/blob/development/src/hw/bluetooth.ts) tables. The older guide's `230` at c7 is Right Alt, and `53852` at c8 is not the Bluetooth Pairing code; neither may be copied as a device control. The Mac template intentionally places Battery Level at L4 c7 and Bluetooth Pairing at L4 c8, while clearing their actual L1 source positions c2 and c1.

Other source examples remain useful but do not define the requested new behaviors: L1 left thumb c1 has Superkey 1 (`53980`), left thumb c2 has Layer Shift L3 (`17452`), and right thumb c5 has One Shot Layer L2 (`49162`). Preserve their existing `superkeys.map`, `macros.map`, and timing commands when comparing fixtures.

## What can be applied now

The L8 Hyper+A example and Bazecor's [additive modifier tables](https://github.com/Dygmalab/Bazecor/blob/development/src/api/keymap/db/utils.ts) establish the Raycast Hyper letter/digit codes. The same Bazecor tables define the VS Code and macOS navigation chord families used in this manifest. Their numeric encodings no longer need separate samples; confirm that the Mac apps perform the intended shortcuts. Raycast's [Hyper manual](https://manual.raycast.com/hyper-key) describes Ctrl+Alt+Cmd by default and optional Shift; this Mac profile currently includes Shift.

The applier previously produced `profiles/macbook-pro-m5-L4-keys.local.json` and `profiles/macbook-pro-m5-L6-navigation.local.json` as separate demonstrations. The combined Mac preview now has one blocking prerequisite: a verified LED offset for the deferred L1 right-thumb Superkey. See `docs/macbook-pro-m5-virtual-preview.md`.

## Remaining examples and decisions

1. **Return behavior:** Move to L1 is selected for L5. The L8 file provides Move to Layer L5/L7, and the same Bazecor command table identifies Move to Layer L1.
2. **Deferred Superkey:** The L8 file only assigns an existing Superkey; `superkeys.map` is unchanged. Save a current example with Tap = Move to L5 and Hold = Layer Shift L6, then compare its map, references, and timing fields.
3. **Required red marker:** Save a one-key L8 lighting fixture for right thumb c4 to verify its LED offset. The combined preview will remain blocked until the deferred L1 key can be marked red. Other configured right-side keys can retain their source lighting pending separate LED checks.

Record Bazecor version, displayed firmware, RGBW mode, and the chosen action/physical position with each saved copy. Preview against the preserved source before applying. The deferred output mode refuses a combined JSON if any deferred key lacks a verified red LED; later check the result visually in Bazecor and on a connected Defy.
