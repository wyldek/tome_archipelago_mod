# Installation and development workflow

These steps target a **Windows development setup**, ToME **1.7.6**, and an
Archipelago **0.6.7** source checkout. These are project targets, not a claim
that they are the latest releases. Use the same Python interpreter for the
bridge and the AP development checkout.

Use a separate ToME copy/profile and back up saves. The beta is not a
finished one-click integration.

## 1. Set up Python and inspect the package

Install a Python version supported by the pinned Archipelago checkout.
Its source instructions specify Python 3.11.9 or newer and below 3.14.
A Python 3.12 virtual environment is a reasonable target.

```powershell
cd C:\dev\tome_archipelago_source
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install lupa
python -m unittest discover -s tests -t . -v
```

Lupa is used only for executing fake-engine Lua tests; it is not a library
to install into ToME. See the included validation report and do not silently
ignore failed tests. Lua tests may be skipped when Lupa is unavailable.

## 2. Install the development addon

Either install the provided `tome-archipelago.teaa` into the game's
`game/addons` directory, or use the source-install helper. **Do not install
both the packed and unpacked form at the same time.**

```powershell
python tools/install_addon.py --help
```

Give the helper the actual game directory shown by Steam's Browse Local
Files command. Its help output is reproduced in TOOL_REFERENCE.md. The
helper intentionally refuses accidental overwrites/coexisting addon copies.

Enable the addon in ToME. Use a fresh disposable character for subsequent
tests. During source debugging, developer mode can change online/save
behavior; do not use an existing valuable save as a test subject.

## 3. Export the actual talent catalog

The addon's load hook exports talent metadata from the installed engine.
The AP subclass can remain unavailable until a valid seed configuration is
present; that does not prevent catalog export.

Look for `runtime-export.json` under the ToME user-data tree. The addon uses
the virtual directory `/tome/archipelago`; its physical location depends on
the engine's writable user-data root. A common Windows search is:

```powershell
Get-ChildItem "$env:USERPROFILE\T-Engine" -Recurse `
  -Filter runtime-export.json -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty FullName
