# Exact option definitions and example configurations

The current APWorld options are defined in `apworld/tome/options.py`. The tree-count options describe **random** trees. Technique / Combat Training is always added separately and therefore does not consume a generic-tree slot.

## Build options

### `class_tree_count`

- Range: 1–20
- Default: 6
- Combat Training does not consume this count.

### `generic_tree_count`

- Range: 0–20
- Default: 4
- Mandatory Combat Training is added in addition to this count.

A default `6/4` seed therefore has six random class trees, four random generic trees, and mandatory Combat Training.

### `prodigy_count`

- Range: 0–20
- Default: 5

Specific prodigies are AP items. Prodigies that add rankable talent categories also add those categories' rank items to the seed.

### `starting_ranks`

- Range: 0–2
- Default: 2

These copies are precollected from one seed-selected usable starter talent and removed from the shuffled pool.

### `level_ceiling`

- Range: 10–50
- Default: 40

This is the last level eligible for variable advancement checks. Enabled fixed checks consume the reward/check budget first, and level checks fill whatever budget remains. If the remaining budget is smaller than the number of levels, the generator uses a sparse level schedule instead of creating filler.

### `logic_mode`

- `unrestricted` (default): ToME upgrades are useful rather than AP-logical progression.
- `readiness`: experimental aggregate build-growth heuristic. It is not a combat solver.

## Location options

### `zone_exploration_checks`

- `true` (default) / `false`

Adds the curated T1/T2 and major campaign zone-entry checks. These checks replace level checks within the same item budget; enabling them does not add filler.

### `quest_checks`

- `none`: no curated quest checks
- `major`: seven deterministic major campaign quest milestones
- `major_and_zone` (default): the seven major milestones plus the four Tier-2 zone objectives

Quest checks replace level checks within the same item budget.

### `shop_checks`

- `off`: no paid shop parcels
- `non_progression` (default): paid parcels are added to eligible ordinary merchants, but an item rule forbids AP progression items from being placed in them

There is intentionally **no excluded-shop mode** in this beta. Fully excluded shops would require enough filler/trap items to fill every parcel location, which this world does not currently manufacture.

Eligible cities are Derth, Last Hope, Elvala, Shatur, and Gates of Morning. Zigur, Iron Council, Angolwen, special quest merchants, and quest-gated services are omitted.

### `shop_checks_per_store`

- Range: 1–3
- Default: 3

Controls how many paid parcels appear in each eligible ordinary merchant when `shop_checks` is enabled. With the current 42-store manifest, the values correspond to 42, 84, or 126 shop checks. Shop checks replace level checks and do not add Vitality or other filler to the normal item pool.

### `early_level_max`

- Range: 1–20
- Default: 10

Advancement checks at or below this level may contain another world's explicitly requested `early_items`/`local_early_items`. Level 1 itself has no advancement reward location. Curated T1/T2 exploration, zone-quest, and boss checks remain early-safe independently of this cutoff.

### `t1_t2_boss_priority`

- `true` (default) / `false`

When enabled, the ten standard T1/T2 guardians are Archipelago `PRIORITY` locations. The boss checks still exist when this option is off; they simply become ordinary locations.

## Default YAML

```yaml
name: wyldek
requires:
  version: 0.6.7
game: "Tales of Maj'Eyal"

"Tales of Maj'Eyal":
  class_tree_count: 6
  generic_tree_count: 4
  prodigy_count: 5
  starting_ranks: 2
  level_ceiling: 40
  logic_mode: unrestricted

  zone_exploration_checks: true
  quest_checks: major_and_zone
  shop_checks: non_progression
  shop_checks_per_store: 3
  early_level_max: 10
  t1_t2_boss_priority: true
```

## Item/check budget

Generation first calculates the real shuffled build-reward pool:

```text
all rank copies in selected random trees
+ all rank copies in mandatory Combat Training
+ all rank copies in selected prodigy-granted categories
+ named +5 stat packages
+ selected prodigies
- precollected starter/support ranks
= shuffled item count
= active AP location count
```

With ten ordinary four-talent/5-rank random trees, mandatory Combat Training's seven 5-rank talents, sixty stat packages, five prodigies, and two starter ranks, the illustrative baseline is `298` shuffled rewards/checks.

Enabled boss/zone/quest/shop locations consume that 298-location budget first. Level checks are then generated to fill the remainder. With the current default fixed-check set, the illustrative 298-reward build has 126 paid shop checks and 126 level checks, with **zero generated Vitality filler copies**.

Real seeds may differ because support trees, talent caps/category sizes, and prodigy-added categories come from the compiled runtime catalog.

## Future artifact option

A world-artifact check option is a likely future extension. It is intentionally not exposed yet because enabling a large artifact pool would substantially increase check density and needs an explicit policy for random/non-guaranteed artifacts.
