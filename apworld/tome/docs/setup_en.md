\
# Tales of Maj'Eyal Archipelago Setup

## Requirements

- Tales of Maj'Eyal 1.7.6.
- Matching `tome-archipelago.teaa` and `tome.apworld` from the same integration release.
- Archipelago 0.6.7.
- Python 3.11.9–3.13 only if using the standalone/source fallback client; normal Launcher use does not require a separate Python setup.

## Install

Install `tome.apworld` through Archipelago Launcher's **Install APWorld** component and restart the Launcher.

Put `tome-archipelago.teaa` in ToME's `game/addons` directory and restart ToME.

## Initialize the mailbox

Start ToME once with the addon enabled. The addon creates its mailbox under virtual root `/archipelago`; on a normal Windows profile this is:

`C:\Users\you\T-Engine\4.0\tome\archipelago`

That directory should contain `mailbox-info.json` and `runtime-export.json` before the first client launch.

## Connect

Launch **Tales of Maj'Eyal Client** from Archipelago. The first launch asks for the mailbox directory. Select the exact `...\tome\archipelago` directory above. The client validates the schema-2 marker and remembers the path.

Connect to the server, enter the slot name if prompted, then start ToME and create an **Archipelago Adventurer**. The addon rejects mismatched seed/team/slot contracts.

Use `/tome` to show the active mailbox, binding, and last error. Use `/resync` to request Sync and resend pending checks.

## Check/item overview

Talent items are named `<Category>: <Talent>` and grant one raw rank. Stat items are named `+5 <Stat>`. Prodigies are named `Prodigy: <Name>`.

Locations include dynamic `Advancement LL — Reward RR` level checks, 16 boss checks, optional zone-entry/quest checks, optional paid merchant parcels, and `Age of Ascendancy — Victory`. Paid parcels display their scouted item/recipient before purchase and cannot contain logical progression from any world.

## Reconnect behavior

ToME can continue recording local checks in `game.json` while the AP client is disconnected. Reconnect the client to flush pending checks and refresh received-item history.
