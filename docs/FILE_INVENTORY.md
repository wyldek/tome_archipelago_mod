\
# Source file inventory

The release source is organized as follows. Generated `dist/`, local runtime exports/catalogs, virtual environments, caches, logs, and save files are intentionally ignored by Git.

```text
README.md
LICENSE
ToMEClient.py
SHA256SUMS.json
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
  Readiness_Test.yaml

tools/
  __init__.py
  audit_install.py
  build.py
  compile_catalog.py
  confirm_manual_offline.py
  install_addon.py
  local_demo.py
  status.py
  windows_offline.ps1

tests/
  __init__.py
  factories.py
  test_antimagic_compat.py
  test_baseline_utilities.py
  test_client_launch.py
  test_client_scouts.py
  test_generation.py
  test_local_demo_seed.py
  test_lua.py
  test_mailbox.py
  test_readiness.py
  test_receipts.py
  test_vanilla_rewards.py

docs/
  1.0.0_RELEASE_NOTES.md
  ARCHITECTURE.md
  CONFIGURATION_REFERENCE.md
  FILE_INVENTORY.md
  IMPLEMENTATION_STATUS.md
  INSTALL.md
  RULESET.md
  SOURCES.md
  TESTING.md
  TOOL_REFERENCE.md
  VALIDATION_REPORT.md
  validation.json
  SOURCE_ANCHOR_AUDIT.json
  0.2.0_BETA_NOTES.md ... 0.2.7_BETA_NOTES.md   # historical only

release/
  NEXT_STEPS.md
```

`tome.apworld`, `tome-archipelago.teaa`, `catalog.json`, and the staged `worlds/tome` directory are build outputs. The canonical release build process is documented in `docs/INSTALL.md`.
