from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tome_ap.catalog import compile_catalog


def main():
    p = argparse.ArgumentParser(description="Compile ToME runtime metadata into the reusable AP catalog")
    p.add_argument("--export", type=Path, required=True)
    p.add_argument(
        "--profile", type=Path,
        default=Path(__file__).resolve().parents[1] / "profiles" / "wanderer-full.json",
    )
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    export = json.loads(a.export.read_text(encoding="utf-8"))
    profile = json.loads(a.profile.read_text(encoding="utf-8"))
    catalog = compile_catalog(export, profile)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(catalog.to_json(), encoding="utf-8")
    print(f"Compiled {len(catalog.trees)} categories and {len(catalog.items)} item types; hash {catalog.hash}")
    print(
        f"Class: {sum(t.kind == 'class' for t in catalog.trees.values())}; "
        f"generic: {sum(t.kind == 'generic' for t in catalog.trees.values())}; "
        f"prodigies: {len(catalog.prodigies)}; mandatory: {len(catalog.mandatory_trees)}"
    )
    if catalog.mandatory_trees:
        print("Mandatory trees: " + ", ".join(catalog.mandatory_trees))


if __name__ == "__main__":
    main()
