# Tales of Maj'Eyal — Archipelago integration

**Development beta. The local item/check transport has been smoke-tested in ToME; full-campaign and shared-multiworld qualification remain.**

This project implements the three components of the proposed integration:

```text
Archipelago server
       | WebSocket, handled by Archipelago CommonClient
Python ToME bridge
       | validated, atomic JSON mailbox snapshots
ToME Lua addon
       | seed-bound character, grants, checks, save state
Tales of Maj'Eyal
```

The default build is six random class trees, four random generic trees, plus mandatory Technique / Combat Training. The generator chooses five specific prodigies, expands the pool for any selected prodigy that grants AP-managed categories, creates the individual rank rewards, adds ten +5 packages for each of the six stats, and subtracts any ranks provided at the start. The number of AP locations is calculated
from the resulting shuffled item budget.

**Read [IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) before using
this with other people's progression items.** This beta includes deliberate
scope limits and has not completed a real ToME campaign. Automated unit tests
and fake-engine Lua tests do not establish game-engine compatibility.

## What is included

- A ToME addon, with its source and a `.teaa` development package.
- APWorld source, YAML options, seed generation, stable item/location IDs,
  exact item-pool accounting, and slot data.
- A Python bridge using Archipelago's CommonClient.
- A runtime catalog exporter and compiler. Talent identifiers and rank caps
  come from the actual game export rather than an invented talent list.
- A local single-player mailbox demo for debugging before using an AP server.
- Tests for generation, receipts, persistence rules, JSON, and Lua adapters
  under a fake engine; optional APWorld tests for an upstream AP checkout.
- Installation, inspection, offline-isolation, packaging, and status tools.
- AP-only antimagic/arcane coexistence: mixed random builds do not inherit vanilla mutual-exclusion flags.

The APWorld **must be built after exporting a compatible catalog from ToME**.
The raw `apworld/tome` source directory is not a finished installable world:
its generated `data/catalog.json` and shared core modules are supplied by
`tools/build.py`. No synthetic test catalog is presented as real game data.

## Project layout

```text
tome_ap/                         Python generation, catalog, protocol and client
apworld/tome/                    Archipelago integration and options
addon/tome-archipelago/          Lua addon and source adapters
profiles/                       Supported candidate talent/prodigy profiles
examples/                       Example player YAML
ToMEClient.py                    Python bridge entry point
tools/                          Catalog, install, demo, audit and build tools
tests/                          Standalone and fake-engine tests
docs/                           Setup, limitations, protocol, references
```

## Read in this order

1. [Implementation status](docs/IMPLEMENTATION_STATUS.md).
2. [Installation and development setup](docs/INSTALL.md).
3. [Tool command reference](docs/TOOL_REFERENCE.md), generated from this build.
4. [Ruleset and YAML](docs/RULESET.md).
5. [Architecture and persistence](docs/ARCHITECTURE.md).
6. [Testing and release gates](docs/TESTING.md).
7. [Validation report](docs/VALIDATION_REPORT.md).

## YAML

```yaml
name: wyldek
game: Tales of Maj'Eyal

Tales of Maj'Eyal:
  class_tree_count: 6
  generic_tree_count: 4
```

A larger build changes the counts, not the implementation:

```yaml
name: wyldek
game: Tales of Maj'Eyal

Tales of Maj'Eyal:
  class_tree_count: 9
  generic_tree_count: 6
```

Use the example files and generated AP template for the other options. Options
are fixed when the seed is generated; editing the YAML cannot change a seed
already in progress.

For ten ordinary 20-rank random trees plus Combat Training (35 ranks), 60 stat packages, five prodigies and two starting ranks, the baseline budget is **298 shuffled items/checks**. Selected prodigies can increase it further by adding their own talent trees. Real generation always sums the exact runtime-exported caps. Fixed boss/story checks consume part of that budget and the remaining locations are distributed over advancement milestones.

## First test

Use a separate ToME installation/profile and a new disposable character.
Install the addon, export its runtime catalog, compile that catalog, and use
the local demo before connecting to a private Archipelago test server.
The exact commands and the expected files are in [INSTALL.md](docs/INSTALL.md).

Do not begin by joining an established group seed. The first end-to-end test
must verify all of the following in the real game: the addon loads, the AP
subclass appears, the trees are correct, an item grants the intended rank,
a level checks the intended locations, and saving/reloading/reconnecting
neither duplicates nor loses grants.

## Build outputs

`tools/build.py --addon-only` packages the addon without requiring a game
catalog. A full build requires a real runtime export and produces a staged
APWorld. With an Archipelago source checkout it can invoke the upstream
**Build APWorlds** component to package `tome.apworld` correctly.

For help:

```powershell
python tools/build.py --help
python tools/install_addon.py --help
python tools/compile_catalog.py --help
python tools/local_demo.py --help
python ToMEClient.py --help
```

## Safety and compatibility

The addon changes advancement, talent grants, equipment validation and online
isolation policy for its AP character. Back up saves. Never enable it on a
valuable character to test it. A failed grant deliberately stops further
receipt processing; do not edit the cursor to skip the problem.

The supplied Windows offline helper blocks the chosen **ToME executable**,
not Python. It does not prove that every possible cached or third-party
content source is disabled. The manual offline acknowledgement is an
acknowledgement, not a network-blocking mechanism.

This source is licensed under MIT for the original code. ToME, Archipelago,
DLC, and third-party libraries remain under their respective licenses. Game
binaries, DLC, and third-party source are not bundled.

## v0.2.7 revealed shop checks

Paid shop checks now use Archipelago LocationScouts. Merchants display the actual item and recipient before purchase; unscouted shop checks are not shown. The real client scouts enabled shop locations on connect, and the local demo publishes equivalent placement metadata.

## v0.2.6 configurable location model

The beta now exposes YAML controls for curated zone exploration, major/zone quest checks, paid shop parcels, the early level band, and T1/T2 boss priority. Paid shop parcels are `non_progression`: they may hold useful/filler/trap items but reject logical progression from every world. They consume the normal location budget rather than adding filler, so the default 6/4 illustrative build remains 298 rewards/checks with zero generated Vitality filler copies.

A future artifact-check option is planned as a separate design pass because it can add a very large number of checks.
