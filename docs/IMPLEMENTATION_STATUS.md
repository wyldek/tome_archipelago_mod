# Implementation status

## Current status

**Development beta.** The v0.1.4 local demo was exercised in a real ToME 1.7.6 install: the Archipelago class appeared, the build contract produced the expected abilities, and restarting after death reconstructed the same seed-owned abilities. The v0.2.7 full-catalog/location/prodigy/compatibility expansion still requires the real-game qualification steps below.

| Area | Implemented | Still to qualify |
|---|---|---|
| Random trees | YAML counts; deterministic class/generic sampling | Large-seed playability |
| Mandatory tree | Combat Training added without consuming generic count | Real-game display/receipt pass |
| Runtime catalog | Schema-2 player-tree export; real IDs/caps/resources/prodigies | Regenerate from current addon and inspect counts |
| Resources | Runtime-driven pool enabling plus baseline regen | Every unusual resource combination |
| Prodigies | Broad runtime prodigy pool; bonus-tree expansion; pending ranks | Each evolution/native callback |
| Stats | Specific +5 packages, no discretionary points | Permanent native stat-effect interactions |
| Equipment | AP-scoped requirement bypass; antimagic/arcane mutual exclusion suppressed | Unusual item/slot combinations |
| Locations | Configurable bosses/zones/quests/paid shops + dynamic level remainder + victory | Native store/quest/zone audit |
| Native loot | Explicitly untouched; boss observer runs after native death | Real boss loot regression test |
| Persistence | Receipt index/prefix, save binding, death/restart reconstruction | Crash/reconnect torture tests |
| APWorld/bridge | Generation, slot data, CommonClient bridge | Real two-player exchange and upstream AP tests |
| Online isolation | Offline-policy tooling | Native online-event/vault audit |

## Known intentional limits

- The release catalog is built from a real ToME runtime export. A packaged APWorld therefore represents the content/DLC present in the export used for that release.
- The boss/zone/quest manifests are curated rather than exhaustive. A future artifact option is intentionally deferred until random-generation semantics and check-count expansion are settled.
- Campaign victory auto-completes only remaining variable advancement rewards, not boss/story checks.
- Resource bootstrap values are a compatibility policy for random builds, not a recreation of every native class's starting resource tuning.
- Readiness logic remains heuristic.

## Release gates before a shared group seed

1. Regenerate schema-2 runtime export with the current addon and compile the full catalog.
2. Run local demo with ordinary trees, a non-mana resource tree, and at least one prodigy-expanded seed.
3. Verify a fixed boss checks AP **and still drops exactly through the native loot path**.
4. Verify configured story/zone checks, paid shop parcels, early-item placement, and campaign victory.
5. Build `tome.apworld` with the pinned Archipelago checkout and run upstream world tests.
6. Run a two-player seed where ToME holds foreign progression and another game holds ToME progression.
7. Test death/restart, save/reload, bridge disconnect, offline receipts and receipt replay.
8. Finish a complete Age of Ascendancy campaign before calling the release stable.
