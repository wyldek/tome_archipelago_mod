# Installation and source-build workflow

This document targets the matching **1.0.2** [APWorld](../release/tome.apworld) and [ToME addon](../release/tome-archipelago.teaa), **Tales of Maj'Eyal 1.7.6**, and **Archipelago 0.6.7**.

## 1. Using the release artifacts

### Install the APWorld

Install `tome.apworld` through Archipelago Launcher's **Install APWorld** component, then restart the Launcher. It registers **Tales of Maj'Eyal** for generation and adds the **Tales of Maj'Eyal Client** launcher component.

### Install the ToME addon

Put the matching `tome-archipelago.teaa` in ToME's `game/addons` directory and restart ToME. Do not mix an addon and APWorld from different integration releases.

### Initialize the mailbox

Start ToME once with the addon enabled before launching the AP client. The addon uses the T-Engine virtual directory:

```text
/archipelago
```

On a normal Windows user profile this resolves to:

```text
C:\Users\<you>\T-Engine\4.0\tome\archipelago
```

The addon writes at least:

```text
mailbox-info.json      schema-2 marker identifying /archipelago
runtime-export.json    runtime talent/category metadata from this ToME install
```

The old development path `...\tome\tome\archipelago` is not the current mailbox.

### Connect the Archipelago client

Launch **Tales of Maj'Eyal Client** from Archipelago. On first launch it opens a directory picker. Select the exact physical directory containing `mailbox-info.json` and `runtime-export.json`.

The bridge validates the marker before accepting or caching the path. If an old cached path is no longer valid, it prompts again instead of creating a new directory.

Connect to the server and enter the slot name if prompted. `/tome` displays the current mailbox, seed/team/slot binding, and the last bridge error. `/resync` requests a server Sync and resends the bridge's pending checks.

### Start the AP character

With the bridge connected to a generated ToME slot, start ToME and create an **Archipelago Adventurer**. The addon rejects a save whose seed/team/slot/contract identity does not match the current client snapshot.

## 2. Expected mailbox files

During normal play the mailbox should look roughly like this:

| File | Writer | Purpose |
|---|---|---|
| `mailbox-info.json` | ToME addon | Marker proving this is the current `/archipelago` mailbox. |
| `runtime-export.json` | ToME addon | Schema-2 installed-content catalog source used for builds. |
| `client.json` | Python bridge | Contract, authoritative ordered receipts, server-confirmed checks, shop scout data. |
| `game.json` | ToME addon | Applied receipt count, locally completed checks, goal, game-side error state. |
| `bridge-state.json` | Python bridge | Persists locally observed checks waiting for/reflecting server acknowledgement. |
| `bridge.lock` | Python bridge | Prevents two bridge processes from owning one mailbox simultaneously. |

If `game.json` exists and contains checks while `client.json` says `connected: false`, the game side is still recording progress; reconnecting the client should flush pending checks to the server.

## 3. Supported Python for source/development use

Archipelago 0.6.7's pinned source environment supports Python 3.11.9 through 3.13. Python 3.14 is not supported by that Archipelago release.

A typical project environment is:

```powershell
cd C:\dev\tome_archipelago_mod
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

The test extra installs pytest and Lupa. Release validation requires both; a plain developer pytest run may skip the Lupa-backed module if Lupa is absent.

## 4. Run the standalone tests

```powershell
python -m pytest -q -rs
python -m compileall -q tome_ap apworld tools tests ToMEClient.py
```

For the full release gate, run `python tools/validate.py` with Lupa installed. These tests validate code-level invariants but do not replace real T-Engine or multiworld testing.

## 5. Build the `.teaa` from source

The addon archive does not need a runtime export:

```powershell
python tools/build.py --addon-only
```

Output:

```text
dist\tome-archipelago.teaa
```

For a release build, install that current addon in ToME and launch the game once before building the APWorld. This refreshes `runtime-export.json` using the exact addon source being released.

## 6. Generate the current schema-2 runtime export

The addon's load hook exports metadata from the installed ToME talent registry. Confirm that this file exists after launching ToME:

```text
C:\Users\<you>\T-Engine\4.0\tome\archipelago\runtime-export.json
```

It must contain `"schema": 2`. Schema-1 exports are intentionally rejected by the full catalog compiler.

The export reflects the content and DLC loaded in that ToME session. A release APWorld therefore represents the content set used to build it. The 1.0.2 release used a Steam-enabled launch with Possessor content; its compiled catalog has 291 AP trees, 1,232 item types, and 62 prodigies. Regenerate the export whenever the addon or loaded ToME content changes before making a release artifact.

## 7. Set up the pinned Archipelago checkout

A packaged `.apworld` build uses Archipelago's own `Build APWorlds` component, so use an Archipelago 0.6.7 source checkout:

```powershell
cd C:\dev
git clone --branch 0.6.7 --depth 1 https://github.com/ArchipelagoMW/Archipelago.git
cd Archipelago
C:\dev\tome_archipelago_mod\.venv\Scripts\python.exe ModuleUpdate.py
```

Do not install an unrelated PyPI package named `Archipelago` as a replacement for the source checkout.

## 8. Build and package the APWorld

Return to the ToME integration repository. Before staging, remove or rename an existing development `worlds\tome` in the AP checkout; the build script intentionally refuses to overwrite it.

```powershell
cd C:\dev\tome_archipelago_mod
python tools/build.py `
  --export "$env:USERPROFILE\T-Engine\4.0\tome\archipelago\runtime-export.json" `
  --ap-root C:\dev\Archipelago `
  --package-apworld
```

