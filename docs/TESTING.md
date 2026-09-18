\
# Testing and qualification

## Automated tests

Run from the repository root:

```powershell
python -m pytest -q -rs
python -m compileall -q tome_ap apworld tools tests ToMEClient.py
```

The Python suite checks deterministic generation, cap-based budgets, stable IDs, option combinations, location allocation, receipt ordering, duplicate copies, wrong-slot rejection, JSON/mailbox validation, and static addon behavior.

`tests/test_lua.py` uses Lupa to execute the real Lua addon against a deliberately small fake engine. It is skipped when Lupa is unavailable. Fake-engine execution can find algorithmic errors but cannot certify native T-Engine callback ordering, serialization, or talent side effects.

The APWorld also contains optional `WorldTestBase` tests to run after staging a real compiled catalog into the pinned Archipelago 0.6.7 source checkout.

## Required release smoke test

Before publishing a release artifact:

- Build/install the current `.teaa`.
- Launch ToME and verify `...\tome\archipelago\mailbox-info.json` reports schema 2 and `/archipelago`.
- Verify a fresh schema-2 `runtime-export.json` is produced.
- Compile/package the APWorld from that export.
- Connect the launcher client to a generated slot and confirm `/tome` shows the correct mailbox and a seed/team/slot binding.
- Create an Archipelago Adventurer and verify the configured categories and precollected ranks.
- Reach a level with advancement checks and verify `game.json` records them.
- Disconnect the AP client, trigger another check, reconnect, and verify the pending check is sent once.
- Verify at least one post-start received ToME item applies once and survives save/reload.

## Native-engine behavior matrix

| Scenario | Expected result |
|---|---|
| Same item ID occurs multiple times | Each receipt advances the ordered prefix; talent ranks stop at the native exported cap. |
| Client reconnects with full history | Previously applied prefix is not granted again. |
| Client is disconnected when a check occurs | `game.json` retains the local check; reconnect sends the unsent check. |
| Restore older save | Receipts after the saved applied prefix can replay from server history; server-checked locations remain idempotent. |
| Wrong seed/team/slot/contract | No cross-seed grants/check submission. |
| Two bridge processes use one mailbox | Second process fails the exclusive lock. |
| Unknown item ID arrives | Explicit sync incompatibility; do not silently convert it to filler. |
| Native talent grant throws | Stop further grants and surface the error. |
| Character dies during delivery | Do not accidentally grant to a dead actor/clone. |
| Admin/overflow copy arrives | Receipt is consumed safely; rank does not exceed the exported cap. |

## Location qualification

### Bosses

For each configured boss, verify the AP check is recorded **after** the normal death path and that native XP/loot/artifacts/quest state are unchanged.

### Zones

Verify each `— Explored` location triggers on first entry to the configured zone rather than requiring map completion.

### Quests

Verify each native quest status/sub-state maps to exactly one AP location and survives save/reload.

### Shops

For each town tier, verify:

- the configured 1/2/3 parcels per merchant;
- the displayed item and recipient match LocationScout data;
- viewing the store does not create an AP hint (`create_as_hint: 0`);
- exact gold deduction;
- one-time check behavior;
- no ordinary inventory transfer for the parcel;
- progression items from any world are rejected by placement rules.

### Victory

Verify native Age of Ascendancy victory checks the victory location, reports `CLIENT_GOAL`, and only auto-checks remaining advancement locations—not unfinished boss/zone/quest/shop checks.

## Shared-multiworld acceptance

Use a private multiworld with at least one other game. Verify both directions:

1. A ToME location contains another player's meaningful item and checking it delivers correctly.
2. Another game contains a ToME talent/stat/prodigy item and receiving it mutates the ToME character exactly once.

Repeat at least one check/item while the ToME bridge is disconnected and confirm normal catch-up after reconnect.

## Full-campaign qualification

A generated seed passing unit tests is not proof that its random build can beat ToME. Record full-campaign runs with different races/difficulties/tree counts and especially unusual resource/prodigy/support-tree combinations. `readiness` remains a heuristic, not a solver.
