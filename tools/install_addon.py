from pathlib import Path
import argparse
import shutil
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description="Install the unpacked development addon without overwriting unrelated files")
p.add_argument("--game-dir",type=Path,required=True)
p.add_argument("--replace",action="store_true")
a=p.parse_args()
addons=a.game_dir/"game/addons"
if not addons.is_dir():raise SystemExit("Expected game/addons under --game-dir")
if (addons/"tome-archipelago.teaa").exists():raise SystemExit("Remove the packaged AP addon before installing the unpacked development version")
target=addons/"tome-archipelago"
if target.exists():
    if not a.replace:raise SystemExit("An AP development addon already exists; use --replace to back it up")
    # Backup is moved outside addons so ToME cannot load both copies.
    backup=a.game_dir/("archipelago-backup-"+datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
    shutil.move(str(target),str(backup));print("Old addon backed up to",backup)
shutil.copytree(ROOT/"addon/tome-archipelago",target)
print("Installed:",target)
print("Enable the addon in ToME. On module load it exports runtime-export.json to the AP mailbox.")
