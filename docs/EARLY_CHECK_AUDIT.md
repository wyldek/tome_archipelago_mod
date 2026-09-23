# Early-check capacity audit (1.0.2 development)

## Requested early ranks

The reviewed profile contains 78 anchored trees, 88 distinct anchored talents, and 92 requested ranks across the whole catalog. These are policy totals; a generated seed selects a subset of trees. Combat Training is mandatory and requests two paid early ranks each of Combat Accuracy, Weapons Mastery, Dagger Mastery, and Exotic Weapons Mastery: eight requests in every build.

The largest possible request under the default numeric options (6 random class trees, 4 random generic trees, 5 prodigies, 2 starter ranks) is **33**. Six random class trees contribute at most 11; prodigy bonus class trees contribute at most 8; Combat Training contributes 8; four random generic trees contribute at most 4; and the Fallen and Worldly Knowledge bonus generic trees can contribute one each. A build with 33 requests was constructed and accepted by `create_build` using the current 1.7.6 tree/item metadata and reviewed profile.

The largest possible request within the allowed option ranges (20 random class trees, 20 random generic trees, 20 prodigies, 0 starter ranks) is **55**. Twenty random class trees contribute at most 25; prodigy bonus class trees contribute at most 8; all generic anchors together contribute 22. Support trees add no further early requests: the support tree's anchor rank, when present, is its free enabling rank. A build with 55 requests was constructed and accepted by `create_build`.

These counts are requests to Archipelago's *multiworld* early-item pool. They are not free character-start ranks or local-only placements. A starter or support rank already granted reduces the request for the same item. For instance, one precollected rank of a two-rank request leaves one early request.

## Locations usable for ToME's early talent ranks

ToME talents are Archipelago `useful` items. In Archipelago 0.6.7, the early-item pass places useful items only in reachable non-priority locations. It reserves `PRIORITY` locations for the early progression pass. For each generated ToME world, the usable early-talent capacity is:

`advancement rewards at levels 2 through min(effective early cutoff, level_ceiling) + (10 if boss priority is off) + (10 if zone exploration is on) + (4 if quest checks are major_and_zone)`.

The ten guardian checks are always present and remain marked early-safe for progression items from other worlds, but default boss priority makes them unusable for ToME's early useful talents. The ten Tier 1/2 zone-entry checks and four Tier 2 zone-quest checks are optional. Major quests, paid shop parcels, later bosses/zones, and Victory do not contribute to this capacity. Shop, zone, and quest checks consume the fixed item/location budget and therefore change the number of advancement checks. Advancement rewards are allocated as evenly as possible over levels 2 through `level_ceiling`, up to 64 per level. `early_level_max` may be 3 through 20, so level 1 itself never supplies an advancement check. Generation increases the effective cutoff only when the chosen build needs more usable ToME checks for its requested ranks. If all advancement levels are exhausted, generation reports the shortage instead of treating priority bosses as available.

Within the configured 20-level window, the location-ID ceiling is 19 × 64 + 24 = **1,240** usable early-talent locations when boss priority is disabled. It is achievable with the current catalog: 20 class trees, 20 generic trees, 20 prodigies, no starter ranks, level ceiling/early maximum 20, shops off, zone and full quest checks on, boss priority off, and RNG seed 1869 produce exactly 1,216 early advancement checks plus 24 fixed checks. With boss priority on, the corresponding ceiling is **1,230**.

| Build and options | Early requests | Early advancement | Usable bosses | Early zones | Early quests | Usable total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Default options, RNG seed 0, priority on | 11 | 36 | 0 | 10 | 4 | 50 |
| Constructed maximum request with default numeric options, priority on | 33 | 108 | 0 | 10 | 4 | 122 |
| Constructed maximum request with maximum tree/prodigy counts, level ceiling 50, priority on | 55 | 198 | 0 | 10 | 4 | 212 |
| Maximum possible capacity, RNG seed 1869 and settings above, priority off | 30 | 1,216 | 10 | 10 | 4 | 1,240 |
| Same maximum-capacity settings, priority on | 30 | 1,216 | 0 | 10 | 4 | 1,230 |
| Default seed 0, `early_level_max=3`, zone and quest checks off, priority on | 11 | 15 | 0 | 0 | 0 | 15 |
| Same tight seed, priority off | 11 | 10 | 10 | 0 | 0 | 20 |

With all default options, ToME has **at least 41 usable early-talent locations** for any valid generated build, which exceeds the 33-request maximum. The conservative lower bound uses the 1.7.6 catalog's six smallest class-tree item budgets (120 ranks), four smallest optional generic-tree budgets (75), mandatory Combat Training (35), 60 stat packages, and five prodigies, minus two starter ranks and at most 17 distinct one-rank external precollects. That leaves at least 276 shuffled items. After the 172 default fixed checks, at least 104 advancement checks remain; the even 39-level schedule gives at least 27 through level 10, plus 14 usable fixed early checks. The ten priority bosses do not enter this bound.

Level 3 alone can still be insufficient when boss priority is on: the tight seed above has ten usable advancement checks at level 3 for eleven requests, so generation extends its effective cutoff to level 4 and supplies fifteen. The generation-side extension marks only as many later advancement levels early-safe as needed. Requests may also be fulfilled by other games' early locations in a multiworld. The APWorld restricts requested names to ToME's early band only during Archipelago's early pass; after the requested copies are placed, remaining copies can fill later checks normally. The actual count must be read from the generated spoiler/build because the item pool and advancement schedule change with the chosen trees and option settings.

Native Archipelago 0.6.7 fill regressions cover tight-window solo fills with boss priority both on and off, repeated Combat Accuracy copies, and a second game's reachable checks receiving requested ToME ranks. The tests assert that requested copies are placed in the early pass and that the remaining copies are legal at later ToME checks.

## Source of counts

The request limits use `profiles/wanderer-full.json`, a local 1.7.6 tree/item metadata snapshot, and the current generation algorithm. Location counts follow `tome_ap/generation.py` and `tome_ap/locations.py`. The final 1.0.2 APWorld was rebuilt from a fresh Steam-enabled ToME runtime export; its 291 tree keys and 1,232 item IDs match the audited snapshot and prior release.
