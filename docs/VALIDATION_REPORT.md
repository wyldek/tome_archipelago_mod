# Validation report — v0.2.6 beta source

This report describes commands run against this source package in the build environment. It does **not** claim a completed native ToME campaign, live T-Engine execution of the new store UI, or a shared multiworld qualification.

## Automated results

```text
python -m pytest -q -rs
97 passed, 1 skipped
```

- Python/generation/mailbox/receipt/static-addon tests: **PASS — 97 tests**.
- Optional Lua execution tests: **SKIPPED** when Lupa is unavailable.
- Real T-Engine store/quest/zone runtime testing: **NOT RUN here**.
- Upstream Archipelago `WorldTestBase` against a packaged release world: **NOT RUN here** because a pinned AP checkout is not present in this environment.

## v0.2.6 checks specifically validated

- Default 6/4 fixture: 298 shuffled build rewards = 298 locations, with zero Vitality filler copies.
- Default fixed manifest: 126 paid shop locations, 18 zone checks, 11 quest checks, 16 boss checks, 1 victory check, leaving 126 level checks.
- Shop modes expose only `off` and `non_progression`; no excluded mode is implemented.
- One/two/three parcels per store correctly produce 42/84/126 shop locations and level checks absorb the difference.
- Quest modes `none`, `major`, and `major_and_zone` rebalance level checks exactly.
- Disabling zone exploration returns all 18 zone slots to the level-check budget.
- Configurable early-level cutoff and T1/T2 boss priority are reflected in generated location metadata.
- Sparse level schedules work when a small build has fewer remaining level checks than level milestones.
- A build whose enabled fixed checks exceed its shuffled reward count fails generation with an explicit configuration error instead of adding filler.
- The current real compiled catalog smoke calculation produces 317 rewards/checks on the known dependency-heavy seed with zero Vitality filler copies.

## Native checks still required

1. Run local demo with default v0.2.6 settings and confirm only the configured number of shop parcels appear.
2. Purchase a parcel and verify exact gold deduction, one-time AP check, no inventory transfer, and no restock duplication.
3. Generate a real multiworld and verify a progression item cannot be placed in a shop parcel while useful/filler/trap items can.
4. Verify each configurable zone/quest observer in a real ToME 1.7.6 campaign.
5. Verify `early_items` from another world can land only in the configured early band and curated T1/T2 checks.
6. Build/package the APWorld in the pinned Archipelago checkout and run upstream world tests.

## Important nonclaims

- Passing generator tests does not prove every random build can win ToME.
- `readiness` logic is a heuristic, not a combat solver.
- Shop gold affordability is deliberately not AP logic because shop parcels cannot hold progression.
- Artifact checks are not yet implemented; their random-generation policy still needs design work.
