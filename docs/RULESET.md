# Ruleset and configurable budgets

## Seed-selected character

A seed chooses `class_tree_count` random class categories and `generic_tree_count` random generic categories. **Technique / Combat Training is mandatory in addition to that configured generic count.** With the default `6/4` options the character therefore begins with 11 AP-managed base categories: six random class, four random generic, and Combat Training.

The categories are available, but their paid ranks are not. Each received talent item adds exactly one raw rank to the named talent, up to the runtime-exported cap. The player does not receive discretionary class or generic points. Two offensive starter rank copies are precollected by default and removed from the shuffled pool.

## Stats and prodigies

Stat rewards are specific packages (`+5 Strength`, `+5 Magic`, etc.), not unspent stat points. The default pool contains ten packages for each of the six primary stats.

Five distinct specific prodigies are selected by default. Normal level/stat/quest requirements are bypassed. Weird/evolution prodigies remain eligible unless they are proven mechanically nonfunctional. If a selected prodigy grants normal player-spendable categories, every rank in those categories is added to that seed's AP item pool and therefore increases its location count. Ranks can arrive before the prodigy and remain pending until its category is enabled. Native free ranks from evolutions are stripped so those ranks remain AP-owned.

Examples handled by the policy include High Thaumaturgist, Technomancer, Fallen, Lich, Tricks of the Trade, Worldly Knowledge, and Rak'Shor's Cunning. Some evolution effects are intentionally strange on an Adventurer; that is allowed so long as they function.

## Exact pool formula

```text
rank copies from random class trees
+ rank copies from random generic trees
+ rank copies from mandatory Combat Training
+ rank copies from selected prodigy-granted trees
+ specific stat packages
+ selected prodigies
- precollected starter rank copies
= shuffled AP items
= active AP locations
```

For the common case of ten ordinary four-talent/5-rank random trees, mandatory Combat Training's seven 5-rank talents, sixty stat packages, five prodigies, and two starter ranks, the baseline is `200 + 35 + 60 + 5 - 2 = 298` shuffled items/checks. This is only an example: the generator uses actual category sizes/caps and selected prodigy expansions.

## Locations

The beta uses configurable fixed world checks plus a dynamic level-check remainder. Boss checks always exist; zone exploration, quest milestones, and paid shop parcels are YAML-configurable. Enabled fixed checks consume the existing reward budget first, and whatever budget remains is distributed across level milestones. A single level-up may therefore check several independent AP locations, or small builds may use a sparse subset of levels. No filler is created merely to support optional world checks.

Boss checks are **observers only**. The native death path executes first; XP, ordinary drops, artifacts, gold, quest state and every other ToME reward remain untouched. AP never replaces a boss drop with an AP item.

Campaign victory checks the victory location and releases any remaining *advancement reward* locations as a safety fallback, but it does not fabricate uncompleted boss/story checks.

## Death/restart

AP progression belongs to the Archipelago slot, not the corpse. A new ToME character started against the same seed reconstructs the same selected categories and replays all items the AP server has already sent. Local character level, equipment and campaign state restart normally. Already checked AP locations remain checked server-side and cannot be farmed by repeated deaths.

## Resources and requirements

Talent, prodigy and equipment eligibility requirements are bypassed for the AP character. When selected categories use a ToME resource, the addon enables that resource's native pool talent and supplies a modest baseline regeneration policy where needed so a randomly assembled build is usable. This does not replace talent-specific resource interactions.

## Native systems that remain native

XP, levels, life progression, gear, artifacts, consumables, inscriptions, gold, crafting and ordinary loot remain ToME systems. AP owns the selected paid talent ranks, specific stat packages, selected prodigies, and AP location state.

## AP item classification

In unrestricted logic mode, ToME character upgrades are classified useful rather than AP-logical progression; foreign progression can still be placed in ordinary ToME locations. Paid shop parcel locations apply an additional rule forbidding `item.advancement`, so logical progression from any world cannot be hidden behind the gold economy. Useful/filler/trap items remain legal there. Readiness mode is an optional aggregate heuristic and is not a combat-solvability proof.

## Hard talent dependencies

A selected category must not contain talents that are permanently unusable only because another talent/category was not selected by the seed.

The compiled catalog therefore carries reviewed **support dependencies**. When any selected random, mandatory, or prodigy-added tree has a hard talent dependency:

- the dependency's category is added as a **support tree** if it is not already active;
- the minimum enabling talent rank is **precollected at rank 1**;
- the remaining ranks of the support tree remain normal Archipelago items;
- support trees do not consume the configured random class/generic tree counts;
- dependencies resolve transitively and duplicate free ranks are collapsed to one copy.

This applies only to hard talent/mechanic dependencies, not ordinary equipment conditions such as needing a shield, bow, staff, or two-handed weapon.

Current reviewed rules include Psiblades support for Corrosive/Oozing Blades, Temporal Hounds, Thought-Forms, Master Summoner, Time Dilation, and the Golemancy support needed by Advanced Golemancy. The dependency manifest is intentionally explicit because many ToME requirements live inside Lua `on_pre_use`/special requirement code and cannot be safely inferred from runtime metadata alone.
## Antimagic and arcane compatibility

Archipelago Adventurers may receive antimagic and spell/arcane categories in the same seed. Vanilla ToME normally tracks these as mutually exclusive through `forbid_arcane` and `has_arcane_knowledge`. For the AP character only, those compatibility flags are suppressed.

This does not remove the Antimagic talent category or change its talent effects. It removes vanilla cross-system exclusions such as arcane-equipment rejection, antimagic-equipment rejection for spell users, campaign access gates tied to the flags, and antimagic disruption caused solely by knowing spells. Non-AP characters retain vanilla behavior.

