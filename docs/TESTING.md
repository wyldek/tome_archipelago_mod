# Testing and release gates

## What automated tests can establish

The standalone tests can check deterministic selection, actual cap-based
budgets, stable IDs, location allocation, receipt index semantics, duplicate
copies, wrong-slot rejection, and JSON validation. Lupa tests execute Lua
against a deliberately small fake engine. They can detect algorithmic errors
in that environment; they cannot certify real ToME method signatures,
callback ordering, object serialization or talent side effects.

Run:

```powershell
python -m pytest -q -rs
python -m compileall -q tome_ap apworld tools tests ToMEClient.py
```

Install Lupa to execute the Lua tests instead of skipping them. The pytest suite is the supported standalone runner because the Lua test module uses `pytest.importorskip()` when Lupa is unavailable. The APWorld
has its own optional WorldTestBase tests, to run after staging a real
catalog into the pinned Archipelago source checkout.

## Required native-engine smoke test

- Addon loads without a Lua traceback; runtime-export.json is produced.
- A real catalog compiles, and a seed with configured counts generates.
- The AP subclass becomes selectable only with a valid configuration.
- Character has the expected selected trees and no unintended paid trees.
- A first talent rank works, another copy raises it, and overflow is safe.
- +5 packages change the intended raw stat and stop at the declared cap.
- Each allowed prodigy can be granted and actually used/triggered safely.
- Native level-up does not award discretionary advancement currency.
- Non-AP actors and ordinary characters retain native behavior.
- Normal inventory constraints remain; the AP eligibility bypass is scoped.
- Mailbox polling works while awaiting input, without corrupting dialogs.
- Native campaign victory is detected using the correct saved flag/event.

## Persistence matrix

Test at least these boundaries with actual game and bridge processes:

| Scenario | Expected result |
|---|---|
| Bridge reconnects with full history | No duplicate grant |
| Same item ID occurs five times | Five ranks up to the actual cap |
| Game receives no new input/turns | Items still become observable at the supported safe poll point |
| Save immediately before receiving an item, then reload | Correct replay from that save's prefix |
| Kill game after mutation but before normal save | Recovery follows the saved cursor/mutation state |
| Restore an older save after checks were sent | No second item for a previously checked location |
| Complete a check offline | It is submitted on reconnect |
| Server provides unexpected receipt gap | Sync/recovery, not arbitrary skip |
| A grant raises after a native side effect | Stop processing and require consistent recovery |
| Wrong seed/slot contract is present | No grants and no check submission |
| Two bridge processes use one mailbox | Second process is rejected |
| Admin sends an overflow item | Safe cap handling and receipt consumed |
| Unknown item ID arrives | Explicit incompatibility, not silent filler |
| Character dies during receipt arrival | No accidental grant to a dead actor/clone |

## Multiworld acceptance test

Use a small private two-player seed. Place/send a known foreign progression
item through a ToME location, and a known ToME rank through the other game.
Verify exact recipient, location, receipt order, save persistence, and offline
reconnection. Repeat with two ToME slots using distinct mailboxes.

## Full-campaign qualification

Complete multiple real campaigns with the supported content profile and
record: build selection, tree counts, starter items, difficulty/race,
resource availability, native check detection, item pacing, all prodigy
behavior, online isolation, and goal handling. Play at minimum and maximum
supported counts, not only the 6/4 default.

A passing generation test or a large number of simulated seeds is not a
substitute for these campaigns. Readiness thresholds do not prove combat
solvability.

## Feature-completion gates from the workplan

Before claiming the complete workplan is implemented:

1. Audit and implement the intended boss/story/zone location manifest.
2. Qualify every resource family and installed-DLC tree set exported by the full runtime catalog.
3. Replace broad offline isolation with verified native content interception,
   or document broad offline mode as the final supported choice.
4. Audit native quest/birth/prodigy/inscription advancement exceptions.
5. Validate actual addon/APWorld packaging in clean installations.
6. Publish the exact compatibility matrix and known failure cases.
