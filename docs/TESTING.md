# Testing and qualification

## Automated tests

Run from the repository root:

```powershell
python -m pip install -e ".[test]"
python tools/validate.py
```

The Python suite checks deterministic generation, cap-based budgets, stable IDs, option combinations, dependency capabilities/anchors, location allocation, receipt ordering, duplicate copies, wrong-slot rejection, JSON/mailbox validation, and static addon behavior.

`tests/test_lua.py` uses Lupa to execute the real Lua addon against `tests/lua/engine.lua`, a deliberately small fake engine. Plain developer pytest runs may skip this module without Lupa, but `tools/validate.py`, release packaging, and CI require Lupa and refuse that skip. Additional runtime regressions in `tests/test_review_runtime.py` can also execute through a real local Lua 5.4 shared library during restricted development. Fake-engine execution does not certify native T-Engine callback ordering, serialization, or talent side effects.

The APWorld contains native `WorldTestBase`, two-slot fill, and early-item placement tests. The early tests cover tight solo windows with boss priority on and off, repeated talent copies, and a second game's locations receiving ToME talents. `tools/build.py --package-apworld` runs them after staging a real compiled catalog into a clean Archipelago checkout at tag `0.6.7`, before official packaging. The default configuration explicitly enables inherited fill/beatability tests. A separately staged world can be validated with `python tools/validate.py --ap-root C:\dev\Archipelago`.

`tests/test_review_world_contract.py` uses API doubles to exercise actual APWorld method bodies in the standalone suite. It is not a replacement for native AP fill/solver tests. Test results must identify which layer actually ran. The [1.0.2 validation report](VALIDATION_REPORT.md) records the release results; [Review fixes](REVIEW_FIXES.md) preserves an earlier, narrower development run.

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
- Learn a talent that uses a previously unused resource and verify its bar appears in both Classic and Minimalist displays without refilling a spent resource during idle polling.
- Buy a paid parcel, restore an older save, and verify the server-confirmed purchase cannot be made again.

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
| Admin/overflow copy arrives | Valid native/catalog talents outside the rolled categories can initialize their category; repeated ranks obey the cap. Missing/mismatched native definitions stop delivery rather than skipping a receipt. |
| Idle render polling after spending resources | Resource amount, maximum, and regeneration are unchanged by repeated polling. |
| Existing save lacks resource-initialization flags | Adopt resources already used by that save without a refill or cursor reset. |
| A talent starts using a new resource | Its bar appears after the rank is learned; other unused resource bars stay hidden. |
| Unused optional content is absent | Birth validates selected content; unused catalog entries do not by themselves block birth. |
| Missing required selected content | Fail validation before initializing the AP character. |

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
- stale or duplicate confirmation is rejected before gold is removed;
- recording failure refunds gold;
- restoring an older save cannot repurchase a server-confirmed parcel;
- no ordinary inventory transfer for the parcel;
- progression items from any world are rejected by placement rules.

### Victory

The generator uses a separate addressless completion event that follows the modeled access rule of the visible Victory location. Confirm modeled completion with useful, filler, and progression rewards at the visible check. The internal event is excluded from network IDs, receipts, and shuffled item/location budgets.

Verify native Age of Ascendancy victory checks the victory location, reports `CLIENT_GOAL`, and only auto-checks remaining advancement locations—not unfinished boss/zone/quest/shop checks.

## Shared-multiworld acceptance

Use a private multiworld with at least one other game. Verify both directions:

1. A ToME location contains another player's meaningful item and checking it delivers correctly.
2. Another game contains a ToME talent/stat/prodigy item and receiving it mutates the ToME character exactly once.

Repeat at least one check/item while the ToME bridge is disconnected and confirm normal catch-up after reconnect.

## Full-campaign qualification

A generated seed passing unit tests is not proof that its random build can beat ToME. Record full-campaign runs with different races/difficulties/tree counts and especially unusual resource/prodigy/support-tree combinations. Readiness is unavailable. Unrestricted generation still does not prove combat solvability.
