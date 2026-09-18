\
# 1.0 documentation audit summary

This overlay was prepared against GitHub `main` at `a9d1753` plus the already-tested final mailbox/path source.

## Updated for 1.0

- README rewritten as an end-user guide with item/check definitions, hint name formats, exact fixed manifests/counts, reconnect behavior, options, and source-build instructions.
- `/archipelago` / `...\T-Engine\4.0\tome\archipelago` documented everywhere; old `/tome/archipelago` setup wording removed from current docs.
- Offline-policy acknowledgement removed from current setup/requirements. Offline helpers are documented as optional developer tools only.
- Version metadata changed to 1.0.0 in addon, APWorld metadata, Python project metadata, and validation metadata.
- Current status/testing/validation docs updated to distinguish demonstrated core transport from still-unqualified campaign breadth.
- APWeb setup/game docs updated.
- Historical 0.2.x beta notes retained as historical documents.
- Stale Lua mailbox test paths and client mailbox-marker tests updated to match schema 2 and `/archipelago`.

## Release hygiene still to do

- Delete the obsolete repository-root `tome_mailbox_validation_fixed.patch` before tagging.
- Rebuild/replace any tracked old release binary (`release/tome-archipelago.teaa`) from the final 1.0 source, or remove tracked build artifacts and attach them only to the GitHub release.
- Regenerate `SHA256SUMS.json` after all final source/doc changes and release-artifact decisions.
- Build the final APWorld from a fresh schema-2 runtime export produced by the 1.0 addon and package it with Archipelago 0.6.7.
- Run the final tests again after applying this overlay.
