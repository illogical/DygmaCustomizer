# Layer templates

Each JSON template names actions and proposed **L1 reference positions**. A profile supplies one computer's OS, installed apps, and shortcut overrides. `scripts/resolve_template.py` resolves **one layer at a time** and prints a text cheat sheet. It does not write Bazecor JSON or claim that the shortcuts work on a connected keyboard.

```sh
python3 scripts/resolve_template.py templates/vscode.json --os macos
python3 scripts/resolve_template.py templates/vscode.json --profile profiles/macbook-pro-m5.local.json --source-json examples/VirtualDefy.json
python3 scripts/resolve_template.py templates/app-launcher.json --profile profiles/macbook-pro-m5.local.json --source-json examples/VirtualDefy.json
python3 scripts/resolve_template.py templates/omarchy.json --profile profiles/omarchy.example.json
```

The VS Code template gives explicit Mac, Windows, and Linux shortcuts for the same named actions. It deliberately does not perform a global `Cmd` ↔ `Ctrl` replacement: navigation and other defaults differ by OS. A profile may override a shortcut by `template-id.action-id`. An action without an OS shortcut or profile override is omitted and reported, not guessed. `requires_app` and `requires_environment` filter actions for a particular machine. An `available_apps` list is an assertion supplied by the user; it is not an automatic inventory. A missing profile app is reported as skipped.

`profiles/*.local.json` and `PERSONALIZATION.md` are ignored by Git because they describe one user's computers. The tracked `*.example.json` profiles show the structure. The Mac profile here records the 13 application hotkeys visible in the supplied Raycast screenshot. Its Hyper modifier expands to Ctrl+Alt+Cmd+Shift based on this Mac's Raycast setting, but test the resulting shortcut in Raycast before encoding it in Bazecor.

The Markdown output can be saved as a cheat sheet when a design is ready: `python3 scripts/resolve_template.py templates/vscode.json --os macos --source-json examples/VirtualDefy.json > vscode-macos-cheatsheet.md`. The `--format json` output preserves action IDs and resolved physical positions for a future Bazecor compiler. Neither output changes a keyboard.

Positions are L1 labels, not keycodes. Confirm each against the target source JSON before writing a keyboard layout. The proposed VS Code layout places frequent navigation near the home rows; it is a starting point to adjust for comfort. Colors are semantic category names, with RGB(W) slots chosen only after inspecting the target palette. `activation` is a proposal; its thumb position remains open until a user selects it.

Template schema v1 keeps only portable intent: `id`, `name`, `platforms`, optional `environment` and `source`, `activation`, and `bindings`. A binding has stable `id`, human `name`, unique `position_l1`, `color_category`, optional `requires_app`, and optional `shortcuts` keyed by OS. Profiles carry `os`, optional `environment` and `version`, `available_apps`, `hyper_modifiers`, and `shortcut_overrides`. `Hyper` expands to the profile's actual modifiers; if unset, resolution fails for that action. Keep action IDs stable so future cheatsheets and migration tools can refer to them.

The [VS Code default keybindings](https://code.visualstudio.com/docs/reference/default-keybindings) and [Omarchy hotkeys manual](https://github.com/omacom/omarchy/blob/quattro/manual/07-hotkeys.md) were read on 2026-10-03. The Omarchy sample is based on the current `quattro` manual while [v4.0.4 was the latest release](https://github.com/omacom/omarchy/releases) at that time; compare it with `Super+K` and your installed Omarchy version before applying it. Its source may evolve. App launch shortcuts also depend on the host app and user settings.
