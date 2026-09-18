# Configuration reference

The current APWorld options are defined in `apworld/tome/options.py`. The tree counts describe **random** categories. Technique / Combat Training is always added separately and does not consume a generic-tree slot.

## Build options

### `class_tree_count`

- Range: 1–20
- Default: 6
- Chooses random player-facing class categories from the compiled runtime catalog.

### `generic_tree_count`

- Range: 0–20
- Default: 4
- Mandatory Combat Training is added in addition to this count.

A default 6/4 seed therefore has six random class categories, four random generic categories, and mandatory Combat Training before prodigy/support expansions.

### `prodigy_count`

- Range: 0–20
- Default: 5

Chooses distinct specific prodigies. A selected prodigy that grants AP-managed rankable categories also adds the applicable category rank items to the seed.

### `starting_ranks`

- Range: 0–2
- Default: 2

Precollects likely offensive starter talent ranks and removes those copies from the shuffled pool. The first rank is seed-selected from likely starter talents in the selected class categories. With two ranks, the second normally goes into the same talent when its cap permits it; otherwise another starter candidate can be used. Selection uses runtime tactical metadata and a fallback; it does not certify every starter/equipment combination.

### Stat packages

The 1.0 APWorld does not expose `stat_packages_per_stat` as a YAML option. It uses **10 copies of each of the six `+5` stat packages** (60 stat items total) when constructing the build.

### `level_ceiling`

- Range: 10–50
- Default: 40

Last level eligible for generated advancement checks. Fixed checks consume the location budget first; level checks fill the remainder across levels 2 through this ceiling. Small builds may use a sparse set of levels rather than creating filler.

### Logic policy (not configurable)

Generation uses unrestricted logic. ToME upgrades are useful rather than AP-logical progression, and no combat-solvability guarantee is made. The public `logic_mode` option has been removed. Omit that key from player YAMLs. Readiness is disabled rather than repaired; attempts to generate it through the internal settings API are also rejected.

## Location options

### `zone_exploration_checks`

- `true` (default) / `false`

Adds 18 curated zone-entry locations. Despite historical `— Explored` names, the check is awarded on entering the configured zone, not on revealing every map tile. These checks replace level checks within the same reward budget.

### `quest_checks`

- `none`: no curated quest locations
- `major`: 7 deterministic major campaign milestones
- `major_and_zone` (default): the 7 major milestones plus 4 Tier-2 zone objectives, for 11 quest locations total

Quest checks replace level checks within the same reward budget.

### `shop_checks`

- `off`: no paid AP parcels
- `non_progression` (default): AP parcels appear in eligible ordinary merchants

A shop parcel may hold useful/filler/trap items but rejects **logical advancement from any world**. The client scouts enabled shop locations and displays the exact item and recipient before purchase. Scouting uses `create_as_hint: 0` and does not create a public hint.

Eligible towns are Derth, Last Hope, Elvala, Shatur, and Gates of Morning. Zigur, Iron Council, Angolwen, special quest merchants, and quest-gated services are not in the current manifest.

### `shop_checks_per_store`

- Range: 1–3
- Default: 3

The current manifest contains 42 merchants. The values therefore produce 42, 84, or 126 shop locations. Parcel prices are fixed at 1x/2x/4x each town's base AP price.

### `early_level_max`

- Range: 1–20
- Default: 10

Advancement locations at or below this level can hold another world's explicitly requested `early_items` / `local_early_items`. Level 1 has no advancement location. Curated T1/T2 boss, zone-entry, and zone-quest checks are independently marked early-safe.

### `t1_t2_boss_priority`

- `true` (default) / `false`

The ten standard T1/T2 guardian locations always exist. When enabled, they are marked Archipelago `PRIORITY`; when disabled they are ordinary locations. Their early-safe status does not depend on this option.

## Unsupported inherited common options

For contract integrity, the world rejects nonempty:

- `start_inventory`
- `start_inventory_from_pool`
- `item_links`
- `exclude_locations`

Use `starting_ranks` rather than custom inventory for normal ToME starters.

## Default YAML

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

## Item/check budget

Generation constructs the exact shuffled build pool:

```text
rank copies from random class categories
+ rank copies from random generic categories
+ rank copies from mandatory Combat Training
+ rank copies from selected prodigy-added categories
+ rank copies from dependency support categories
+ 60 named +5 stat packages
+ selected prodigies
- precollected starter ranks
- precollected dependency ranks
= shuffled item count
= active location count
```

Fixed world checks then consume location slots from that count; the remaining slots become advancement checks.

For the illustrative ordinary 6/4 build with ten four-talent/5-rank random categories, seven 5-rank Combat Training talents, 60 stat packages, 5 prodigies, and 2 starter ranks:

```text
200 random ranks + 35 Combat Training ranks + 60 stats + 5 prodigies - 2 starters = 298
```

With all default fixed-location options enabled, that illustrative seed has 172 fixed checks (16 boss + 18 zone + 11 quest + 126 shop + 1 victory) and 126 advancement checks. Real seeds can differ because the runtime catalog supplies actual caps/category sizes and because prodigy/support categories can expand the build.

Normal generation does not add Vitality filler merely to make the totals match. `Vitality: +1 maximum life` exists as the world's AP filler/admin fallback.
