# Historical 1.0 documentation audit

This record describes the 1.0 documentation overlay prepared against GitHub `main` at `a9d1753` plus the then-tested mailbox/path source. It is retained for history. For current setup, use the [README](README.md), [installation guide](docs/INSTALL.md), and [1.0.2 validation report](docs/VALIDATION_REPORT.md).

## Updated for 1.0

- README rewritten as an end-user guide with item/check definitions, hint name formats, exact fixed manifests/counts, reconnect behavior, options, and source-build instructions.
- `/archipelago` / `...\T-Engine\4.0\tome\archipelago` documented everywhere; old `/tome/archipelago` setup wording removed from current docs.
- Offline-policy acknowledgement removed from current setup/requirements. Offline helpers are documented as optional developer tools only.
- Version metadata changed to 1.0.0 in addon, APWorld metadata, Python project metadata, and validation metadata.
- Current status/testing/validation docs updated to distinguish demonstrated core transport from still-unqualified campaign breadth.
- APWeb setup/game docs updated.
- Historical 0.2.x beta notes retained as historical documents.
- Stale Lua mailbox test paths and client mailbox-marker tests updated to match schema 2 and `/archipelago`.

## Later resolution

The obsolete patch is absent from the current repository. Both tracked release archives were replaced for 1.0.2 from matching source. The APWorld was compiled from a fresh schema-2 ToME 1.7.6 export and packaged with Archipelago 0.6.7. The source and native APWorld tests passed; artifact hashes are recorded in the [1.0.2 validation report](docs/VALIDATION_REPORT.md). There is no current `SHA256SUMS.json`; the earlier instruction to regenerate it is superseded by that report.
