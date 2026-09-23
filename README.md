# Tales of Maj'Eyal — Archipelago integration

**Version 1.0.2.** This release uses catalog schema 4 dependency protection while keeping contract schema 3 and mailbox protocol 1 for compatibility with existing generated seeds. Core item/check transport, starter-item delivery, level/zone checks, disconnected check accumulation, and reconnect catch-up have been smoke-tested in the real game. Full-campaign coverage, every prodigy/resource combination, and broad shared-multiworld qualification are still limited; see [Implementation status](docs/IMPLEMENTATION_STATUS.md).

The integration has three parts:

```text
Archipelago server
       | WebSocket, handled by Archipelago CommonClient
Python ToME bridge
       | validated JSON mailbox snapshots
ToME Lua addon
       | seed-bound character, grants, checks, save state
Tales of Maj'Eyal
```

## Quick start

1. Install `tome.apworld` through Archipelago Launcher's **Install APWorld** component and restart the Launcher.
2. Install the matching `tome-archipelago.teaa` in ToME's `game/addons` directory and restart ToME.
3. Start ToME once with the addon enabled. The addon creates the mailbox marker and runtime export. On a normal Windows profile the mailbox is:

   ```text
   C:\Users\<you>\T-Engine\4.0\tome\archipelago
   ```

4. Launch **Tales of Maj'Eyal Client** from Archipelago. On first launch, select that exact `...\tome\archipelago` directory. The client validates `mailbox-info.json` before accepting it and remembers the validated path.
5. Connect to the multiworld and enter the slot name if prompted.
6. Start ToME and create an **Archipelago Adventurer**. The class appears only when a valid bridge snapshot is present.

The old development path `...\tome\tome\archipelago` is not the 1.0 mailbox. Marker schema 2 identifies the current `/archipelago` virtual root and causes stale cached paths to be rejected.

## What the seed changes

A normal seed selects a character build rather than randomizing ToME's native loot table. By default it chooses:

- 6 random class talent categories;
- 4 random generic talent categories;
- mandatory **Technique / Combat Training** in addition to those 4 generic categories;
- 5 specific prodigies;
- 10 copies of each named `+5` primary-stat package;
- 2 precollected starter talent ranks.

Prodigies can add additional AP-managed categories. Reviewed dependencies can add support categories, functional-mechanic providers, and same-tree anchor ranks so a rolled category is not left without the mechanic it operates on. Native gear, artifacts, gold, XP, consumables, inscriptions, crafting, ordinary drops, and normal campaign maps remain ToME systems.

## ToME items in the Archipelago pool

| Item type | Hint / item name format | Effect |
|---|---|---|
| Talent rank | `<Category name>: <Talent name>` | Adds exactly one raw rank to that talent, up to its runtime-exported cap. Example: `Temporal Guardian: Warden's Focus`. |
| Stat package | `+5 <Stat>` | Adds 5 points to one named primary stat. The six names are Strength, Dexterity, Constitution, Magic, Willpower, and Cunning. |
| Prodigy | `Prodigy: <Prodigy name>` | Grants that specific prodigy. Selected prodigies that add rankable categories also add those categories' rank items to the seed. |
| Vitality fallback | `Vitality: +1 maximum life` | AP filler/admin-safe fallback. Normal ToME seed construction does **not** add Vitality copies merely to make the item and location counts match. |

Precollected ranks are real AP items but are removed from the shuffled pool before placement:

- `starting_ranks` precollects 0–2 likely offensive starter ranks. Starter selection is a metadata heuristic, not a guarantee that every equipment/resource combination is immediately usable. With the default value of 2, both ranks normally go into the same starter talent when its cap permits it; otherwise a second starter can be used.
- Dependency protection precollects enabling ranks from external support categories. Functional requirements reuse an already-rolled provider when possible and only add the reviewed fallback tree when necessary. Same-tree anchor ranks remain paid shuffled items; the reviewed number of ranks is requested through Archipelago's multiworld early-item pool.

The item pool is therefore based on the exact runtime catalog:

```text
all rank copies in selected random trees
+ all rank copies in mandatory Combat Training
+ all rank copies in prodigy-added trees
+ all rank copies in dependency support trees
+ 10 x each of the six +5 stat packages
+ selected prodigies
- precollected starter ranks
- precollected external dependency ranks
= shuffled ToME items
= active ToME locations
```

For the illustrative common case of ten ordinary four-talent/5-rank random trees, Combat Training's seven 5-rank talents, 60 stat packages, 5 prodigies, and 2 starter ranks, the result is **298 shuffled items/checks**. Real seeds can differ because category sizes/caps, dependency support/anchor rules, and prodigy-added categories come from the runtime catalog.

## What counts as a ToME check

Fixed world checks use part of the same reward budget as level checks. Enabling more fixed checks does **not** create more ToME items; it replaces level-reward locations with world locations.

| Check type | Default | Location name format / examples | Trigger |
|---|---:|---|---|
| Advancement | Dynamic | `Advancement 02 — Reward 01` | Reach the named character level. Several independent checks can share one level. |
| Boss | 16 | `Trollmire — Guardian Defeated`, `Dreadfell — The Master Defeated` | Defeat the configured native boss. AP observes the kill after the normal death/loot path. |
| Zone entry | 18 | `Trollmire — Explored`, `Gates of Morning — Reached` | Enter the configured zone. Despite the historical `— Explored` wording, the check is awarded on zone entry; 100% map exploration is not required. |
| Quest | 11 with `major_and_zone` | `Old Forest — Zone Quest Completed`, `Staff of Absorption — Orc Ambush Survived` | Reach the configured native quest status/sub-state. |
| Paid shop parcel | 126 with 3/store | `<Town> — <Merchant> — Archipelago Parcel <N>` | Buy the AP parcel from an eligible merchant. The store shows the scouted item and recipient before purchase. |
| Victory | 1 | `Age of Ascendancy — Victory` | Win the native Age of Ascendancy campaign. |

The default fixed manifest is 16 bosses + 18 zone entries + 11 quests + 126 shops + 1 victory = **172 fixed checks**. An illustrative 298-item seed therefore has **126 advancement checks** left over. The generator distributes those advancement checks across levels 2 through `level_ceiling` (40 by default).

### Boss check manifest

The always-present boss checks are:

- Trollmire guardian: Prox the Mighty or Shax the Slimy
- Norgos Lair guardian: Norgos, the Guardian or Norgos, the Frozen
- Kor'Pul guardian: The Shade or The Possessed
- Scintillating Caves: Spellblaze Crystal
- Rhaloren Camp: Rhaloren Inquisitor
- Heart of the Gloom: The Withering Thing or The Dreaming One
- Old Forest: Wrathroot or Shardskin
- The Maze: Minotaur of the Labyrinth or Horned Horror
- Daikara: Rantha the Worm or Varsha the Writhing
- Sandworm Lair: Sandworm Queen
- Dreadfell: The Master
- Reknor: Golbug the Destroyer
- Rak'Shor Pride, Vor Pride, Gorbat Pride, and Grushnak Pride leaders

The ten T1/T2 guardian locations are early-safe. With `t1_t2_boss_priority: true` they are also Archipelago `PRIORITY` locations.

### Zone-entry check manifest

When `zone_exploration_checks` is enabled, checks exist for Trollmire, Norgos Lair, Ruins of Kor'Pul, Scintillating Caves, Rhaloren Camp, Heart of the Gloom, The Maze, Sandworm Lair, Daikara, Old Forest, Dreadfell, Reknor, Gates of Morning, the four Orc Prides, and High Peak.

### Quest check manifest

`quest_checks: major` enables 7 major milestones: Tier-2 starter zones complete, Dreadfell complete, Staff of Absorption ambush survived, East Portal orb secured, Journey East / Far East reached, Orc Prides campaign quest complete, and High Peak orb-command complete.

`quest_checks: major_and_zone` additionally enables the four Tier-2 zone objectives for Old Forest, The Maze, Sandworm Lair, and Daikara.

### Paid shop checks

`shop_checks: non_progression` adds AP parcels to 42 ordinary merchants across Derth (7), Last Hope (11), Elvala (6), Shatur (7), and Gates of Morning (11). `shop_checks_per_store` controls whether each merchant gets 1, 2, or 3 parcels, for 42 / 84 / 126 checks total.

Parcel prices are fixed AP prices:

- Derth / Elvala / Shatur: 50, 100, 200 gold
- Last Hope: 100, 200, 400 gold
- Gates of Morning: 250, 500, 1000 gold

Shop parcels can contain useful/filler/trap items but reject **logical advancement from any world**. The client scouts shop placements with `create_as_hint: 0`, so seeing the parcel contents in the merchant does not create a public Archipelago hint.

## Hint naming cheatsheet

If another player sees a ToME hint, these are the important formats:

```text
Talent item:       Category Name: Talent Name
Stat item:         +5 Strength
Prodigy item:      Prodigy: Prodigy Name
Fallback item:     Vitality: +1 maximum life
Level location:    Advancement 07 — Reward 03
Boss location:     Zone — Guardian/Boss Defeated
Zone location:     Zone — Explored
Quest location:    Quest/Zone — ... Completed
Shop location:     Town — Merchant — Archipelago Parcel 2
Goal location:     Age of Ascendancy — Victory
```

Category/talent/prodigy capitalization comes from the installed ToME runtime catalog, so some native category names are lower-case while others are title-cased.

## Native ToME behavior that remains native

AP boss and campaign checks are additive observers. They do not replace native XP, loot, artifacts, gold, quest rewards, or map progression. AP characters do not receive normal discretionary class/generic/stat/category/prodigy points; those advancement currencies are scrubbed because the corresponding upgrades are owned by Archipelago.

Equipment stat/level eligibility is bypassed for the AP character so random builds can use their tools, while normal inventory/slot constraints remain. AP characters also suppress vanilla antimagic/arcane mutual-exclusion flags so a random seed can contain both systems.

## Death, saves, disconnects, and reconnects

AP progression belongs to the **Archipelago slot**, not a particular corpse. A fresh ToME character bound to the same seed/team/slot can reconstruct the same build and replay the authoritative received-item history; its local level, equipment, and campaign state start over normally.

The Lua addon records locally completed checks in `game.json` even when the AP client is disconnected. When the client reconnects, it compares those checks with the server's confirmed set and sends anything still pending. Received items likewise come from the server's ordered history, so a reconnect should not duplicate an already-applied prefix.

## Main YAML options

The normal default is:

```yaml
name: PlayerName
requires:
  version: 0.6.7
game: "Tales of Maj'Eyal"

"Tales of Maj'Eyal":
  class_tree_count: 6
  generic_tree_count: 4
  prodigy_count: 5
  starting_ranks: 2
  level_ceiling: 40
  zone_exploration_checks: true
  quest_checks: major_and_zone
  shop_checks: non_progression
  shop_checks_per_store: 3
  early_level_max: 10
  t1_t2_boss_priority: true
```

See [Configuration reference](docs/CONFIGURATION_REFERENCE.md) for exact ranges and semantics. Nonempty generic `start_inventory`, `start_inventory_from_pool`, `item_links`, and `exclude_locations` are deliberately rejected for this world; use `starting_ranks` for ToME starters.

Generation now uses **unrestricted only**. There is no player-facing logic-mode option; readiness generation is disabled, including through the core generation API. Existing YAMLs should omit `logic_mode`. Unrestricted logic does not prove that every generated build can finish ToME.

## Building the release artifacts from source

The `.teaa` can be built directly from the repository:

```powershell
python tools/build.py --addon-only
```

A reproducible `.apworld` additionally needs a **fresh schema-2 `runtime-export.json` from ToME 1.7.6 using the current addon**, plus an Archipelago 0.6.7 source checkout. The release catalog intentionally reflects the content/DLC installed in the ToME installation used for that export.

Release packaging requires the test dependencies, Git, and a clean Archipelago checkout at tag `0.6.7`. The packager runs the standalone suite with Lupa required, runs native APWorld tests against the staged catalog, and verifies packaged code/catalog bytes before copying the final APWorld.

Typical Windows flow after launching ToME once with the current addon:

```powershell
python -m pip install -e ".[test]"
python tools/build.py `
  --export "$env:USERPROFILE\T-Engine\4.0\tome\archipelago\runtime-export.json" `
  --ap-root C:\dev\Archipelago `
  --package-apworld
```

That produces/stages the compiled catalog and copies the officially packaged `tome.apworld` into `dist`. See [Installation and build workflow](docs/INSTALL.md) for the full setup, including the pinned AP checkout and clean-world staging requirement.

## Current qualification level

1.0.2 is the current feature-complete release of the design, not a claim that every ToME combination has been exhaustively tested. Core bridge transport and reconnect behavior have been exercised in the real game. The remaining qualification backlog includes full campaigns, broad multiworld play, every optional location family, every installed-DLC/prodigy/resource combination, and crash/save edge cases.

Do not enable this addon alongside Rosen's ToME Archipelago addon. Both declare the internal addon name `archipelago`, but they implement different clients, item models, and seed contracts.

## Project docs

- [Review fixes and verification limits](docs/REVIEW_FIXES.md)
- [Installation and source build](docs/INSTALL.md)
- [Configuration reference](docs/CONFIGURATION_REFERENCE.md)
- [Ruleset](docs/RULESET.md)
- [Dependency model](docs/DEPENDENCY_MODEL.md)
- [Architecture and recovery](docs/ARCHITECTURE.md)
- [Implementation status](docs/IMPLEMENTATION_STATUS.md)
- [Testing](docs/TESTING.md)
- [Validation report](docs/VALIDATION_REPORT.md)
- [Tool reference](docs/TOOL_REFERENCE.md)
- [1.0.2 release notes](docs/1.0.2_RELEASE_NOTES.md)
- [1.0.0 release notes](docs/1.0.0_RELEASE_NOTES.md)

Historical `0.2.x` beta notes are retained under `docs/` as historical records and should not be treated as current setup instructions.

This project's original code is MIT-licensed. ToME, Archipelago, DLC, and third-party libraries remain under their own licenses; game binaries, DLC, and third-party source are not bundled.
