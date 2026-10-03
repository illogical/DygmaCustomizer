# Personalization template

Copy to `PERSONALIZATION.md` and fill in the parts you want an agent to use. Keep machine-specific app paths, shortcuts, and preferences here. Do not put private account data or tokens in layout JSON.

## Platform and input

- Operating system and version:
- Keyboard layout/language:
- Bazecor and Defy firmware versions (if known):
- Which virtual JSON is the current starting point:
- Machine profile path (`profiles/*.local.json`), OS, and installed apps:

## Layer plan

| Layer | Purpose | Activation (Shift / Lock / One Shot) | Return path | Status |
| --- | --- | --- | --- | --- |
| L1 | Base | Default | — | Existing |

## Color key

| Category | Preferred color / palette slot | Meaning | Exceptions |
| --- | --- | --- | --- |
| Navigation | TBD | Same meaning across layers | |

Record the RGB(W) values and slot number after checking `python3 scripts/defy.py inspect INPUT.json`. A slot's color affects all LEDs that reference it; track semantic categories here rather than assuming an existing slot has one meaning.

## App shortcuts

| App/context | Action | Trigger (tap/hold/etc.) | Mac shortcut or events | Windows shortcut or events | Linux shortcut or events | L1 position | Layer | Color category | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

For macros, write the event sequence with presses, releases, text, clicks, and delays in order. Record whether holding/repeating the trigger should repeat it. For Superkeys, record each requested gesture separately and leave others unused. Mark whether the action is only proposed, checked in Bazecor, or tested on a physical keyboard. See `CUSTOMIZATION_GUIDE.md`.

For launchers, record whether Raycast (or another launcher) owns the shortcut, the actual shortcut, and whether the target app must be installed. Avoid assuming a keyboard macro can directly launch an app on every OS.

Reusable action names and suggested L1 positions live in `templates/`. This file explains personal priorities; a machine profile supplies OS, installed apps, and shortcut overrides. Run `scripts/resolve_template.py` to preview one template and make a cheat sheet before editing Bazecor.

## Open decisions

- Thumb key position for layer access:
- Apps and workflows to prioritize:
- Any keys or layers that must remain available as escape routes:
