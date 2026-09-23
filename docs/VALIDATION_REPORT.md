# Validation report — 1.0.2 dependency update

**Historical snapshot:** the counts and results below describe the first dependency update. The later 1.0.2 working tree now has 5 exact support rules, 12 functional rules, and 78 same-tree early-anchor rules. Its current Python/Lua suite passes 231 tests, and a separate 200-seed default generator sweep preserved item/location accounting. Same-tree anchors are now paid early-item requests, so the earlier “anchor precollects” check below no longer describes current behavior. Native Archipelago 0.6.7 tests pass 34 cases against a schema-4 catalog reconstructed from the checked-in 1.7.6 metadata snapshot; release validation still needs a fresh runtime export and packaged APWorld. The current early-request and location-capacity audit is in [EARLY_CHECK_AUDIT.md](EARLY_CHECK_AUDIT.md).

This report records what was actually exercised for the 1.0.2 dependency-model update. It does **not** claim exhaustive full-campaign qualification, every DLC/content combination, or broad shared-multiworld qualification.

## Automated source results

From the 1.0.2 source tree:

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

## Final artifact checks

The generated `.teaa` and `.apworld` pass ZIP integrity checks. The APWorld's packaged core files/catalog were compared against the staged source used for the build.

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

## Still not claimed in this environment

- The Lupa-backed Lua execution suite was not run here.
- Upstream Archipelago `WorldTestBase` was not run here because a clean pinned Archipelago 0.6.7 checkout was not present.
- The final APWorld was verified as a structurally valid package assembled from the tested staged world; the official Archipelago `Build APWorlds` command was not run in this environment.
- No exhaustive full campaign was completed specifically on a 1.0.2 dependency-heavy seed.
- No exhaustive live test of every boss/zone/quest/shop observer, prodigy/evolution/resource combination, or save/crash boundary is claimed.
- Unrestricted logic still does not prove combat solvability.
