# Tales of Maj'Eyal

The ToME Archipelago integration creates a seed-selected **Archipelago Adventurer** for Tales of Maj'Eyal 1.7.6.

The configured random class/generic counts select player-facing talent categories from a runtime-generated catalog. Technique / Combat Training is always included as an additional mandatory category. Talent items are named `<Category>: <Talent>` and each received copy grants one raw rank. Stat items are named `+5 <Stat>`. Specific prodigies are named `Prodigy: <Name>`.

Selected prodigies may add their own rankable categories. Hard talent dependencies can add support categories and precollect one enabling rank. Precollected ranks are removed from the shuffled item pool, so every shuffled ToME item still corresponds to exactly one active ToME location.

Locations are a configurable mixture of:

- dynamic advancement checks named `Advancement LL — Reward RR`;
- 16 native boss-defeat observers;
- 18 optional zone-entry checks;
- 7 major quest checks plus 4 optional Tier-2 zone objectives;
- 42 eligible merchants with 1–3 optional paid parcels per store;
- `Age of Ascendancy — Victory`.

Fixed world checks consume the existing shuffled reward budget first and advancement checks fill the remainder; normal generation does not manufacture Vitality filler merely to support enabled checks.

Boss checks are additive observations and do not replace native XP, loot, artifacts, gold, quest rewards, or other game rewards. Zone locations historically use `— Explored` names but trigger on entering the configured zone rather than on full map exploration.

Paid shop parcels are optional gold sinks. They scout and display the exact AP item and recipient before purchase, use `create_as_hint: 0`, and reject logical progression items from any world.

AP progression belongs to the AP slot. A fresh ToME character bound to the same seed/team/slot can reconstruct the same build and replay already-received upgrades while local level/equipment/campaign progress starts over normally. Checks recorded while the bridge is disconnected are retained locally and sent after reconnect.

Generation uses unrestricted logic only. There is no player-facing logic-mode option; readiness is disabled. Omit `logic_mode` from player YAMLs. No combat-solvability guarantee is made.

A packaged APWorld must be built from a real schema-2 runtime export produced by the current addon. The resulting catalog reflects the content/DLC installed in the ToME installation used for that build.
