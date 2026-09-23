# Dependency model (catalog schema 4)

ToME talent requirements do not describe every mechanical dependency. Some categories can be learned and cast according to their formal requirements while still lacking the thing their talents operate on. Catalog schema 4 keeps these reviewed relationships in generation policy rather than trying to infer arbitrary Lua behavior.

## Exact support dependencies

Use `support_dependencies` when a source tree requires one specific tree/talent pair. The required tree is made available as support and the enabling talent is precollected once.

## Functional capabilities

`capabilities` defines one or more providers for a named mechanic. Each provider names a concrete tree and the minimum talent rank(s) that establish that mechanic. Exactly one installed provider is marked as the deterministic fallback.

`functional_dependencies` maps a source tree to one or more required capabilities. During generation the resolver:

1. prefers the first provider whose tree is already available at character creation;
2. precollects that provider's enabling rank(s);
3. otherwise promotes the reviewed fallback tree to a support tree and precollects its enabling rank(s);
4. resolves dependencies of newly added support trees transitively;
5. deduplicates all free ranks.

A prodigy-gated bonus tree does not satisfy another tree's birth-time dependency merely because it exists in the eventual build. If needed, the dependency resolver promotes a ready provider instead.

Current reviewed capabilities cover Shadows, summon creation, bindable Chronomancy spells, combo generation, alchemist-gem creation, Insanity generation, entropic backlash, undead minion creation, and Alchemist Golem creation.

## Anchor talents

`anchor_talents` handles same-tree bootstraps. If a selected tree's later talents assume its core mechanic already exists, one rank of that core talent is precollected and removed from the shuffled pool. Examples include Call Shadows, Temporal Hounds, Thought-Forms, Prophecy, Golem Power, and several Demented state-machine talents.

## Compatibility boundary

These fields exist only in catalog schema 4. They are fully resolved before slot data is emitted. The generated contract still uses schema 3 fields (`support_trees`, `support_precollects`, concrete tree definitions, and the exact item/location multiset). Mailbox protocol 1 and character-state schema 3 are unchanged.

An old generated seed therefore remains playable with newer runtime code, but it is not retroactively repaired. A new catalog-v4 seed may have different support trees, precollected ranks, item count, location count, catalog hash, and contract hash even when using the same YAML and numeric RNG seed as an older release.
