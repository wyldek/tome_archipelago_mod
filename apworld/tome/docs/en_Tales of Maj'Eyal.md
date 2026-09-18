# Tales of Maj'Eyal

This integration creates a seed-selected Archipelago Adventurer. The configured class/generic counts choose random player-facing talent categories, and Technique / Combat Training is always included as an additional mandatory category. Each received talent item grants one raw rank. Stat rewards add five points to one named stat, and prodigies are individually selected by the seed.

Selected prodigies may add their own rankable talent categories. Those categories add their rank items and an equal number of locations to that seed; ranks received before the corresponding prodigy remain pending until the category is enabled.

Native equipment and loot remain entirely in ToME. AP boss checks are additive observations of native boss defeats: they do not replace XP, drops, artifacts, gold, quest rewards, or other game rewards.

Locations are a configurable mixture of bosses, zone exploration, major/zone quests, paid shop parcels, and variable level-reward locations. Enabled fixed checks consume the existing shuffled reward budget first, and level checks fill the remainder so item and location counts remain exactly equal without manufacturing filler. Paid shop parcels are optional gold sinks that may contain useful/filler/trap items but reject logical progression items. Campaign victory releases only still-unchecked variable advancement rewards and does not invent uncompleted boss/story/shop checks.

AP progression belongs to the AP slot. After a ToME death/restart, a fresh character using the same seed reconstructs the same selected build and replays the items already received by that slot, while local level, equipment, and campaign progress restart normally.

**Unrestricted logic:** the supported default does not model combat strength, survival, real time, or exact campaign pacing. `readiness` is an experimental aggregate heuristic, not a combat-solvability proof.

A real, matching schema-2 ToME runtime catalog is required to build this APWorld. Development fixtures and old schema-1 exports are rejected.

## Location YAML options

The world exposes `zone_exploration_checks`, `quest_checks`, `shop_checks`, `shop_checks_per_store`, `early_level_max`, and `t1_t2_boss_priority`. Shop mode currently supports only `off` and `non_progression`; a fully excluded shop mode is deliberately not offered because it would require a large filler/trap reserve.
