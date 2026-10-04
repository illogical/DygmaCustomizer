# Bazecor fixtures for the Mac Defy manifest

Use the existing assignments in `examples/VirtualDefy.json` before creating new fixtures for `profiles/macbook-pro-m5-init.local.json`. Keep that source intact. For each genuinely new example below, start from a separate copy, make only the stated change, use Bazecor's Save action, and save the result under a distinct filename. Send the saved examples for command-by-command comparison. Loading a virtual file does not update a connected keyboard.

Record the Bazecor version, Defy model/layout, firmware shown by Bazecor, and whether RGBW mode is enabled. These encodings may depend on Bazecor or firmware; the Mac's Raycast, VS Code, screenshot, and Herdr shortcuts must also be checked on that Mac. Do not infer a new keycode merely from an older API example or from a different machine.

## Next fixture to make

One saved copy can cover the immediate questions. First inspect the existing L1 thumb assignments listed below in Bazecor. In the copy, set One Shot Layer L4 on L1 `Super 1` and Layer Lock L7 on L1 `No Key` **only if those exact behaviors are absent**. Put a Layer Lock L1 return on L5 `Macro 1` if its code cannot be established from the inspected assignments. Save screenshots or notes identifying each edited position and its Bazecor action. Avoid changing macros or Superkeys in this fixture.

For lighting, use otherwise empty L8 and assign 11 *different existing palette slots* to the 11 right-side physical positions listed at the end of this guide. Keep a position-to-color list or screenshot. One saved result lets us compare the keymap and colormap separately against the untouched source. The source already stores every palette slot's RGBW values; this fixture establishes the missing **key-to-LED positions**, not the RGBW values. If Bazecor cannot distinguish all 11 chosen slots in one save, use successive saved copies for the ambiguous positions.

The source is a wireless RGBW Defy virtual file with ten layers and 80 key positions per layer. L4–L10 are entirely Transparent in `keymap.custom`; L1–L3 contain assignments. `keymap.custom` and `keymap.default` currently have identical data. `macros.map` and `superkeys.map` are nonempty, so preserve their contents and references when adding actions. The colormap has 178 entries per layer, while `device.keyboard` lists only 35 left and 35 right physical-key LEDs; additional LED positions must not be guessed from the key layout.

## Already present in the source

The L1 keymap already contains these assignments at the named physical positions:

| L1 position | Key index | Stored code | What it establishes |
| --- | --- | --- | --- |
| Battery Level (`defy:right:r5:c7`) | 78 | `230` | The L4 assignment can copy this exact L1 code from the preserved source. |
| Bluetooth Pairing (`defy:right:r5:c8`) | 79 | `53852` | The L4 assignment can copy this exact L1 code from the preserved source. |
| `Super 1` (`defy:left:r5:c1`) | 64 | `53980` | Inspect the existing action's type, target, and behavior. |
| Left thumb `defy:left:r5:c2` | 65 | `17452` | Inspect whether it is a usable layer example. |
| Left thumb `defy:left:r5:c4` | 67 | `49211` | Inspect whether it is a usable layer or Superkey example. |
| `No Key` (`defy:left:r5:c5`) | 68 | `49721` | The stored assignment is not the transparent code `65535`; inspect its actual behavior. |
| `Macro 1` (`defy:right:r5:c4`) | 75 | `49209` | Inspect its reference and gestures; `superkeys.map` and `macros.map` are separate commands. |
| Right thumb `defy:right:r5:c1` | 72 | `54109` | Inspect whether it is a usable layer example. |
| Right thumb `defy:right:r5:c2` | 73 | `54108` | Inspect whether it is a usable layer example. |
| Right thumb `defy:right:r5:c5` | 76 | `49162` | Inspect whether it is a usable layer or Superkey example. |
| L3 top-row F5 position | 5 | `62` | The VS Code debug action can use this existing plain F5 code. |

The Battery Level and Bluetooth Pairing codes are sufficient to copy **these existing assignments** to L4 after confirming their labels in Bazecor. They are not proposed as portable constants for another source or firmware. The final layout makes their L1 positions Transparent.

## Layer actions still to inspect or demonstrate

