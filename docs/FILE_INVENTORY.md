# Source file inventory

The release source is organized as follows. Generated `dist/`, local runtime exports/catalogs, virtual environments, caches, logs, and save files are intentionally ignored by Git.

```text
.github/workflows/tests.yml
README.md
LICENSE
ToMEClient.py
DOC_AUDIT_SUMMARY.md            historical 1.0 documentation audit
pyproject.toml

addon/tome-archipelago/
  init.lua
  data/birth.lua
  hooks/load.lua
  overload/mod/class/Archipelago.lua
  overload/mod/class/ArchipelagoJSON.lua
  superload/mod/class/Actor.lua
  superload/mod/class/Game.lua
  superload/mod/class/NPC.lua
  superload/mod/class/Player.lua
  superload/mod/class/Store.lua
  superload/mod/class/uiset/ClassicPlayerDisplay.lua
  superload/mod/class/uiset/Minimalist.lua

apworld/tome/
  .apignore
  __init__.py
  archipelago.json
  bridge_mailbox.py
  client.py
  components.py
  options.py
  docs/en_Tales of Maj'Eyal.md
  docs/setup_en.md
  test/__init__.py
  test/bases.py
  test/test_world.py

tome_ap/
  __init__.py
  catalog.py
  client.py
  generation.py
  locations.py
  mailbox.py
  model.py
  receipts.py

profiles/
  wanderer-full.json

examples/
  wyldek.yaml
  Large_Build.yaml

tools/
  __init__.py
  audit_install.py
  build.py
  compile_catalog.py
  confirm_manual_offline.py
  install_addon.py
  local_demo.py
  status.py
  validate.py
  windows_offline.ps1

tests/
  __init__.py
  _lua_exec.py
  conftest.py
  factories.py
  lua/engine.lua
  test_antimagic_compat.py
  test_baseline_utilities.py
  test_catalog_optional_content.py
  test_client_launch.py
  test_client_scouts.py
  test_dependency_capabilities.py
  test_dependency_profile.py
  test_generation.py
  test_local_demo_seed.py
  test_lua.py
  test_mailbox.py
  test_readiness.py
  test_receipts.py
  test_release_validation.py
  test_review_runtime.py
  test_review_world_contract.py
  test_vanilla_rewards.py

docs/
  1.0.0_RELEASE_NOTES.md
  1.0.2_RELEASE_NOTES.md
  ARCHITECTURE.md
  CONFIGURATION_REFERENCE.md
  DEPENDENCY_MODEL.md
  EARLY_CHECK_AUDIT.md
  FILE_INVENTORY.md
  IMPLEMENTATION_STATUS.md
  INSTALL.md
  REVIEW_FIXES.md
  RULESET.md
  SOURCES.md
  TESTING.md
  TOOL_REFERENCE.md
  VALIDATION_REPORT.md
  validation.json
  0.2.0_BETA_NOTES.md ... 0.2.7_BETA_NOTES.md   # historical only

release/
  NEXT_STEPS.md
  tome-archipelago.teaa
  tome.apworld
```

The two archives in `release/` are tracked 1.0.2 build outputs. Generated `dist/` archives, `catalog.json`, and staged `worlds/tome` directories remain ignored. Archive versions and SHA-256 hashes are recorded in `VALIDATION_REPORT.md`; there is no repository-root `SHA256SUMS.json`. The canonical release build process is documented in `INSTALL.md`.
