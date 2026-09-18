# Architecture, ownership and recovery

## Component ownership

**APWorld:** selects the seed's immutable character build, creates the exact
item/location multisets, defines the logic mode, and returns the contract
through slot data. It must not inspect a running local ToME save during
multiworld generation.

**Python bridge:** handles the AP connection, full received-item history,
server check acknowledgements, identity validation, and atomic snapshots.
It does not emulate ToME's talent callbacks or decide which talent a reward
means after generation.

**Lua addon:** reads the contract, initializes the AP character, applies game
mutations, records the receipt prefix/cursor in that same character's save,
and detects gameplay accomplishments.

## Mailbox

The integration uses JSON data, not executable Lua or Python written by the
server. The actual schemas and field names are defined in `model.py`,
`mailbox.py`, `client.py` and `Archipelago.lua`. Use those code definitions as
the authority when extending the protocol.

The client snapshot contains identity, immutable contract, complete ordered
receipts and server-confirmed checks. The game snapshot reports identity,
applied receipt count, locally completed checks, goal and diagnostic state.
Use atomic replacement for Python-written snapshots; readers reject
truncated, malformed or incompatible input rather than treating it as an
empty inventory.

Only one bridge or demo process may own a mailbox at a time. A filesystem
lock is provided. The mailbox belongs to one active slot; do not share it
between unrelated characters or clients.

## Identity

A run is bound to seed name, team, slot and contract hash. A character saved
for seed A may not submit its checks into seed B even when both slots have
the same display name. Item/location IDs and contract hashes are stable
content identifiers, not an authentication mechanism against a malicious
local user.

Passwords remain in the AP client/network flow and are not copied into game
files. The local filesystem is treated as trusted user-controlled storage;
this is not a hardened remote administration service.

## Receipts

The authoritative history is an ordered list. Item IDs can repeat by design:

```text
index 0: Flame
index 1: +5 Magic
index 2: Flame
```

The addon stores how much of that ordered prefix it has applied and the
applied IDs. It must not deduplicate by item ID or assume every item has a
normal positive source location. Starting inventory/admin commands can have
special provenance.

A full-history resync does not regrant the already-applied prefix. A gap,
shortened authoritative history or changed applied prefix is a recovery
condition, not permission to skip arbitrary entries. The bridge's
ReceivedItems handling must follow the AP index/reset semantics.

## Save and crash behavior

The character's game mutations and applied prefix are saved together by the
native character-save mechanism. When an older save is restored, unapplied
receipts can be replayed from the server history. Locally completed checks
and server-confirmed checks form an idempotent set; a previously checked
location cannot be farmed for a second item.

This design still needs actual process-crash tests to validate ToME's save
boundaries. It does not claim the engine provides a transactional database
for arbitrary talent callbacks. If a callback partly mutates the character
and then errors, the addon stops further grants and reports the failure.
Restore a known consistent save after fixing the adapter instead of blindly
retrying a partly applied grant.

## Restart policy

A new character deliberately bound to the same AP slot can reconstruct
received upgrades from the same history. Previously checked server locations
remain checked. This allows recovery without creating another set of checks,
but it is a gameplay policy that must be documented for group play. Do not
present it as a normal vanilla permadeath run.

## Victory

The runtime client reports `CLIENT_GOAL` only after the native campaign goal
is detected. That network status is separate from the APWorld's abstract
completion event. The generation code must never read `victory.txt` or a
mailbox to decide where items can be placed.

## Extending the integration

Player-facing trees are exported dynamically from installed subclass birth descriptors. Adding a new resource family still requires resource initialization, prerequisite/support adapters, forced-learning tests, and an actual-use test. Adding a location requires a stable ID, a native completion predicate, save/load recovery, guaranteed availability or an explicit alternate completion route, and a matching generation rule.

Do not bypass errors from the catalog validator. Fail visibly when the seed cannot be represented by the installed content. Prodigy-only trees are cataloged for selected prodigies but are not part of the ordinary random tree roll.
