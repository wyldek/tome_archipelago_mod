# Tales of Maj'Eyal Archipelago Setup

## Requirements

- Tales of Maj'Eyal 1.7.6 with the matching `tome-archipelago.teaa` addon.
- Archipelago 0.6.7.
- For the standalone fallback client only: Python 3.11.9 through 3.13. Python 3.14 is not supported by Archipelago 0.6.7.

## Install the APWorld

Install `tome.apworld` through Archipelago Launcher's **Install APWorld** component, then restart the Launcher. The world adds **Tales of Maj'Eyal** to generation and registers a **Tales of Maj'Eyal Client** launcher component.

## Install the ToME addon

Install the matching `tome-archipelago.teaa` into ToME's addon directory and restart ToME. Do not mix an addon and APWorld from different integration versions.

## Generate

Create a normal Archipelago YAML for `Tales of Maj'Eyal` and generate the multiworld. The default 6/4 build uses the configured world checks first and fills the remaining reward budget with dynamic level checks.

## Connect

Launch **Tales of Maj'Eyal Client** from Archipelago. The first launch opens a directory picker for the ToME mailbox directory, for example:

`C:\Users\you\T-Engine\4.0\tome\archipelago`

The client remembers that directory for later launches. WebHost `archipelago://` links are supported.

Start ToME and create an **Archipelago Adventurer**. The addon and bridge reject mismatched seed/slot contracts.

## Shop checks

Paid shop checks scout their locations from the server before display. The merchant shows the exact AP item and recipient before purchase. Shop scouting uses `create_as_hint: 0`, so revealing the store inventory does not create or broadcast hints.

## Standalone client fallback

The separate client bundle no longer requires `--ap-root`. It first tries an importable/source Archipelago 0.6.7 install, then the standard Windows install (`C:\ProgramData\Archipelago`) and delegates to the installed Launcher client. `--ap-root` remains an optional override for unusual source-checkout locations.

Typical direct-source use:

`python ToMEClient.py --mailbox C:\path\to\T-Engine\4.0\tome\archipelago --connect host:port --name SlotName`

Use `/tome` for current bridge status and `/resync` to resend Sync and pending checks.
