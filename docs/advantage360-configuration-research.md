# Advantage360 key-binding configuration research

Researched 2026-10-04. This is a documentation-based comparison of the **wired Advantage360 (SmartSet USB, KB360)** and **wireless Advantage360 Professional (ZMK/Bluetooth, KB360-PRO)**. No keyboard, configuration export, build, or deployment was tested here. The two models use different configuration systems; a SmartSet layout cannot be treated as a ZMK keymap. [Kinesis wired support](https://kinesis-ergo.com/support/kb360/) · [Kinesis Pro support](https://kinesis-ergo.com/support/kb360pro/).

## Recommendation for an agent workflow

**For fast, repeatable key-binding experiments through scripts, the wired SmartSet model is the easier starting point.** Its active profile files are plain text on a keyboard-mounted virtual drive. A script can parse a preserved copy, change exact position/action tokens, validate the diff, and copy the result to the drive. Routine remaps do **not** require a firmware build or a flash. Kinesis documents the syntax and token list, although SmartSet itself is a proprietary programming engine. [Direct Programming Guide](https://kinesis-ergo.com/wp-content/uploads/Adv360-SmartSet-Direct-Programming-Guide-Version-8-8-25.pdf) · [Action Token List](https://kinesis-ergo.com/wp-content/uploads/Adv360-SmartSet-Direct-Programming-Action-Tokens-v3-31-23.pdf).

**For advanced behavior authored as code, the wireless Pro is more flexible.** Kinesis publishes an [MIT-licensed ZMK configuration repository](https://github.com/KinesisCorporation/Adv360-Pro-ZMK) and uses a customized [ZMK firmware fork](https://github.com/KinesisCorporation/Adv360-Pro-ZMK#note). An agent can make source-controlled keymap and firmware changes and compile them through GitHub Actions or locally. Applying that source-built firmware requires flashing separate left and right `.uf2` files. Kinesis warns that its fork can lag upstream ZMK keycodes/features. [Pro build and flash instructions](https://github.com/KinesisCorporation/Adv360-Pro-ZMK#building-the-firmware-with-github-actions).

The Pro also has **Clique**, a browser interface based on ZMK Studio. With Clique-capable firmware, ordinary remaps can be applied over USB without a new build or flash each time. This is attractive for quick *hands-on* edits, but Clique changes are stored on the keyboard and do not update the GitHub source repository. Kinesis documents fewer advanced behaviors in Clique than in the source route. A pre-Clique Pro needs a one-time firmware update. [Kinesis Clique upgrade guide](https://kinesis-ergo.com/360p-clique-upgrade/) · [Clique Help](https://kinesis-ergo.com/clique-help/).

| Question | Wired Advantage360 / SmartSet | Wireless Advantage360 Pro / ZMK |
| --- | --- | --- |
| Routine remap source | `layout*.txt` on the keyboard's v-Drive | ZMK `.keymap` source **or** Clique's on-device state |
| How an agent edits it | Parse and write documented text tokens | Edit and build Git source; Clique is a USB/browser workflow |
| Apply routine remap | Save file, safely close/eject v-Drive, test | Source route: build and flash both halves; Clique route: Apply then Save over USB |
| Open-source path | SmartSet syntax documented; firmware source not established here | Kinesis ZMK config and fork are public/MIT licensed |
| Advanced behavior | SmartSet macros, tap-and-hold, supported layer tokens, within its grammar | ZMK behaviors and settings in source; Clique supports a subset |
| Source-of-truth risk | Live v-Drive file can diverge from saved project copy | Clique changes explicitly do not sync to GitHub source |

## Wired SmartSet: how bindings change

Kinesis says the keyboard exposes a virtual flash drive (the **v-Drive**) with nine programmable profiles, each having text layout and indicator-light files. Profile 0 is deliberately non-programmable. A profile layout file records only overrides to the factory behavior, so an otherwise blank file does not describe the entire effective keymap. The [direct programming guide](https://kinesis-ergo.com/wp-content/uploads/Adv360-SmartSet-Direct-Programming-Guide-Version-8-8-25.pdf) describes the `layouts` folder, profile files, five layer headers (`<base>`, `<keypad>`, `<function1>`, `<function2>`, `<function3>`), and the distinction between physical **position tokens** and output **action tokens**.

The documented form for a simple remap is `[position]>[action]`; Kinesis gives `[hk1]>[q]` as an example. Macros use curly-braced trigger/action tokens and can encode press/release order and delays. Tap-and-hold has its own syntax. The [action token list](https://kinesis-ergo.com/wp-content/uploads/Adv360-SmartSet-Direct-Programming-Action-Tokens-v3-31-23.pdf) identifies common keys, modifiers, media, mouse, and layer controls. A future script should still check tokens against the installed firmware and preserve unrecognized lines rather than normalize or discard them.

An agent would mount the v-Drive with the onboard command, read the **selected numbered profile**, save its original file separately, produce a distinct proposed text file, validate the exact changed lines and untouched lines, then copy it to the mounted drive when ready to apply. Save/close the files and follow Kinesis's OS-specific eject/close procedure before testing. The [support page](https://kinesis-ergo.com/support/kb360/) offers SmartSet apps for Windows/macOS and notes that Linux users can directly edit v-Drive text files. Its firmware-update procedure is separate from routine remapping.

The grammar is readable but proprietary. Unknown tokens, conflicting duplicate commands, and syntax errors can yield unexpected/default behavior; the direct guide says the last conflicting command generally wins. A skill should validate one physical position and profile at a time, preserve a known-good copy, and verify behavior on the attached keyboard. Its text files also configure **six RGB indicator LEDs**, not Defy-like per-key lighting. [Direct Programming Guide](https://kinesis-ergo.com/wp-content/uploads/Adv360-SmartSet-Direct-Programming-Guide-Version-8-8-25.pdf).

## Wireless Pro: two distinct routes

### Versioned ZMK source and firmware

The [Kinesis ZMK repository](https://github.com/KinesisCorporation/Adv360-Pro-ZMK) contains the keymap/configuration source. Its README describes GitHub Actions builds and a local `make` build using Docker or Podman; `make` builds both halves. For a source-based update, edit the keymap, review the diff, compile, inspect the two firmware outputs, connect each half over USB, enter its bootloader, then copy `left.uf2` to the left and `right.uf2` to the right. Kinesis documents both key-combination and physical-button bootloader entry. This is a reproducible Git-based path suited to an agent skill, with a larger deployment step than SmartSet.

The repository warns that Kinesis-specific status LEDs may fail on unmodified upstream ZMK and that not every new upstream keycode is immediately supported by the Kinesis fork. A skill should pin the exact repository branch/revision, follow Kinesis's matrix position reference, and compile before claiming support for a behavior. [Kinesis repository README](https://github.com/KinesisCorporation/Adv360-Pro-ZMK).

### Clique and ZMK Studio runtime edits

[Kinesis's Clique guide](https://kinesis-ergo.com/360p-clique-upgrade/) says a Clique-enabled Pro connects via its **left module over USB** to a compatible desktop browser, where keymap changes can be made without firmware flashing. In the [Clique workflow](https://kinesis-ergo.com/clique-help/), Apply changes the live layout and **Save** makes the change persistent. Clique supports ordinary keys, modifier combinations, layer navigation, tap-and-hold, and a bounded macro set; it does not expose arbitrary ZMK settings or user-defined behaviors such as home-row mods/tap dance. Kinesis says Clique edits do **not** update the user's GitHub fork. Kinesis also points to the ZMK Studio native app as a separate runtime-editing option, without official Kinesis support for that app.

Kinesis's Clique upgrade page calls for Chrome or Edge and a USB serial connection. A future agent could potentially use the UI on a host with the keyboard connected, but no stable file export or script API for Clique was established in this research. For a durable agent-owned configuration, prefer the Git source route or test a readback/export process before making Clique the source of truth. Preserve the keyboard's unlock path; Kinesis says overwriting it can require a reset/flash. [Clique upgrade guide](https://kinesis-ergo.com/360p-clique-upgrade/) · [Clique Help](https://kinesis-ergo.com/clique-help/).

## First validation before writing an Advantage360 skill

1. Pick the exact model and firmware. For wired SmartSet, obtain a copied numbered-profile layout from its v-Drive plus the matching token documentation. For Pro, clone the user's actual Kinesis ZMK fork or inspect its current Clique layout; do not assume the public factory source equals the device state.
2. Choose one low-risk remap and record its physical position independently of its current label. Preserve a base-layer route back and, for the Pro, the bootloader/Clique unlock path.
3. Implement a minimal transform that leaves every unrelated binding intact. Validate syntax and show a line-level diff; for Pro source, compile both halves before deploying.
4. Apply through the model's actual path and test on-device and on the host. Record whether the observed behavior matches the proposed binding. Keep a known-good profile/file or firmware for recovery.

**Decision:** Start a script-first skill with **wired SmartSet** if the priority is rapid, repeated key-binding edits. Choose the **Pro's ZMK source path** if advanced firmware behavior, public source, and Git review matter more. Use Clique for interactive experiments after confirming firmware support, while treating its on-device state separately from Git. These conclusions come from Kinesis documentation; this project has not yet tested either model.
