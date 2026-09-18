# Tool command reference

Captured from this source package. Import/dependency errors are preserved rather than hidden.

## `tools/build.py`

```text
usage: build.py [-h] [--export EXPORT] [--profile PROFILE] [--ap-root AP_ROOT]
                [--output OUTPUT] [--addon-only] [--package-apworld]

options:
  -h, --help         show this help message and exit
  --export EXPORT
  --profile PROFILE
  --ap-root AP_ROOT
  --output OUTPUT
  --addon-only
  --package-apworld
```

## `tools/install_addon.py`

```text
usage: install_addon.py [-h] --game-dir GAME_DIR [--replace]

Install the unpacked development addon without overwriting unrelated files

options:
  -h, --help           show this help message and exit
  --game-dir GAME_DIR
  --replace
```

## `tools/compile_catalog.py`

```text
usage: compile_catalog.py [-h] --export EXPORT [--profile PROFILE]
                          --output OUTPUT

options:
  -h, --help         show this help message and exit
  --export EXPORT
  --profile PROFILE
  --output OUTPUT
```

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

Single-player protocol simulator for testing ToME before AP installation. Uses
real compiled metadata, not fixture talent names. It is deliberately a
separate seed namespace, so its saves cannot sync into a real multiworld.

options:
  -h, --help            show this help message and exit
  --catalog CATALOG
  --mailbox MAILBOX
  --seed SEED           reproducible demo seed; omitted = fresh random seed
                        (or resume existing demo state)
  --class-trees CLASS_TREES
  --generic-trees GENERIC_TREES
  --zone-exploration-checks, --no-zone-exploration-checks
  --quest-checks {none,major,major_and_zone}
  --shop-checks {off,non_progression}
  --shop-checks-per-store {1,2,3}
  --early-level-max EARLY_LEVEL_MAX
  --t1-t2-boss-priority, --no-t1-t2-boss-priority
  --grant-all
  --reset
```

## `tools/status.py`

```text
usage: status.py [-h] --mailbox MAILBOX

options:
  -h, --help         show this help message and exit
  --mailbox MAILBOX
```

## `tools/audit_install.py`

```text
usage: audit_install.py [-h] --game-dir GAME_DIR [--output OUTPUT]

options:
  -h, --help           show this help message and exit
  --game-dir GAME_DIR
  --output OUTPUT
```

## `tools/confirm_manual_offline.py`

```text
usage: confirm_manual_offline.py [-h] --mailbox MAILBOX
                                 --i-have-disabled-tome-networking

Record explicit operator acknowledgement on systems without our Windows
helper. This does NOT block networking; configure the OS/game beforehand.

options:
  -h, --help            show this help message and exit
  --mailbox MAILBOX
  --i-have-disabled-tome-networking
```

## `ToMEClient.py`

The fallback client auto-detects an Archipelago source checkout when possible and delegates to the installed Archipelago Launcher client on the normal Windows installation. `--ap-root` is an optional override, not a requirement. `--mailbox` is also optional after first use because the selected directory is persisted by Archipelago.

Typical use:

```text
python ToMEClient.py --mailbox C:\path\to\T-Engine\4.0\tome\archipelago --connect host:port --name SlotName
```

## Windows offline helper

Inspect the complete PowerShell script before running it as administrator.

```powershell
# Explicit opt-in: run in an elevated PowerShell. Blocks only this executable.
# Use a separate ToME installation for AP if ordinary ToME should stay online.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$GameExe,
    [Parameter(Mandatory=$true)][string]$Mailbox,
    [switch]$Remove
)
$ErrorActionPreference = 'Stop'
$exe = (Resolve-Path -LiteralPath $GameExe).Path
$bytes = [System.Text.Encoding]::UTF8.GetBytes($exe.ToLowerInvariant())
$hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
$id = ([System.BitConverter]::ToString($hash)).Replace('-','').Substring(0,16)
$name = "ToMEArchipelago-Offline-$id"
if ($Remove) {
    Get-NetFirewallRule -Name $name -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    Remove-Item -LiteralPath (Join-Path $Mailbox 'offline-policy.json') -ErrorAction SilentlyContinue
    Write-Host "Removed AP firewall rule for $exe"
    exit 0
}
if (-not (Get-NetFirewallRule -Name $name -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -Name $name -DisplayName "ToME AP offline ($id)" `
        -Direction Outbound -Program $exe -Action Block -Profile Any | Out-Null
}
$rule = Get-NetFirewallRule -Name $name
if ($rule.Enabled -ne 'True' -or $rule.Action -ne 'Block') {
    throw 'Firewall rule could not be verified.'
}
New-Item -ItemType Directory -Force -Path $Mailbox | Out-Null
$json = @{schema=1; mode='windows_firewall'; executable=$exe; rule=$name; confirmed=$true} | ConvertTo-Json
[System.IO.File]::WriteAllText((Join-Path $Mailbox 'offline-policy.json'), $json, (New-Object System.Text.UTF8Encoding $false))
Write-Host "ToME outbound networking is blocked for $exe. The Python AP bridge remains online."
Write-Host 'Also set Allow online events to Disabled in ToME, and use a new character.'
```
