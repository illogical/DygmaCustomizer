# Describe a customization

This guide translates a requested behavior into a Bazecor feature and a verifiable change. It applies to the Defy first; check the model, Bazecor version, firmware, and source format before using it for another Dygma keyboard. See [Dygma's Defy guide](https://dygma.com/pages/defy-configuration), [Superkeys guide](https://support.dygma.com/hc/en-us/articles/22652130341277-How-to-configure-Superkeys), and [shortcut guide](https://support.dygma.com/hc/en-us/articles/22628279896349-How-to-create-shortcuts-and-home-row-modifiers).

## A useful request

Describe the **action**, **trigger**, **location**, and **return behavior**. An agent can infer routine details from the source, but should resolve ambiguous L1 labels and unknown app shortcuts before changing assignments.

> On L5, make the position occupied by `J` on L1 run VS Code's “Toggle Terminal” on macOS. Use the same semantic color as other editor actions. Keep other positions as they are.

> Make the L1 left inner thumb key access L6 as a One Shot Layer: tap for the next key, hold while using several keys, and double tap to lock it. The same position on L6 should be Transparent. Keep an obvious route back to L1.

> On the L1 `F` position, tap for `F` and hold for Shift. Tune the timing only after I report whether typing rolls accidentally trigger Shift.

For a macro, give the ordered sequence of key presses/releases, text, clicks, and delays, plus the app and OS. State whether repeating or holding the trigger should repeat the macro. For a Superkey, give only the gestures you want: Tap, Hold, Tap & Hold, 2Tap, or 2Tap & Hold. Unspecified gestures should stay unused.

## Choose the simplest Bazecor feature

| Desired behavior | Bazecor feature | Confirm before encoding |
| --- | --- | --- |
| One key or media/mouse action | Direct assignment | Keycode and device support |
| One key with modifiers pressed together | Shortcut / Combo Key | Actual app shortcut on each OS |
| Tap does one action, hold another | Dual-function key or Superkey | Hold timing and rollover feel |
| Several gestures on one position | Superkey | Which gestures are valid for each action |
| Ordered key, mouse-click, text, or delay events | Macro | Event order, modifier release, timing, repeat |
| Layer active while a key is held | Layer Shift | Target and escape/transparent position |
| Tap toggles a layer | Layer Lock | How to return from target layer |
| Tap affects next key; hold shifts; double tap locks | One Shot Layer | Transparent same position on target and unlock behavior |

A Superkey supports up to five gestures. Dygma says Layer Shift can be a **hold** action but not a **tap** action; its Superkey mouse options exclude the wheel. Keep a plain shortcut as a shortcut: a macro adds sequence timing and should be used when order or delays matter. See [Dygma's Superkey limitations](https://support.dygma.com/hc/en-us/articles/22652130341277-How-to-configure-Superkeys).

One Shot Layer setup includes making the trigger's position Transparent on the target layer, according to [Dygma's configuration steps](https://dygma.com/blogs/product-development/one-shot-modifiers-and-layers). Tap, hold, and double-tap behavior should be checked in Bazecor and later on the physical keyboard. Superkey and dual-function timing depends on typing style; record a symptom before changing thresholds. See [Dygma's timing guidance](https://support.dygma.com/hc/en-us/articles/22628279896349-How-to-create-shortcuts-and-home-row-modifiers).

## Preserve meaning across platforms

Record an action by its name, then list its actual Mac, Windows, and Linux shortcuts in `PERSONALIZATION.md`. A keyboard emits keys and mouse actions; Raycast, VS Code, and other host apps decide what those inputs do. App launching normally requires a host launcher or OS binding. Do not assume a Mac shortcut has the same effect elsewhere.

For repeatable designs, put named actions, stable physical position IDs, L1 hints, and semantic color categories in `templates/`. A template can be a small key group merged into an existing layer. Put a particular computer's OS, installed apps, Hyper definition, shortcut overrides, and agreed category-to-palette-slot mapping in a profile. Resolve one template with `scripts/resolve_template.py` to preview a cheat sheet. Use `scripts/apply_template.py preview` to inspect a target layer's occupied keys and supported encodings before writing a distinct virtual JSON with `apply`. The template is an intent layer above Bazecor's numeric keycodes; see `templates/README.md` for the schema and limitations. Keep a shortcut's actual OS-specific chord explicit, because defaults such as VS Code Back differ across Mac, Windows, and Linux.

For each planned action, record: app/context, action name, target layer and L1 reference position, trigger gesture, OS shortcut or macro events, semantic color category, and verification status. `PERSONALIZATION.example.md` provides a table. A color slot is a shared RGB(W) value; the category is a user convention, so audit current use before reassigning a slot across layers.

## Build and verify

1. Identify the source: virtual JSON or a backup from a connected keyboard. Record Bazecor and firmware versions when available. Keep that source intact.
2. Resolve physical positions from L1 and inspect any existing macro/Superkey definitions and references. A virtual file stores `keymap.custom`, `macros.map`, and `superkeys.map` as distinct commands; changing or moving one reference can affect other assignments.
3. Create a distinct output. Use `scripts/defy.py` for its supported key, layer, and color edits, or `scripts/apply_template.py` for supported partial template patches. The latter requires explicit `--override` for occupied keys and checks any requested color slot against the source's RGB(W) palette. For macros, Superkeys, layer trigger keycodes, modifier combos beyond the verified Cmd+S example, and other functions, configure one minimal example in Bazecor first, save a new virtual file or backup, and compare its parsed commands to the source. Turn that verified difference into a focused script only when it is reusable.
4. Verify exact changed key positions, LED positions, command lengths, and any macro/Superkey references; confirm unrelated commands and layers are unchanged. Open the output in Bazecor and inspect/try the behavior.
5. When a physical Defy is connected, export a backup of its current setup first. Confirm model, firmware, and compatibility in Bazecor, then use Bazecor to apply and test the change on the keyboard. Preserve a known working backup and record observed behavior. A virtual JSON load alone does not apply it to hardware. [Dygma's backup guidance](https://support.dygma.com/hc/en-us/articles/28094167317405-One-half-of-my-keyboard-doesn-t-turn-on) describes export; [restore guidance](https://support.dygma.com/hc/en-us/articles/360007165377-How-to-restore-the-default-configuration-of-the-keyboard) describes full backups.

Bazecor can [share or load a single layer](https://support.dygma.com/hc/en-us/articles/25643999587997-How-to-save-and-load-layers), which is useful for a portable layer recipe. Use a [full backup](https://support.dygma.com/hc/en-us/articles/25644360260637-How-to-save-and-restore-backups) when the result depends on macros, Superkeys, preferences, or other layers. Dygma says names are stored in Bazecor backups rather than on the keyboard, so keep human-readable names in the personalization file too; [name syncing guidance](https://support.dygma.com/hc/en-us/articles/15334667208989-How-to-sync-the-names-of-layers-superkeys-and-macros-between-devices) explains the distinction.

The [Bazecor FOCUS API](https://github.com/Dygmalab/Bazecor/blob/development/FOCUS_API.md) documents macro and Superkey command structures, but its examples do not replace a round trip through the current Bazecor UI and firmware. Treat macros, Superkeys, and their names as separate data with possible references from key assignments. Avoid hand-writing an unverified byte sequence into a user's configuration.
