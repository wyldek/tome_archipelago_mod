"""Compile runtime metadata, stage the APWorld, and package the ToME addon."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tome_ap.catalog import compile_catalog
from tools.validate import validate_ap_root, run_standalone, run_native_world_tests, verify_apworld


def build_addon(destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted((ROOT / "addon/tome-archipelago").rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(ROOT / "addon/tome-archipelago"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--export", type=Path)
    p.add_argument("--profile", type=Path, default=ROOT / "profiles/wanderer-full.json")
    p.add_argument("--ap-root", type=Path)
    p.add_argument("--output", type=Path, default=ROOT / "dist")
    p.add_argument("--addon-only", action="store_true")
    p.add_argument("--package-apworld", action="store_true")
    a = p.parse_args()
    if a.addon_only and a.package_apworld:
        p.error("--addon-only and --package-apworld are mutually exclusive")
    if a.package_apworld and not a.ap_root:
        p.error("--package-apworld requires --ap-root")
    if not a.addon_only and not a.export:
        p.error("--export is required unless --addon-only is used")
    if a.package_apworld:
        try:
            validate_ap_root(a.ap_root)
            run_standalone()
        except RuntimeError as exc:
            p.error(str(exc))
    a.output.mkdir(parents=True, exist_ok=True)
    addon = a.output / "tome-archipelago.teaa"
    build_addon(addon)
    print(f"Addon: {addon}")
    if a.addon_only:
        return
    if not a.export:
        p.error("--export is required unless --addon-only is used")
    export = json.loads(a.export.read_text(encoding="utf-8"))
    if export.get("fixture"):
        p.error("Refusing to build a release APWorld with test metadata")
    profile = json.loads(a.profile.read_text(encoding="utf-8"))
    catalog = compile_catalog(export, profile)
    stage = a.output / "worlds/tome"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(ROOT / "apworld/tome", stage)
    core = stage / "core"
    if core.exists():
        shutil.rmtree(core)
    core.mkdir()
    for name in ("__init__.py", "model.py", "catalog.py", "generation.py", "locations.py"):
        shutil.copy2(ROOT / "tome_ap" / name, core / name)
    (stage / "data").mkdir(exist_ok=True)
    (stage / "data/catalog.json").write_text(catalog.to_json(), encoding="utf-8")
    (a.output / "catalog.json").write_text(catalog.to_json(), encoding="utf-8")
    print(f"Staged world: {stage}")
    if a.ap_root:
        ap = a.ap_root.resolve()
        if not (ap / "Launcher.py").is_file():
            p.error("--ap-root lacks Launcher.py")
        target = ap / "worlds/tome"
        if target.exists():
            raise SystemExit(f"Refusing to overwrite {target}; remove/rename the old version first")
        shutil.copytree(stage, target)
        print(f"Installed development world: {target}")
        if a.package_apworld:
            # Run against the actual compiled catalog staged for this release,
            # not only the small synthetic catalogs in standalone tests.
            run_native_world_tests(ap)
            subprocess.run(
                [sys.executable, str(ap / "Launcher.py"), "Build APWorlds", "--", "Tales of Maj'Eyal"],
                cwd=ap, check=True,
            )
            built = ap / "build/apworlds/tome.apworld"
            if not built.is_file():
                raise SystemExit("AP builder completed but tome.apworld was not found")
            verify_apworld(built, target)
            shutil.copy2(built, a.output / "tome.apworld")
    elif a.package_apworld:
        p.error("--package-apworld requires --ap-root")
    print("Catalog hash:", catalog.hash)
    print(
        f"Catalog content: {len(catalog.trees)} trees, {len(catalog.prodigies)} prodigies, "
        f"mandatory={catalog.mandatory_trees}"
    )


if __name__ == "__main__":
    main()