```

This search is a way to discover the file, not a claim that the directory
must be in that exact location on every installation. Use the directory
that actually contains the export as the **mailbox directory**. Do not point
the bridge at an unrelated directory and assume the engine can see it.

If the file does not appear, inspect `te4_log.txt` and the addon load errors.
Do not proceed by generating fake talent IDs. Use `tools/audit_install.py`
to collect the relevant installed-source API evidence.

## 4. Isolate ToME's online content

The Python bridge must be able to reach Archipelago; the game executable
must not receive live ToME event/vault content during these tests.

Inspect the offline helper before running it:

```powershell
Get-Help .\tools\windows_offline.ps1 -Full
Get-Content .\tools\windows_offline.ps1
```

Run its block operation from an elevated PowerShell, passing the exact
ToME executable and mailbox directory using the parameters declared in the
script. It writes an offline-policy acknowledgement and can remove its own
firewall rule later. It does not need to block Python.

On other platforms, apply your own process/network isolation and then use
`tools/confirm_manual_offline.py --help` for an explicit acknowledgement.
That helper does **not** implement a firewall. Also disable online events in
ToME and avoid existing/cached online-event saves.

## 5. Compile and validate the catalog

```powershell
python tools/compile_catalog.py --help
```

Provide the real runtime export and the supplied
`profiles/wanderer-full.json` full player-tree policy profile. The tool resolves
actual talent symbols, caps, class/generic classification and prodigies.
Missing profile entries are reported. Insufficient eligible content for a
requested tree count is an error; it must not silently replace missing
content or reinterpret stable item IDs.

The full profile takes player-facing class/generic categories from the runtime export, always includes Combat Training, and adds reviewed prodigy-granted categories. The release catalog reflects the DLC/content installed in the export used to build it; use the same supported content set when testing the packaged world.

## 6. Run the local demo before a server

```powershell
python tools/local_demo.py --help
```

Supply the compiled catalog and actual mailbox directory using the tool's
arguments. The demo writes a seed-bound client configuration and serves a
local single-player item queue based on observed game checks. It is not an
Archipelago server and must not be run alongside the real bridge in the
same mailbox.

After the configuration is present, reopen character creation and select
**Archipelago Adventurer**. Validate the selected trees and starter grants,
reach level 2, and verify that the generated advancement locations are checked and cause corresponding receipts. The beta also includes additive boss and campaign milestone checks; those observe native accomplishments and do not replace ToME loot. Save/reload and test duplicate
receipt handling.

Use a new test save when changing demo seeds. Do not reuse a live server
character in the demo. Consult the demo's help for reset/grant-all testing
options; they are debugging operations.

## 7. Set up the pinned Archipelago checkout

```powershell
cd C:\dev
git clone --branch 0.6.7 --depth 1 https://github.com/ArchipelagoMW/Archipelago.git
cd Archipelago
C:\dev\tome_archipelago_source\.venv\Scripts\python.exe ModuleUpdate.py
```

Follow any dependency prompts. The project's ToME bridge imports this
checkout's CommonClient and related modules; do not install a random PyPI
package named Archipelago as a replacement.

## 8. Build and stage the APWorld

Return to the project directory and inspect:

```powershell
python tools/build.py --help
```

The build requires `--export` pointing to the real runtime catalog export.
Pass `--ap-root` for the pinned Archipelago source checkout. Add
`--package-apworld` to invoke Archipelago's official Build APWorlds component.
Use the tool's current help for any optional profile/output arguments.

The build stages the `tome` world, generated catalog and shared core under
`dist/worlds/tome`, then optionally installs that stage into the AP checkout.
It intentionally refuses an unrequested overwrite of an existing world.
The upstream packaging step supplies APContainer metadata rather than
manually fabricating the manifest's packaging version fields.

A source-only addon package can also be made independently:

```powershell
python tools/build.py --addon-only
```

## 9. Generate a private test seed

In the Archipelago checkout, generate template options through Launcher.py
or start with the project's `examples/wyldek.yaml`. Use a fresh Players folder
containing only the intended test player files. The minimal settings are:

```yaml
name: wyldek
game: Tales of Maj'Eyal
Tales of Maj'Eyal:
  class_tree_count: 6
  generic_tree_count: 4
```

Then:

```powershell
python Generate.py
```

Inspect generation errors and the selected-tree/item-count output. Do not
force generation by deleting failed assertions. The world includes optional
WorldTestBase tests under `worlds/tome/test` after staging.

## 10. Start the server and bridge

Host the generated archive using the AP checkout:

```powershell
python MultiServer.py "C:\path\to\generated_seed.zip"
```

Use the server's actual announced port. In another terminal, from this
project:

```powershell
python ToMEClient.py --help
```

Pass `--mailbox`, the exact slot name, and the server connection using the flags shown by that command. `--ap-root` is now optional and only needed to override automatic Archipelago source-root detection. On the standard Windows install, the fallback delegates to the installed Tales of Maj'Eyal Launcher client. The client uses the AP base parser for standard connection/password options. Do not store a password in Lua,
slot data or the mailbox.

Stop the local demo before starting the bridge. Start or reload an AP
character only after the bridge has published a valid configuration for the
intended seed and slot. The addon refuses a different identity for an
existing character.

## 11. Verify a real two-player exchange

A ToME-owned check must be able to contain a foreign player's progression
item. Complete that check and confirm the other game's client receives it.
Then send a ToME talent item from that other world and confirm it applies
exactly once in ToME. Also test an item sent while the game and bridge are
offline.

This is the point where the architecture has been demonstrated end to end.
It still does not establish that every generated build can complete the
campaign or that every native adapter is correct.

## Troubleshooting order

1. Addon load / Lua traceback.
2. Actual runtime-export file and actual mailbox path.
3. Offline-policy acknowledgement.
4. Runtime catalog and supported profile compatibility.
5. Seed/team/slot/contract identity.
6. Client connection and receipt history.
7. Native grant failure or check-detector failure.

Use `python tools/status.py --help` for the mailbox status utility. Preserve
logs, mailbox snapshots and the affected save when filing a bug. Never
"repair" a save by incrementing its receipt cursor by hand.