First open the existing L1 thumb assignments above in the current Bazecor UI. A screenshot or written list of each assignment panel is enough for this inspection; no edited JSON is needed. Record each action's type, target layer, and, for a Superkey, all gestures and timing values. If an existing assignment exactly matches a requested behavior, reuse it rather than making another example. For any behavior absent from the source, save one minimal example per row so differences in `keymap.custom`, `superkeys.map`, `macros.map`, and timing commands can be attributed to that action.

| Requested behavior | Make a new example only if the source does not show it |
| --- | --- |
| One Shot Layer L4 | L1 `Super 1` (`defy:left:r5:c1`): tap for next key, hold for Layer Shift, double tap for lock; same position Transparent on L4. |
| Layer Lock L7 | L1 `No Key` (`defy:left:r5:c5`). |
| Tap/hold Superkey | L1 `Macro 1` (`defy:right:r5:c4`): Tap = Layer Lock L5, Hold = Layer Shift L6, other gestures unused. |
| Layer Lock L1 return | L5 `Macro 1`; use on L7 as well if the same encoding is valid there. |

Keep a route back to L1 from each locked layer. A code found on another thumb key is useful evidence, but its numeric value alone does not prove One Shot versus Lock versus Shift or a Superkey's gesture references.

## Later: Combo Key examples

First inspect existing key assignments in Bazecor for any of the listed chord shapes; the raw large keycodes in this JSON do not identify their modifiers by themselves. Create saved examples only for missing modifier/key families at an otherwise unused position on a spare layer. A few representative examples may establish a current-Bazecor encoding rule; compare additional members of each family before using that rule for all actions. If the rule is unclear, save each needed chord separately. Confirm the host actually performs each intended action.

| Family | Example chords | Remaining chords required by the manifest |
| --- | --- | --- |
| Raycast Hyper | `Hyper+A`, `Hyper+1` | Hyper with B, C, D, E, F, N, S, T, V, Z, after confirming Include Shift on this Mac |
| VS Code | `Cmd+P`, `Cmd+Comma`, `Ctrl+Minus`, `Ctrl+Shift+Minus`, `Shift+F12`, `Shift+Cmd+B` | None; plain F5 is already present on L3 of the source. |
| macOS navigation | `Ctrl+Cmd+Left`, `Shift+Cmd+Tab`, `Cmd+Grave`, `Shift+Ctrl+C` | `Ctrl+Cmd+Right`, `Cmd+Tab`, `Shift+Cmd+Grave` |

Raycast's [Hyper Key manual](https://manual.raycast.com/hyper-key) says macOS Hyper sends Ctrl+Alt+Cmd by default, with an optional Include Shift setting. The local profile currently includes Shift based on the earlier Mac setting; confirm that toggle before encoding Raycast chords. The L6 Finder action has been removed.

## Deferred: Herdr macros

The Herdr template already states `Ctrl+B`, release, then its standard command key. No macro examples are requested in this round. The full L7 Herdr layer remains blocked until its Bazecor macro encoding is verified later; preserve the source's nonempty `macros.map` and references.

## Right-side lighting map

On L8, assign distinct **existing palette colors** to the following L1 physical positions, then save. L8 currently uses slot 15 throughout, so choose other slots. Comparing each chosen slot in `colormap.map` with the untouched source should reveal its LED index. Do not derive the right-side LED map by zipping key and LED arrays; this source has 36 right key positions and 35 right LEDs.

`defy:right:r2:c3`, `r2:c4`, `r2:c6`, `r3:c2`, `r3:c3`, `r3:c4`, `r3:c5`, `r4:c2`, `r5:c4`, `r5:c7`, `r5:c8`.

The Mac manifest maps color purposes to existing palette slots only; it does not edit RGBW values. After the LED mapping is verified, preview the whole manifest and inspect its layer colors in Bazecor.

The proposed identities are green app keys on L4 (slot 1), cyan search keys on L5 (slot 4), blue navigation keys on L6 (slot 5), and a blue/teal navigation and creation grouping on L7 (slots 5 and 7). Amber activation keys (slot 0) mark layer access and return; transparent pass-through positions use the existing off slot 12. The other purpose mappings are recorded per template entry in the Mac manifest. Review visibility in Bazecor before treating these color choices as final.
