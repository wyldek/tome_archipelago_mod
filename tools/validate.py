"""Release gates. Requires the test extra; native AP tests need a staged world.

This does not launch ToME or certify real-game campaigns/content combinations.
"""
from __future__ import annotations
import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
AP_TAG = "0.6.7"
PACKAGED_FILES = (
    "__init__.py", "options.py", "client.py", "bridge_mailbox.py", "components.py",
    "core/__init__.py", "core/model.py", "core/catalog.py", "core/generation.py",
    "core/locations.py", "data/catalog.json",
)


def validate_ap_root(root: Path) -> str:
    """Require the documented AP tag and an unmodified tracked core checkout."""
    root = root.resolve()
    if not (root / "Launcher.py").is_file():
        raise RuntimeError(f"{root} does not contain Launcher.py")
    try:
        def git(*args: str) -> str:
            return subprocess.check_output(["git", "-C", str(root), *args],
                                           text=True, stderr=subprocess.PIPE).strip()
        head = git("rev-parse", "HEAD")
        pinned = git("rev-parse", f"refs/tags/{AP_TAG}^{{commit}}")
        if head != pinned:
            raise RuntimeError(f"Release packaging requires the Archipelago {AP_TAG} tag; got {head}")
        git("diff", "--exit-code", "--quiet")
        git("diff", "--cached", "--exit-code", "--quiet")
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            f"Cannot verify a clean Archipelago {AP_TAG} Git checkout. "
            "Fetch that tag, check it out, and restore tracked core modifications. "
            "The untracked staged worlds/tome directory is allowed."
        ) from exc
    return head


def run_standalone() -> None:
    missing = [name for name in ("pytest", "lupa") if importlib.util.find_spec(name) is None]
    if missing:
        raise RuntimeError(
            "Release validation requires " + ", ".join(missing) +
            '. Install the test extra first: python -m pip install -e ".[test]"'
        )
    env = os.environ.copy()
    env["TOME_REQUIRE_LUA_TESTS"] = "1"
    subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT, env=env, check=True)
    subprocess.run([sys.executable, "-m", "compileall", "-q", "tome_ap", "apworld",
                    "tools", "tests", "ToMEClient.py"], cwd=ROOT, check=True)


def run_native_world_tests(root: Path) -> None:
    if not (root / "worlds/tome/test/test_world.py").is_file():
        raise RuntimeError("Stage the current ToME world into AP's worlds/tome before native validation")
    subprocess.run([
        sys.executable, "-m", "unittest", "discover",
        "-s", "worlds/tome/test", "-t", ".", "-v",
    ], cwd=root, check=True)


def verify_apworld(artifact: Path, staged_world: Path) -> None:
    """Ensure the packaged program/catalog are the ones that were staged/tested."""
    with zipfile.ZipFile(artifact) as archive:
        names = archive.namelist()
        roots = [prefix for prefix in ("tome/", "worlds/tome/", "")
                 if prefix + "core/catalog.py" in names]
        if len(roots) != 1:
            raise RuntimeError("Cannot identify one ToME package root in the APWorld")
        for relative in PACKAGED_FILES:
            name = roots[0] + relative
            if names.count(name) != 1:
                raise RuntimeError(f"Missing or duplicate APWorld member: {name}")
            if archive.read(name) != (staged_world / relative).read_bytes():
                raise RuntimeError(f"Packaged APWorld differs from tested source: {relative}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ap-root", type=Path, help="Pinned AP checkout containing the staged worlds/tome")
    args = parser.parse_args()
    try:
        if args.ap_root:
            validate_ap_root(args.ap_root)
        run_standalone()
        if args.ap_root:
            run_native_world_tests(args.ap_root)
    except (RuntimeError, subprocess.CalledProcessError, OSError) as exc:
        raise SystemExit(f"Validation failed: {exc}") from exc


if __name__ == "__main__":
    main()
