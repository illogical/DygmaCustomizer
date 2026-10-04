# Bazecor fixtures for the Mac Defy manifest

Use the existing assignments in `examples/VirtualDefy.json` before creating new fixtures for `profiles/macbook-pro-m5-init.local.json`. Keep that source intact. For each genuinely new example below, start from a separate copy, make only the stated change, use Bazecor's Save action, and save the result under a distinct filename. Send the saved examples for command-by-command comparison. Loading a virtual file does not update a connected keyboard.

Record the Bazecor version, Defy model/layout, firmware shown by Bazecor, and whether RGBW mode is enabled. These encodings may depend on Bazecor or firmware; the Mac's Raycast, VS Code, screenshot, and Herdr shortcuts must also be checked on that Mac. Do not infer a new keycode merely from an older API example or from a different machine.

## Already present in the source

The L1 keymap already contains these assignments at the named physical positions:

| L1 position | Key index | Stored code | What it establishes |
| --- | --- | --- | --- |
| Battery Level (`defy:right:r5:c7`) | 78 | `230` | The L4 assignment can copy this exact L1 code from the preserved source. |
| Bluetooth Pairing (`defy:right:r5:c8`) | 79 | `53852` | The L4 assignment can copy this exact L1 code from the preserved source. |
| `Super 1` (`defy:left:r5:c1`) | 64 | `53980` | A layer-related thumb assignment exists; its mode and target need UI inspection. |
| `No Key` (`defy:left:r5:c5`) | 68 | `49721` | The stored assignment is not the transparent code `65535`; inspect its actual behavior. |
| `Macro 1` (`defy:right:r5:c4`) | 75 | `49209` | Inspect its reference and gestures; `superkeys.map` and `macros.map` are separate commands. |

The Battery Level and Bluetooth Pairing codes are sufficient to copy **these existing assignments** to L4 after confirming their labels in Bazecor. They are not proposed as portable constants for another source or firmware. The final layout makes their L1 positions Transparent.

## Layer actions still to inspect or demonstrate

First open the existing L1 thumb assignments above in the current Bazecor UI. Record each action's type, target layer, and, for a Superkey, all gestures and timing values. If an existing assignment exactly matches a requested behavior, reuse it rather than making another example. For any behavior absent from the source, save one minimal example per row so differences in `keymap.custom`, `superkeys.map`, `macros.map`, and timing commands can be attributed to that action.

| Requested behavior | Make a new example only if the source does not show it |
| --- | --- |
| One Shot Layer L4 | L1 `Super 1` (`defy:left:r5:c1`): tap for next key, hold for Layer Shift, double tap for lock; same position Transparent on L4. |
| Layer Lock L7 | L1 `No Key` (`defy:left:r5:c5`). |
| Tap/hold Superkey | L1 `Macro 1` (`defy:right:r5:c4`): Tap = Layer Lock L5, Hold = Layer Shift L6, other gestures unused. |
| Layer Lock L1 return | L5 `Macro 1`; use on L7 as well if the same encoding is valid there. |

Keep a route back to L1 from each locked layer. A code found on another thumb key is useful evidence, but its numeric value alone does not prove One Shot versus Lock versus Shift or a Superkey's gesture references.

## Combo Key examples

Create saved examples for the modifier/key families below at an otherwise unused position on a spare layer. A few representative examples may establish a current-Bazecor encoding rule; compare additional members of each family before using that rule for all actions. If the rule is unclear, save each needed chord separately. Confirm the host actually performs each intended action.

| Family | Example chords | Remaining chords required by the manifest |
| --- | --- | --- |
| Raycast Hyper | `Ctrl+Alt+Cmd+Shift+A`, `Ctrl+Alt+Cmd+Shift+1` | Same modifiers with B, C, D, E, F, N, S, T, V, Z |
| VS Code | `Cmd+P`, `Cmd+Comma`, `Ctrl+Minus`, `Ctrl+Shift+Minus`, `Shift+F12`, `Shift+Cmd+B`, `F5` | None |
| macOS navigation | `Ctrl+Cmd+Left`, `Shift+Cmd+Tab`, `Cmd+Grave`, `Shift+Ctrl+C` | `Ctrl+Cmd+Right`, `Cmd+Tab`, `Shift+Cmd+Grave` |

The local profile currently defines Hyper as Ctrl+Alt+Cmd+Shift. The L6 Finder action has been removed.

## Herdr macro examples

Save a minimal macro triggered from L7 for `Ctrl+B`, release, `H`, then another for `Ctrl+B`, release, `Minus`. Check how Bazecor stores key-down/key-up events, macro IDs, keymap references, delays, and timing settings. The same verified structure must then cover final keys J, K, L, V, C, N, P, W, G, Z, X, and Q. Confirm Herdr's prefix and terminal behavior on the Mac before applying the full set.

## Right-side lighting map

On a spare layer, assign visibly distinct **existing palette colors** to the following L1 physical positions, then save. Comparing each chosen color's slot in `colormap.map` with the untouched source should reveal its LED index. If a chosen color already matches the original, choose a different existing color for that position. Do not derive the right-side LED map by zipping key and LED arrays; this source has 36 right key positions and 35 right LEDs.

`defy:right:r2:c3`, `r2:c4`, `r2:c6`, `r3:c2`, `r3:c3`, `r3:c4`, `r3:c5`, `r4:c2`, `r5:c4`, `r5:c7`, `r5:c8`.

The Mac manifest maps color purposes to existing palette slots only; it does not edit RGBW values. After the LED mapping is verified, preview the whole manifest and inspect its layer colors in Bazecor.

The proposed identities are green app keys on L4 (slot 1), cyan search keys on L5 (slot 4), blue navigation keys on L6 (slot 5), and a blue/teal navigation and creation grouping on L7 (slots 5 and 7). Amber activation keys (slot 0) mark layer access and return; transparent pass-through positions use the existing off slot 12. The other purpose mappings are recorded per template entry in the Mac manifest. Review visibility in Bazecor before treating these color choices as final.
