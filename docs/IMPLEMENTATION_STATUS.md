# Implementation status — 1.0.2

## Release status

**1.0.2 is the current release and feature-complete for the present design, with further live qualification needed.** The matching addon and APWorld are in [`release/`](../release/). The release build passed 231 Python/Lua tests, 34 native Archipelago tests, archive integrity checks, and staged-source comparisons. These checks do not establish that every ToME build, DLC combination, optional check family, or full campaign works in live play.

Core end-to-end behavior has been exercised in the real game: the client bound to a generated slot, two precollected starter ranks arrived, ToME created `game.json`, level and Trollmire zone checks accumulated while the client was disconnected, and reconnecting sent the pending checks and resumed reward delivery.

| Area | Current implementation | Qualification still useful |
|---|---|---|
| Random trees | Runtime-catalog 6/4 default with configurable counts | Large variety of real seeds and DLC sets |
| Mandatory tree | Combat Training added without consuming generic count | Broad real-build use |
| Runtime catalog | Schema-2 installed player-tree export with real IDs/caps/resources/prodigies | Regenerate/inspect for each release content set |
| Starters | 0–2 precollected likely offensive talent ranks | More edge-case starter categories |
| Dependency protection | Catalog-v4 exact dependencies, reusable capabilities, support trees, and same-tree anchors | Continued audit for obscure callback/equipment dependencies |
| Resources | One-time initialization; resource bars appear when a using talent is learned; non-refilling reconciliation; legacy-save adoption | Every unusual resource combination and display layout |
| Prodigies | Broad runtime prodigy pool; bonus-tree expansion; pending ranks | Every evolution/native callback |
| Stats | Named +5 packages; no discretionary AP stat points | Permanent native stat-effect interactions |
| Equipment | AP-scoped eligibility bypass; native slot/inventory constraints remain | Unusual equipment systems |
| Antimagic/arcane | AP-only vanilla mutual-exclusion flags suppressed | More mixed-tree campaigns |
| Boss checks | 16 additive observers | Every alternate guardian and native loot regression |
| Zone checks | 18 configurable zone-entry observers | Full manifest smoke pass |
| Quest checks | 7 major + 4 T2 objectives configurable | Full manifest smoke pass |
| Shop checks | 42 merchants, 1–3 parcels/store, scouted item/recipient display, purchase-time recheck and failed-recording refund | Broad purchase/restock/price tests |
| Advancement checks | Dynamic remainder distributed over levels | Pacing across very small/large builds |
| Victory | Native victory + remaining advancement fallback | Full real campaign completion |
| Mailbox | `/archipelago`, schema-2 marker, validated cached path | Other OS/profile layouts |
| Reconnect | Pending local checks survive client disconnect and flush on reconnect | Longer outages/crash boundaries |
| Save/restart | Ordered receipt-prefix design and same-slot reconstruction | Crash/save torture testing |
| Shared multiworld | Standard AP protocol/client path implemented | More foreign progression and multi-slot sessions |

## Known intentional limits

- The packaged APWorld represents the content/DLC present in the schema-2 runtime export used to build it.
- Boss/zone/quest manifests are curated rather than exhaustive.
- Artifact checks are not implemented.
- Unrestricted is the only supported generation mode and remains intentionally light logic. Readiness is disabled; no combat-solvability guarantee is made.
- Full campaign completion has not been broadly qualified across random builds.
- Some prodigy/evolution and resource combinations are expected to be strange even when mechanically valid.
- The optional developer network-isolation tools remain in the repository, but the runtime no longer requires or reads an offline-policy acknowledgement.

## Qualification backlog after 1.0.2

1. Complete one or more full Age of Ascendancy campaigns on generated builds.
2. Exercise every fixed boss, zone, and quest observer in real ToME.
3. Purchase shop parcels across all towns and test reconnect/restock edge cases.
4. Run shared multiworlds where ToME holds another game's progression and another game holds ToME upgrades.
5. Exercise prodigy-added categories, capability fallbacks, anchors, and support trees in live play.
6. Test death/restart, save rollback, process crash, and long bridge disconnect scenarios.
7. Repeat the clean Archipelago 0.6.7 package and native test checks when the ToME content set or release source changes.
