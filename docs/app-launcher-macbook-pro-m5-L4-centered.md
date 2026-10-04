# L4 Defy preview report

This is a proposed layout. No Bazecor JSON or keyboard was changed.

- Source: `examples/VirtualDefy.json`
- Template or manifest: `profiles/macbook-pro-m5-init.local.json`
- Profile: `/Users/matt/dev/projects/DygmaCustomizer/profiles/macbook-pro-m5.local.json`
- Actions: 15
- Action issues: 3

## Blockers and manual checks

| L1 position | Action | Issue |
| --- | --- | --- |
| N (`58`) | app-launcher.notion | LED position unverified |
| Right Alt (`78`) | device-controls.battery_level | LED position unverified |
| keycode:53852 (`79`) | device-controls.bluetooth_pairing | LED position unverified |

## Position and palette notes

- one_shot_return: cannot confirm mnemonic 'Super 1' from defy:left:r5:c1 (keycode:53980)
- battery_level: cannot confirm mnemonic 'Right Alt' from defy:right:r5:c7 (keycode:230)
- bluetooth_pairing: cannot confirm mnemonic 'keycode:53852' from defy:right:r5:c8 (keycode:53852)

Check host shortcuts and the intended behavior in Bazecor before applying a virtual configuration.
