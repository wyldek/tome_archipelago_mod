# Architecture, mailbox ownership, and recovery

## Component ownership

**APWorld** selects the seed's immutable character build, constructs exact item/location multisets, applies placement rules, and returns the contract through slot data. Generation never depends on a running local ToME save.

**Python bridge** owns the Archipelago network connection, authoritative received-item history, server-confirmed check state, shop scouting, mailbox validation, identity validation, and bridge snapshots.

**Lua addon** owns the in-game AP character, applies received upgrades, records the applied receipt prefix in the character save, detects gameplay accomplishments, and publishes local check state.

## Mailbox location

The addon uses the T-Engine virtual root:

```text
/archipelago
```

On the normal Windows ToME profile this is commonly:

```text
C:\Users\<you>\T-Engine\4.0\tome\archipelago
```

The old development root `/tome/archipelago` produced an unintended physical `...\tome\tome\archipelago` path and is no longer used.

## Mailbox files

| File | Writer | Meaning |
|---|---|---|
| `mailbox-info.json` | Lua addon | Schema-2 marker containing game/addon identity and `virtual_root: "/archipelago"`. |
| `runtime-export.json` | Lua addon | Schema-2 runtime catalog source from the installed ToME talent registry. |
| `client.json` | Python bridge | Seed identity, immutable contract, complete ordered receipts, server-confirmed checks, connection flag, shop scout metadata. |
| `game.json` | Lua addon | Seed identity, applied receipt count, local check set, goal, revision, game-side error. |
| `bridge-state.json` | Python bridge | Pending/local checks persisted across bridge restarts for the bound identity. |
| `bridge.lock` | Python bridge | Exclusive ownership lock for the mailbox. |

The bridge validates `mailbox-info.json` before using a directory. A stale cached directory is rejected and the picker is shown again. The bridge does not create arbitrary selected directories on the user's behalf.

Only one bridge/demo process may own a mailbox at a time. Do not share one mailbox between unrelated concurrent slots.

## Snapshot direction

```text
Archipelago server
       ↕
Python bridge
       ↓ client.json
       ↑ game.json
ToME addon
```

The addon can continue writing `game.json` while the network client is disconnected. Once reconnected, the bridge merges the local check set into its pending set, compares it with server-confirmed `checked_locations`, and sends the unsent remainder.

## Identity

A run is bound to seed name, team, slot, and contract hash. A save for seed A must not submit checks into seed B even if the visible slot names are identical.

The contract hash covers the generated build/settings/content contract. The local mailbox path and bridge implementation are transport details and are not part of that hash; transport fixes can therefore remain compatible with an already-generated seed when the catalog and contract are unchanged.

Passwords stay in the AP client/network flow and are not copied into game snapshots.

## Receipts

The authoritative received history is ordered and item IDs may repeat:

```text
index 0: Temporal Guardian: Warden's Focus
index 1: +5 Magic
index 2: Temporal Guardian: Warden's Focus
```

The addon stores the length and IDs of the prefix it has successfully applied. It does not deduplicate by item ID. Starting inventory/admin deliveries can use special source-location values and remain valid receipts.

A full-history reconnect does not regrant an already-applied prefix. A shortened authoritative history, changed applied prefix, unknown item, or grant failure is a recovery error; the addon stops rather than skipping arbitrary entries.

## Saves and crashes

The applied receipt prefix and game mutations are saved with the character. Restoring an older save can replay receipts after that save's cursor from the authoritative server history. Server-confirmed locations are idempotent and cannot be collected twice.

ToME is not a transactional database for arbitrary talent callbacks. If a native callback partly mutates state and then errors, the addon records the error and stops further receipt processing. Recover from a known consistent save after fixing the adapter rather than editing the receipt cursor manually.

## Restart policy

AP progression belongs to the slot. A newly created character deliberately bound to the same seed/team/slot can reconstruct the same selected categories and replay received upgrades. Its local ToME campaign state starts over normally; already checked AP locations remain checked server-side.

## Victory

The addon sends `CLIENT_GOAL` only after native Age of Ascendancy victory is observed. The visible `Age of Ascendancy — Victory` remains an ordinary shuffled check. Generator completion instead uses an addressless `Age of Ascendancy — Completion Event` with a locked progression event item, whose access rule follows the visible Victory location. This keeps beatability evaluation independent of the visible reward's classification. The internal event has no network item/location ID and is not included in the contract, receipt stream, or shuffled budget. On victory the addon additionally checks any still-unchecked variable advancement locations, but not uncompleted boss/zone/quest/shop locations.

## Runtime catalog and release builds

Player-facing talent categories are exported dynamically from the installed ToME 1.7.6 runtime. `tools/build.py` requires a schema-2 `runtime-export.json` for a release APWorld and rejects old schema-1 or fixture metadata.

A release builder should install the current addon, launch ToME to regenerate the export, then build against the pinned Archipelago 0.6.7 source checkout. This keeps the APWorld catalog aligned with the addon and installed content set.

### Catalog v4 dependency policy

Catalog schema 4 adds generation-only `capability_providers`, `functional_dependencies`, and `anchor_talents`. They are deliberately not copied into slot data. Generation resolves external requirements into concrete support categories and precollected enabling ranks. Same-tree anchors stay paid and request their specified rank counts through Archipelago's multiworld early-item pool. The network/runtime boundary remains contract schema 3, mailbox protocol 1, and character-state schema 3. A new APWorld rejects an old catalog file rather than silently ignoring v4 policy, while already-generated v3 contracts remain valid inputs to the client/addon.

## Resource initialization and old saves

Each resource receives its native infrastructure and initial AP resource policy once, tracked by a saved `resources_initialized` map. Routine category reconciliation does not refill resources or repeatedly reapply regeneration floors. Existing schema-3 saves without this map adopt the resources used by their selected, extra, or already-known categories without changing current resource values, maxima, regeneration, or the applied receipt cursor. An unseen resource introduced later still initializes once.

Classic and Minimalist UI superloads decide bar visibility from talents actually learned by the AP character. Native pool talents may be initialized earlier without exposing every resource bar at once.

## Paid shop purchase state

The bridge scouts enabled parcel locations and the addon displays their item and recipient. The store adapter checks availability when the confirmation dialog opens and again when purchase is confirmed. It removes gold only after the second check, refunds it if the check cannot be recorded, and removes the parcel after successful recording. Server-confirmed shop checks are reconciled with saved local state, so restoring an older save does not make an already-checked parcel purchasable again.

## Runtime content and administrative grants

Birth verifies native availability for selected categories and prodigies. A missing unused catalog talent no longer blocks birth. This is per-build validation, not a promise of compatibility with arbitrary content modifications. For an out-of-build talent delivery, the addon validates all catalog members of the category against the installed native category and derives its resources before mutating that category. Valid definitions are saved for subsequent deliveries. Unavailable or mismatched content remains an explicit error; receipt skipping and automatic replay after partial mutation are still forbidden.

The compiler determines installed, non-excluded prodigies before adding their bonus, choice, cleanup, or dependent categories. Absent optional prodigies therefore do not demand their unavailable categories.

## Optional native-online isolation

The 1.0.2 runtime has **no offline-policy gate**. Historical/developer tools can still block the ToME executable from native online services during experiments, but `offline-policy.json` is not read by the addon and is not required for synchronization.
