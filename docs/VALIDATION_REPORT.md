\
# Validation report — 1.0.0 release preparation

This report records what has actually been exercised for the 1.0 source line. It does **not** claim exhaustive full-campaign or broad shared-multiworld qualification.

## Automated baseline

Using the RC2 source baseline with the final mailbox/path changes overlaid, the current standalone suite produced:

```text
110 passed, 1 skipped
```

and:

```text
python -m compileall -q tome_ap apworld tools tests ToMEClient.py
```

completed successfully.

The one skipped module is the optional Lupa-backed Lua execution suite when Lupa is unavailable. Historical test counts in older 0.2.x notes are not the current release baseline.

## Real-game transport smoke test

The final mailbox design was exercised with real ToME 1.7.6 and an Archipelago 0.6.7-hosted seed:

- the addon wrote to the physical `...\T-Engine\4.0\tome\archipelago` mailbox using virtual root `/archipelago`;
- `mailbox-info.json`, `runtime-export.json`, `client.json`, and `game.json` were present together;
- the AP client successfully authenticated and bound to the generated seed/team/slot;
- two precollected starter talent ranks were received by the ToME character;
- ToME recorded level-2, level-3, and Trollmire zone checks in `game.json`;
- while the AP client was disconnected, those checks remained local rather than being lost;
- reconnecting the AP client sent the pending checks and reward delivery resumed.

This specifically validates the core bidirectional filesystem bridge and reconnect catch-up path that previously failed during development.

## Generator facts verified from current source

- Boss manifest: 16 checks.
- Zone-entry manifest: 18 checks when enabled.
- Quest manifest: 7 major checks or 11 with the four Tier-2 zone objectives.
- Shop manifest: 42 merchants and 1/2/3 parcels per store = 42/84/126 checks.
- Victory: 1 check.
- Default illustrative 298-item build with all fixed checks enabled leaves 126 advancement checks.
- Fixed checks consume the existing reward budget; normal generation does not add Vitality filler merely to accommodate them.
- Shop locations reject logical advancement from any world.

## Still not claimed

- No broad full-campaign sample across random builds.
- No exhaustive live test of every boss/zone/quest/shop observer.
- No exhaustive prodigy/evolution/resource/support-tree matrix.
- No broad crash/save-rollback torture test.
- No claim that `readiness` proves combat solvability.
- Upstream Archipelago `WorldTestBase` should still be run in the clean pinned checkout used to package the final release artifact.
