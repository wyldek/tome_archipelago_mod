# Early-check capacity audit (1.0.2 development)

## Requested early ranks

The reviewed profile contains 78 anchored trees, 88 distinct anchored talents, and 92 requested ranks across the whole catalog. These are policy totals; a generated seed selects a subset of trees. Combat Training is mandatory and requests two paid early ranks each of Combat Accuracy, Weapons Mastery, Dagger Mastery, and Exotic Weapons Mastery: eight requests in every build.

The largest possible request under the default numeric options (6 random class trees, 4 random generic trees, 5 prodigies, 2 starter ranks) is **33**. Six random class trees contribute at most 11; prodigy bonus class trees contribute at most 8; Combat Training contributes 8; four random generic trees contribute at most 4; and the Fallen and Worldly Knowledge bonus generic trees can contribute one each. A build with 33 requests was constructed and accepted by `create_build` using the current 1.7.6 tree/item metadata and reviewed profile.

The largest possible request within the allowed option ranges (20 random class trees, 20 random generic trees, 20 prodigies, 0 starter ranks) is **55**. Twenty random class trees contribute at most 25; prodigy bonus class trees contribute at most 8; all generic anchors together contribute 22. Support trees add no further early requests: the support tree's anchor rank, when present, is its free enabling rank. A build with 55 requests was constructed and accepted by `create_build`.

These counts are requests to Archipelago's *multiworld* early-item pool. They are not free character-start ranks or local-only placements. A starter or support rank already granted reduces the request for the same item. For instance, one precollected rank of a two-rank request leaves one early request.

## Locations ToME allows for early items

For each generated ToME world, the number of early-safe locations is:

`advancement rewards at levels 2 through min(effective early cutoff, level_ceiling) + 10 early boss checks + (10 if zone exploration is on) + (4 if quest checks are major_and_zone)`.

The ten guardian checks are always present. The ten Tier 1/2 zone-entry checks and four Tier 2 zone-quest checks are optional. Major quests, paid shop parcels, later bosses/zones, and Victory are never early-safe. Shop, zone, and quest checks consume the fixed item/location budget and therefore change the number of advancement checks. Advancement rewards are allocated as evenly as possible over levels 2 through `level_ceiling`, up to 64 per level. `early_level_max` may be 3 through 20, so level 1 itself never supplies an advancement check. Generation increases the effective cutoff only when the chosen build needs more ToME early-safe checks to hold its own requested ranks. If too many slots are tied up in non-early shops and later checks, generation reports that no such cutoff can supply enough non-shop checks. A 100,000-build sweep across the allowed option ranges found level 3 sufficient for every valid current-profile build and found seeds where level 2 was insufficient.

Within the configured 20-level window, the location-ID ceiling is 19 × 64 + 24 = **1,240** early-safe locations. It is achievable with the current catalog: 20 class trees, 20 generic trees, 20 prodigies, no starter ranks, level ceiling/early maximum 20, shops off, zone and full quest checks on, and RNG seed 1869 produce exactly 1,216 early advancement checks plus 24 fixed checks.

| Build and options | Early requests | Early advancement | Early bosses | Early zones | Early quests | Total early-safe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Default options, RNG seed 0 | 11 | 36 | 10 | 10 | 4 | 60 |
| Constructed maximum request with default numeric options | 33 | 108 | 10 | 10 | 4 | 132 |
| Constructed maximum request with maximum tree/prodigy counts, level ceiling 50 | 55 | 198 | 10 | 10 | 4 | 222 |
| Maximum possible early-safe capacity, RNG seed 1869 and settings above | 30 | 1,216 | 10 | 10 | 4 | 1,240 |
| Default seed 0, `early_level_max=3`, zone and quest checks off | 11 | 10 | 10 | 0 | 0 | 20 |

With all default options, ToME has **at least 51** early-safe locations for any valid generated build, which exceeds the 33-request maximum. The conservative lower bound uses the 1.7.6 catalog's six smallest class-tree item budgets (120 ranks), four smallest optional generic-tree budgets (75), mandatory Combat Training (35), 60 stat packages, and five prodigies, minus two starter ranks and at most 17 distinct one-rank external precollects. That leaves at least 276 shuffled items. After the 172 default fixed checks, at least 104 advancement checks remain; the even 39-level schedule gives at least 27 through level 10, plus 24 fixed early-safe checks.

The previous minimum of 1 could leave only ten eligible ToME checks, fewer than this seed's eleven requests. The new minimum of 3 closes that case. The generation-side extension also protects unusual future catalog/option combinations by marking only as many later advancement levels early-safe as needed. Requests may still be fulfilled by other games' early locations in a multiworld. The actual count must be read from the generated spoiler/build because the item pool and advancement schedule change with the chosen trees and option settings.

## Source of counts

The request limits use `profiles/wanderer-full.json`, the checked-in 1.7.6 tree/item metadata snapshot in `local/compiled-catalog.json`, and the current generation algorithm. Location counts follow `tome_ap/generation.py` and `tome_ap/locations.py`. The snapshot is an audit input; 1.0.1 release packages have not been rebuilt.
