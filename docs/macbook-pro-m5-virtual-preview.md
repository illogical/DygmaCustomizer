# MacBook Pro M5 virtual Defy preview

This guide uses `examples/VirtualDefy.json` as the preserved source and `profiles/macbook-pro-m5-init.local.json` as the manifest. L1 activates the app launcher on L4 with One Shot Layer. L5 contains VS Code actions and a Move to L1 return. L6 contains macOS navigation. L7 is unused. Loading a virtual file does not change a connected keyboard.

## One key still needs Bazecor configuration

| Layer and L1 position | Intended behavior | What blocks automatic configuration | What to save |
| --- | --- | --- | --- |
| L1 right thumb, L1 `Macro 1` position (`defy:right:r5:c4`, key index 75) | Tap: move to L5. Hold: Layer Shift to L6. | The preserved L8 example assigns an existing Superkey reference but does not define these gestures: `superkeys.map` and its timing settings are unchanged. This thumb key's LED offset is also unverified. | A distinct virtual JSON with this Superkey configured in Bazecor, including its gestures, references, and timing; first save a separate one-key color example to establish its LED. |

The generated file must show this deferred key in red (existing palette slot 11). The script leaves its original keycode untouched until a current Bazecor save proves the desired Superkey encoding. An output is refused if the red LED cannot be mapped.

## Establish the right-thumb LED

1. In Finder, make a **new copy** of `examples/VirtualDefy-L8-fixtures.json` with a distinct name, such as `VirtualDefy-L8-thumb-color-fixture.json`. Keep the source and `/Users/matt/Dygma/Backups/VirtualDefy.json` intact.
2. In Bazecor, open **Keyboard Manager → Use existing virtual keyboard** and select that copy. On L8, select the right-thumb key at the L1 `Macro 1` position. Change **only that key's lighting** to the existing red palette color (slot 11), then Save. Do not change the global palette.
3. Give the saved copy to the agent. It should compare `colormap.map` with the preserved L8 fixture, require exactly one L8 LED change and no key, palette, or unrelated command changes, then add its verified LED offset as `"75": LED_NUMBER` under `verified_leds` in the Mac manifest.

## Build and inspect the combined preview

After that LED mapping is verified:

```sh
python3 scripts/apply_template_set.py preview examples/VirtualDefy.json profiles/macbook-pro-m5-init.local.json --override --defer-unsupported
python3 scripts/apply_template_set.py apply examples/VirtualDefy.json profiles/macbook-pro-m5-init.local.json --override --defer-unsupported --output profiles/macbook-pro-m5-virtual-preview.local.json
```

The preview must report the deferred Superkey and its red LED without blockers. The output filename must be new. Other keys with verified assignments but unverified LED mapping retain their source lighting; they do not require manual key configuration.

Load the output through **Keyboard Manager → Use existing virtual keyboard**. Check L1's One Shot L4 trigger and the red `Macro 1` thumb; L4's application and device-control keys; L5's VS Code keys and Move to L1 return; and L6's navigation keys. Bazecor Save writes to the selected virtual JSON, so preserve a separate pre-inspection copy if you edit it. Test host shortcuts in their apps; the JSON preview alone cannot prove them.

## Capture the Superkey example for automation

On another distinct virtual copy, use Bazecor to configure the red L1 `Macro 1` key as a Superkey: **Tap → Move to L5** and **Hold → Layer Shift to L6**. Save and give that copy to the agent. Compare `superkeys.map`, the assigned key reference, and Superkey timing commands with the preserved source. Once the encoding is verified, the script can encode the action and replace the red marker with its intended activation color in a new output. A connected Defy should receive changes only through a separately backed-up and verified hardware workflow.
