# Unreleased review fixes

Base: `wyldek/tome_archipelago_mod` commit `e3fe3d0866545b945e1d5634bde0d840f363a2c7`.

This is a source correction set, not a new published release or a claim of full-game qualification. The release files already in the repository are unchanged and do not contain these fixes.

## Changes

1. **Generator completion:** a separate addressless completion event follows the modeled access rule of the visible Victory check. Generator beatability no longer depends on the classification of the reward placed at that check. The event does not add a network item, receipt, check ID, or shuffled-budget entry. The live client still requires native victory before reporting `CLIENT_GOAL`.
2. **Resources:** resource infrastructure and initial refill/regeneration policy run once per resource. Routine polling does not refill spent resources or reset temporary regeneration effects. Old schema-3 saves without the new flags adopt already-active resources without changing resource values or the receipt cursor. Known categories are no longer relearned on every poll; category rank reconciliation uses a cached per-tree index.
3. **Readiness removed from player access:** the APWorld's `LogicMode` class and option field are gone, the readiness sample YAML is deleted, and current examples omit `logic_mode`. Generation rejects internal settings with anything other than `unrestricted`. The unused threshold helper is retained for historical development only; readiness has not been repaired. Existing generated readiness seeds are not migrated or repaired by this patch.
4. **Optional content:** the compiler determines installed, non-excluded prodigies before deriving their bonus, choice, cleanup, and transitive support categories. Missing categories for an installed applicable prodigy still produce an error rather than silently changing its behavior.
5. **Administrative talent delivery:** an out-of-build talent category can be resolved from the installed native registry and the immutable item catalog. Every catalog member is checked before the category or its resources are changed. Repeated deliveries remain subject to the exported rank cap. Unknown/mismatched content still stops synchronization; no receipt is silently skipped.
6. **Runtime validation:** an absent unused catalog talent no longer blocks character creation. Selected build talents and prodigies remain mandatory. This is scoped availability checking, not a guarantee of compatibility with arbitrary gameplay addons or mismatched game versions.
7. **Tests and release gates:** the Lua fixture now implements category lookup, resource definitions, infrastructure talents, and the required actor methods. The test extra includes Lupa. CI and `tools/validate.py` require it; release packaging also checks the AP tag/clean tracked source, executes native APWorld tests against the actual staged catalog, and compares packaged code/catalog bytes to the tested staging directory.
8. **Documentation:** current option/example instructions, resource behavior, completion semantics, and verification limits are updated. Historical release/validation notes remain records of earlier work. Do not enable this addon together with Rosen's different addon using the same internal `archipelago` name.

Shop density/prices, item budgets, native loot, and the intended randomized-build design are unchanged. Broader starter usability and campaign balance recommendations from the review require design decisions and real-game qualification; this patch does not claim to solve them.

## Existing saves and seeds

The internal completion event only affects newly generated AP worlds. It cannot rewrite an already generated multiworld. The addon changes preserve the existing schema-3 identity and receipt cursor and do not intentionally reset an existing unrestricted save. Back up saves before testing an updated addon. A save that already stopped after a partially applied native callback still needs recovery from a known consistent save; this patch does not clear that error or replay the failed callback automatically.

The retained internal `logic_mode: unrestricted` contract field avoids gratuitously changing existing unrestricted contract structure. The public option has been removed: remove `logic_mode` from player YAMLs, including old unrestricted YAMLs. A catalog rebuilt for a different installed content set may still have a different catalog/contract hash.

## Validation recorded for this correction set

A focused regression run completed **68 tests successfully**. It covered core readiness rejection, optional/excluded prodigy filtering, actual addon/JSON execution in a real Lua 5.4 VM against the fake engine, APWorld method wiring against explicit API doubles, and release-validator behavior. The Lua tests cover twelve resource types, idle polling, old-save adoption, valid/invalid administrative delivery, receipt prefix checks, and native-goal reporting. Python compilation of the available source files also passed.

Four negative-control tests were run against the original source and failed as expected: idle mana refill, the out-of-build category grant, absent optional prodigy categories, and the exposed logic-mode option. The corresponding corrected tests pass.

**Not executed in this environment:** the complete original standalone suite through Lupa; the native Archipelago 0.6.7 test/fill suite; GitHub Actions; full release packaging using a real runtime export; or an actual ToME campaign. Lupa and a runnable Archipelago checkout were unavailable here. The native tests and packaging gates are supplied for execution in the release builder's environment, not reported as already passing. Fake-engine tests and AP API doubles cannot certify native callback side effects or combat solvability.

## Validate and rebuild

From the repository root, install the test dependencies and run the full local gate:

```powershell
python -m pip install -e ".[test]"
python tools/validate.py
```

Build/install the corrected exporter addon, then restart ToME and create a fresh runtime export:

```powershell
python tools/build.py --addon-only
```

The file is `dist/tome-archipelago.teaa`. Install it in ToME's `game/addons`, then launch ToME once. Back up/remove conflicting older versions as described in the installation guide.

Use a clean Git checkout of Archipelago at tag `0.6.7`, with its normal dependencies installed. The `worlds/tome` directory must not already exist before the build; remove or move aside only the previous ToME staging directory, not the Archipelago core files.

```powershell
python tools/build.py `
  --export "$env:USERPROFILE\T-Engine\4.0\tome\archipelago\runtime-export.json" `
  --ap-root C:\dev\Archipelago `
  --package-apworld
```

Packaging now runs the full standalone gate and the native APWorld tests. Fix any failures before distributing a release. The output is `dist/tome.apworld` and `dist/tome-archipelago.teaa`; existing files under `release/` are not automatically updated. Perform the real-game and shared-multiworld smoke tests in [Testing](TESTING.md) before replacing published assets.
