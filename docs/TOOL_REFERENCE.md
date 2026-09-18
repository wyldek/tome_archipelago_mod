\
# Tool reference

## `tools/build.py`

```text
usage: build.py [-h] [--export EXPORT] [--profile PROFILE] [--ap-root AP_ROOT]
                [--output OUTPUT] [--addon-only] [--package-apworld]
```

Important modes:

- `--addon-only`: packages `addon/tome-archipelago` as `dist/tome-archipelago.teaa`; no runtime export is required.
- Full build: requires `--export` pointing to a real schema-2 `runtime-export.json`; writes the compiled catalog and staged world.
- `--package-apworld`: additionally requires `--ap-root` pointing to an Archipelago source checkout containing `Launcher.py`; invokes Archipelago's official **Build APWorlds** component and copies `tome.apworld` to the output directory.
- If `<ap-root>/worlds/tome` already exists, the development install step deliberately refuses to overwrite it. Remove/rename the old staged world first.

Typical release command:

```powershell
python tools/build.py `
  --export "$env:USERPROFILE\T-Engine\4.0\tome\archipelago\runtime-export.json" `
  --ap-root C:\dev\Archipelago `
  --package-apworld
```

## `tools/install_addon.py`

```text
usage: install_addon.py [-h] --game-dir GAME_DIR [--replace]
```

Installs the unpacked development addon under the specified ToME game directory. It intentionally avoids silently coexisting with/overwriting unrelated addon copies.

## `tools/compile_catalog.py`

```text
usage: compile_catalog.py [-h] --export EXPORT [--profile PROFILE]
                          --output OUTPUT
```

Compiles a schema-2 runtime export with the reviewed profile. Schema-1 exports and fixture metadata are not release inputs.

## `tools/local_demo.py`

```text
usage: local_demo.py [-h] --catalog CATALOG --mailbox MAILBOX [--seed SEED]
                     [--class-trees CLASS_TREES]
                     [--generic-trees GENERIC_TREES]
                     [--zone-exploration-checks | --no-zone-exploration-checks]
                     [--quest-checks {none,major,major_and_zone}]
                     [--shop-checks {off,non_progression}]
                     [--shop-checks-per-store {1,2,3}]
                     [--early-level-max EARLY_LEVEL_MAX]
                     [--t1-t2-boss-priority | --no-t1-t2-boss-priority]
                     [--grant-all] [--reset]
```

Single-player mailbox simulator for development before connecting to a real AP server. It uses a distinct local-demo seed namespace.

## `tools/status.py`

```text
usage: status.py [-h] --mailbox MAILBOX
```

Prints mailbox status for development/troubleshooting.

## `tools/audit_install.py`

```text
usage: audit_install.py [-h] --game-dir GAME_DIR [--output OUTPUT]
```

Collects installed-source API evidence used while auditing ToME integration assumptions.

## `ToMEClient.py`

The preferred client is the launcher component embedded in `tome.apworld`. The fallback client can locate an Archipelago source checkout or delegate to the normal Windows Archipelago Launcher client.

Typical direct-source use:

```text
python ToMEClient.py --mailbox C:\Users\you\T-Engine\4.0\tome\archipelago --connect host:port --name SlotName
```

The selected mailbox is persisted by Archipelago after its schema-2 marker is validated. `/tome` shows mailbox/binding/error state and `/resync` requests a fresh server Sync plus pending check submission.

## Optional native-online isolation tools

`tools/windows_offline.ps1` can deliberately block outbound networking for the selected ToME executable while leaving Python/AP online. `tools/confirm_manual_offline.py` writes an operator acknowledgement for manual isolation workflows.

These are **optional developer tools only** in 1.0. The runtime does not read `offline-policy.json`, and neither helper is required for normal AP synchronization.
