# Validation report — 1.0.2

## Final 1.0.2 release build (2026-09-23)

The addon was built from the 1.0.2 source and loaded in ToME 1.7.6 with Steam-enabled Possessor content. Its fresh schema-2 export contained 381 runtime trees, 1,882 talents, and 276 player trees. Compiling that export with the reviewed profile produced catalog schema 4 with 291 AP trees, 1,232 item types, and 62 prodigies. Tree keys and item IDs match the 1.0.1 release catalog. The new catalog hash is:

```text
9dbd4427fd52f248212581f75c8c5695f895fc66d54a93cf40ed2ed5249c4e3f
```

The Python/Lua suite passed **231 tests** with Lupa present. The staged world passed **34 native ToME tests** in the pinned Archipelago 0.6.7 checkout, including tight early-item fill and mixed-world placement. Archipelago's official **Build APWorlds** component produced the `.apworld`; its optional dependency updater was disabled because unrelated bundled worlds were missing dependencies. Both release archives pass ZIP integrity checks. The packaged APWorld core/catalog bytes match the tested staged world, and every addon archive member matches the current addon source.

| Artifact | Embedded version | SHA-256 |
| --- | --- | --- |
| `release/tome-archipelago.teaa` | ToME addon 1.0.2; game 1.7.6 | `955550dd4db888a63a6b13254f1b169e50a164f2541f8bd3a28078391dfa7ff7` |
| `release/tome.apworld` | World 1.0.2; minimum AP 0.6.7; catalog schema 4 | `010f245d876b934afd88242f6138e9d6b83b58273247530123393413048e11fe` |

The generated contract remains schema 3, mailbox protocol remains 1, and saved character state remains schema 3. This package validation does not replace a full 1.0.2 live campaign or exhaustive in-game boss, zone, quest, shop, and DLC smoke tests.

## Earlier dependency-update snapshot

**Historical snapshot:** the counts and results below describe the first dependency update. The final 1.0.2 source has 5 exact support rules, 12 functional rules, and 78 same-tree early-anchor rules. Same-tree anchors are now paid early-item requests, so the earlier “anchor precollects” check below no longer describes current behavior. The current early-request and location-capacity audit is in [EARLY_CHECK_AUDIT.md](EARLY_CHECK_AUDIT.md).

This report records what was actually exercised for the 1.0.2 dependency-model update. It does **not** claim exhaustive full-campaign qualification, every DLC/content combination, or broad shared-multiworld qualification.

## Automated source results

During that earlier dependency-update run:

```text
python -m pytest -q -rs
182 passed, 1 skipped
```

and:

```text
python -m compileall -q tome_ap apworld tools tests ToMEClient.py
```

completed successfully.

The skipped module is the Lupa-backed Lua execution suite because Lupa is not installed in this build environment. The release-validation workflow and `tools/validate.py` require Lupa when run in the documented release environment.

## Catalog-v4 dependency validation

The dependency policy was compiled against the same 291-tree / 1,232-item runtime content represented by the 1.0.1 release catalog. The v4 catalog preserves the existing tree definitions, item definitions/IDs, prodigy definitions, and prodigy rules while adding dependency metadata.

Validated catalog policy:

- 34 capability-provider entries;
- 11 functional dependency rules;
- 18 same-tree anchor rules;
- 2 remaining exact support-dependency rules.

A real-catalog generator sweep passed:

- 1,000 default seeds;
- 100 minimal/no-fixed-check seeds;
- 100 small seeds;
- 100 large seeds;
- 100 maximum-tree/no-shop seeds;
- 100 no-starter seeds.

For every generated build in that sweep, validation checked exact pool/location accounting, exported talent-cap accounting, anchor precollects, functional-provider availability, exact support dependencies, and the catalog-v4/contract-v3 boundary.

The eleven functional fallbacks were also forced individually and verified to select the reviewed fallback provider when no natural provider was ready.

## Compatibility checks

- Catalog schema is now **4**.
- Generated contract/slot-data schema remains **3**.
- Mailbox protocol remains **1**.
- Character `archipelago_state` remains schema **3**.
- Contract validation accepts a valid contract-v3 carrying a legacy catalog hash; it does not compare the server-provided contract against the currently bundled catalog hash.
- Stable item definitions/IDs and tree definitions are unchanged from the 1.0.1 compiled catalog.

Existing generated 1.0.x contracts are therefore not rewritten by 1.0.2. They remain self-contained and are accepted by the new client/runtime code, but they do not gain dependency repairs retroactively.

## Earlier artifact comparison

The earlier dependency-update `.teaa` and `.apworld` passed ZIP integrity checks. The APWorld's packaged core files/catalog were compared against the staged source used for that earlier build. The final 1.0.2 artifacts and hashes are reported at the top of this document.

Compared with the generated 1.0.1 artifacts:

- the ToME `.teaa` changes only `init.lua` version metadata; dependency resolution itself is generation-side;
- the APWorld changes the version manifest, catalog/generation/model core, compiled v4 catalog, dependency documentation, and embedded world regression test.

The packaged catalog reports 291 trees, 1,232 item types, 62 prodigies, and catalog hash:

```text
32f30e7d211c880550240702d4e24a6052381fac2fb717989b1badf3b487fda8
```

## Historical real-game transport smoke test

The 1.0 transport design was previously exercised with real ToME 1.7.6 and an Archipelago 0.6.7-hosted seed: seed/team/slot binding, precollected starter delivery, level and Trollmire zone checks, disconnected local check retention, reconnect submission, and resumed reward delivery all worked.

That smoke test validates the transport path retained by 1.0.2. It is **not** a live-game test of every newly curated dependency relationship.

## Not claimed in the earlier dependency-update run

- The Lupa-backed Lua execution suite was not run here.
- Upstream Archipelago `WorldTestBase` was not run here because a clean pinned Archipelago 0.6.7 checkout was not present.
- The final APWorld was verified as a structurally valid package assembled from the tested staged world; the official Archipelago `Build APWorlds` command was not run in this environment.
- No exhaustive full campaign was completed specifically on a 1.0.2 dependency-heavy seed.
- No exhaustive live test of every boss/zone/quest/shop observer, prodigy/evolution/resource combination, or save/crash boundary is claimed.
- Unrestricted logic still does not prove combat solvability.
