\
# Ruleset and item/check ownership

## Seed-selected character

A seed chooses `class_tree_count` random class categories and `generic_tree_count` random generic categories. **Technique / Combat Training is mandatory in addition to the configured generic count.** A default 6/4 seed therefore begins with 11 AP-managed base categories before prodigy/support expansion: 6 random class, 4 random generic, and Combat Training.

The categories are available to the character, but the paid ranks are not. Each talent item adds exactly one raw rank to the named talent, up to the runtime-exported cap. AP characters do not receive ordinary discretionary class/generic/category/stat/prodigy point pools.

## Item ownership and names

The generated ToME item types are:

- Talent ranks named `<Category name>: <Talent name>`.
- Stat packages named `+5 Strength`, `+5 Dexterity`, `+5 Constitution`, `+5 Magic`, `+5 Willpower`, and `+5 Cunning`.
- Specific prodigies named `Prodigy: <Prodigy name>`.
- `Vitality: +1 maximum life` exists as the AP filler/admin fallback but is not manufactured by normal ToME build accounting.

Ten copies of each stat package are used by the current 1.0 world. Five distinct prodigies are selected by default.

## Starters and hard dependencies

`starting_ranks` precollects 0–2 usable starter talent copies and removes those copies from the shuffled pool.

A selected category must not contain talents that are permanently unusable solely because another talent/category was not selected. The compiled catalog therefore carries reviewed support dependencies. When an active category has a hard dependency:

- the dependency category is added as a support category if not already active;
- the minimum enabling talent rank is precollected once;
- remaining ranks in the support category are ordinary shuffled items;
- support categories do not consume the configured random class/generic counts;
- dependencies resolve transitively and duplicate free ranks collapse to one copy.

This applies to hard talent/mechanic dependencies, not ordinary equipment conditions such as needing a shield, bow, staff, or two-handed weapon.

## Prodigies

Normal level/stat/quest requirements are bypassed for received AP prodigies. If a selected prodigy adds AP-managed rankable categories, those categories' talent ranks become part of that seed's item pool. Ranks can arrive before the prodigy and remain pending until the category is enabled. Native free ranks created by an evolution are normalized so AP-owned ranks remain governed by received-item history.

The exact set of installed/approved prodigies comes from the runtime export plus the reviewed profile. A release catalog represents the ToME content/DLC installed when that catalog was built.

## Exact pool formula

```text
all rank copies from random class categories
+ all rank copies from random generic categories
+ all rank copies from mandatory Combat Training
+ all rank copies from selected prodigy-added categories
+ all rank copies from dependency support categories
+ 10 copies of each of six named +5 stat packages
+ selected prodigies
- precollected starter ranks
- precollected dependency ranks
= shuffled AP items
= active AP locations
```

The generator uses the actual exported talent caps/category sizes. The familiar 298-item 6/4 example is illustrative, not a fixed global count.

## Locations

Boss checks always exist. Zone-entry checks, quest milestones, and paid shop parcels are configurable. A victory check always exists. All enabled fixed checks consume the existing item/location budget first; the remainder becomes advancement checks distributed from level 2 through `level_ceiling`.

A single level-up can therefore trigger several independent `Advancement LL — Reward RR` locations. If a small build has fewer remaining advancement slots than eligible levels, only a sparse subset of levels receives a check.

### Boss checks

Boss checks are **observers only**. The native death path executes normally; XP, drops, artifacts, gold, quest state, and other ToME rewards remain untouched. AP never replaces a boss drop with an AP item.

### Zone checks

Zone checks are awarded when the AP character enters the configured zone. The location names retain `— Explored` for most zones, but full tile/map exploration is not required.

### Quest checks

Quest checks watch deterministic native quest state/sub-state transitions. Choice branches that represent the same milestone can collapse to one AP location, such as the East Portal orb outcome.

### Shop checks

Paid shop parcels are optional gold sinks. Their Archipelago item rule forbids `item.advancement`, so logical progression from **any world** cannot be hidden behind the ToME gold economy. Useful/filler/trap items are legal. The merchant shows the scouted item and recipient before purchase.

### Victory

Native Age of Ascendancy victory checks `Age of Ascendancy — Victory` and also marks any remaining **advancement** locations complete as a safety fallback. It does not fabricate uncompleted boss, zone, quest, or shop checks.

## AP item classification

In `unrestricted` logic, ToME character upgrades are classified useful rather than logical progression. Foreign progression can still be placed in ordinary ToME locations. Paid shop locations independently reject logical advancement from all worlds.

`readiness` is an optional experimental aggregate talent/stat heuristic. It can mark ToME upgrades as progression for placement but is not a combat-solvability proof.

## Death/restart and reconnects

AP progression belongs to the Archipelago slot, not the corpse. A new ToME character started against the same seed/team/slot reconstructs the same build and replays items already received by that slot. Local character level, equipment, and campaign progress restart normally. Server-checked locations remain checked and cannot be farmed by repeated deaths.

The addon can continue recording local checks in `game.json` while the AP client is disconnected. When the bridge reconnects, those pending checks are reconciled with the server's confirmed set and sent as needed.

## Resources and requirements

Talent, prodigy, and equipment eligibility requirements are bypassed where needed for the AP character. When selected categories use a ToME resource, the addon enables the resource's native pool plumbing and provides a modest baseline regeneration policy where required for random-build usability.

Normal inventory/slot constraints remain.

## Antimagic and arcane compatibility

Archipelago Adventurers may receive antimagic and spell/arcane categories in the same seed. For the AP character only, vanilla `forbid_arcane` / `has_arcane_knowledge` mutual-exclusion flags are suppressed. This does not remove the Antimagic category or rewrite its talent effects; it removes cross-system exclusions caused solely by those vanilla compatibility flags. Non-AP characters retain native behavior.

## Native systems that remain native

XP, character level, life progression, gear, artifacts, consumables, inscriptions, gold, crafting, maps, and ordinary loot remain ToME systems. AP owns the selected paid talent ranks, named stat packages, selected prodigies, precollected dependency/starter ranks, and AP location state.