Outputs include:

```text
dist\tome-archipelago.teaa
dist\catalog.json
dist\worlds\tome\...       staged AP world
dist\tome.apworld           official APWorld package
```

`tools/build.py` compiles the real runtime export, copies the shared generator/core modules into the staged world, writes `data/catalog.json`, installs the development world into the AP source checkout, and invokes Archipelago's official packager.

A synthetic fixture catalog is refused for a release APWorld.

The official Archipelago launcher may try to install optional dependencies for unrelated bundled worlds before packaging. If that interrupts a noninteractive build **after the ToME tests pass**, the tested `worlds/tome` stage remains in the AP checkout. From this repository's activated Python environment, finish with:

```powershell
$env:SKIP_REQUIREMENTS_UPDATE = "1"
Push-Location C:\dev\Archipelago
try {
  python Launcher.py 'Build APWorlds' -- "Tales of Maj'Eyal"
  if ($LASTEXITCODE -ne 0) { throw "APWorld packaging failed" }
}
finally { Pop-Location; Remove-Item Env:SKIP_REQUIREMENTS_UPDATE }
python tools/validate.py --ap-root C:\dev\Archipelago
if ($LASTEXITCODE -ne 0) { throw "Native validation failed" }
python -c "from pathlib import Path; from tools.validate import verify_apworld; verify_apworld(Path(r'C:\dev\Archipelago\build\apworlds\tome.apworld'), Path(r'C:\dev\Archipelago\worlds\tome'))"
if ($LASTEXITCODE -ne 0) { throw "Package differs from staged world" }
Copy-Item C:\dev\Archipelago\build\apworlds\tome.apworld dist\tome.apworld
```

Run these steps only with the staged ToME world and pinned checkout produced by the build above. The [1.0.2 validation report](VALIDATION_REPORT.md) records this path and the final archive checks.

## 9. Generate a multiworld

Generate the template through Archipelago or start with the repository examples. Minimal settings are:

```yaml
name: PlayerName
requires:
  version: 0.6.7
game: "Tales of Maj'Eyal"

"Tales of Maj'Eyal":
  class_tree_count: 6
  generic_tree_count: 4
```

The complete option list is in [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md).

The world intentionally rejects nonempty generic `start_inventory`, `start_inventory_from_pool`, `item_links`, and `exclude_locations` settings because they can violate the seed-bound build contract. Use `starting_ranks` for normal ToME starter ranks.

## 10. Standalone client fallback

The preferred client is the launcher component embedded in `tome.apworld`. `ToMEClient.py` is a fallback for development/source use. It tries an importable/source Archipelago checkout, then the normal Windows Archipelago installation and can delegate to its Launcher client.

Typical source-checkout use:

```powershell
python ToMEClient.py `
  --mailbox "$env:USERPROFILE\T-Engine\4.0\tome\archipelago" `
  --connect host:port `
  --name SlotName
```

`--ap-root` is optional and only needed to override automatic Archipelago source discovery.

## 11. Optional ToME network isolation tools

The repository still contains `tools/windows_offline.ps1` and `tools/confirm_manual_offline.py` for developers who deliberately want to isolate ToME's native online services while testing modified addons.

**They are not part of the 1.0.2 runtime protocol.** The addon does not read `offline-policy.json`, and no offline acknowledgement is required to create or synchronize an AP character. The Python bridge itself must remain online to reach the Archipelago server.

## 12. Troubleshooting order

1. Confirm the matching addon and APWorld are installed.
2. Start ToME and verify `...\tome\archipelago\mailbox-info.json` has schema 2 and `virtual_root: "/archipelago"`.
3. Verify `runtime-export.json` appears in the same directory.
4. Launch the AP client and run `/tome`; confirm the mailbox path and a non-`None` seed/team/slot binding after connection.
5. Verify `client.json` appears and shows the expected contract/identity.
6. Enter the AP character and verify `game.json` appears.
7. If checks are present in `game.json` but not on the server, confirm the AP client is currently connected; reconnecting should flush pending checks.
8. If items stop applying, inspect the in-game `[Archipelago] SYNC STOPPED` message and the `error` fields in the mailbox snapshots before editing any save or receipt state.
9. Do not hand-edit `applied_count`, the receipt prefix, or contract identity to force recovery.

Use `python tools/status.py --help` for a simple mailbox status view during development.
