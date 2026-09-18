"""Single-player protocol simulator for testing ToME before AP installation.

Uses real compiled metadata, not fixture talent names. It is deliberately a
separate seed namespace, so its saves cannot sync into a real multiworld.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from random import Random
import secrets
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tome_ap.catalog import Catalog
from tome_ap.generation import Settings,create_build
from tome_ap.model import Identity,Receipt
from tome_ap.mailbox import (read_json,atomic_write_json,exclusive_bridge,client_snapshot,
                            validate_game_snapshot)

def _saved_seed(saved):
    if not isinstance(saved, dict):
        return None
    seed = saved.get("demo_seed")
    if type(seed) is int and seed > 0:
        return seed
    try:
        seed_name = saved["identity"]["seed_name"]
    except (KeyError, TypeError):
        return None
    prefix = "LOCAL-DEMO-"
    if isinstance(seed_name, str) and seed_name.startswith(prefix):
        try:
            seed = int(seed_name[len(prefix):])
        except ValueError:
            return None
        return seed if seed > 0 else None
    return None

def choose_demo_seed(requested, saved, reset):
    """Explicit seed wins; otherwise resume state unless reset, else make a fresh seed."""
    if requested is not None:
        return requested
    if not reset:
        resumed = _saved_seed(saved)
        if resumed is not None:
            return resumed
    return secrets.randbelow(2**63 - 1) + 1

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog",type=Path,required=True)
    p.add_argument("--mailbox",type=Path,required=True)
    p.add_argument("--seed",type=int,default=None,help="reproducible demo seed; omitted = fresh random seed (or resume existing demo state)")
    p.add_argument("--class-trees",type=int,default=6)
    p.add_argument("--generic-trees",type=int,default=4)
    p.add_argument("--zone-exploration-checks", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--quest-checks", choices=("none", "major", "major_and_zone"), default="major_and_zone")
    p.add_argument("--shop-checks", choices=("off", "non_progression"), default="non_progression")
    p.add_argument("--shop-checks-per-store", type=int, choices=(1, 2, 3), default=3)
    p.add_argument("--early-level-max", type=int, default=10)
    p.add_argument("--t1-t2-boss-priority", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--grant-all",action="store_true")
    p.add_argument("--reset",action="store_true")
    a=p.parse_args()
    a.mailbox.mkdir(parents=True,exist_ok=True)
    cache=a.mailbox/"local-demo-state.json"
    saved=read_json(cache)
    seed=choose_demo_seed(a.seed,saved,a.reset)
    c=Catalog.load(a.catalog)
    settings=Settings(
        class_tree_count=a.class_trees, generic_tree_count=a.generic_trees,
        zone_exploration_checks=a.zone_exploration_checks,
        quest_checks=a.quest_checks, shop_checks=a.shop_checks,
        shop_checks_per_store=a.shop_checks_per_store, early_level_max=a.early_level_max,
        t1_t2_boss_priority=a.t1_t2_boss_priority,
    )
    b=create_build(c,settings,Random(seed));contract=b.contract(c)
    identity=Identity(f"LOCAL-DEMO-{seed}",0,1,contract["contract_hash"])
    items=list(b.pool);Random(seed+1).shuffle(items)
    placements={loc.code:c.items[key].code for loc,key in zip(b.locations,items)}
    item_names={item.code:item.name for item in c.items.values()}
    shop_codes={loc.code for loc in b.locations if loc.event=="shop"}
    scouts=[dict(location=code,item=placements[code],item_name=item_names[placements[code]],
                  player=1,player_name="Local Demo",flags=2)
            for code in sorted(shop_codes)]
    receipts=[Receipt(c.items[k].code,-2,0) for k in b.precollected]
    checked=set();revision=0
    if saved and not a.reset:
        if saved["identity"]!=identity.to_dict():
            raise SystemExit("Mailbox contains another demo. Use a different directory or --reset with a NEW ToME character")
        checked=set(saved["checks"])
        receipts=[Receipt.from_dict(r) for r in saved["receipts"]]
    if a.reset:
        for stale in (a.mailbox/"game.json", a.mailbox/"client.json"):
            try:
                stale.unlink()
            except FileNotFoundError:
                pass
    if a.grant_all:
        for loc in sorted(placements):
            if loc not in checked:
                checked.add(loc);receipts.append(Receipt(placements[loc],loc,1))
    print(f"Demo seed: {identity.seed_name}; {len(b.trees)} active trees; {len(placements)} checks")
    print("Random trees:")
    for tree in b.random_trees:
        print(f"  - {tree}")
    print("Mandatory trees:")
    for tree in b.mandatory_trees:
        print(f"  - {tree}")
    print("Selected prodigies:")
    for item_key in b.prodigies:
        print(f"  - {c.items[item_key].name}")
    if b.bonus_trees:
        print("Prodigy-added trees:")
        for tree in b.bonus_trees:
            print(f"  - {tree}")
    if b.support_trees:
        print("Dependency support trees:")
        for tree in b.support_trees:
            print(f"  - {tree}")
    if b.support_precollects:
        print("Free dependency ranks:")
        for key in b.support_precollects:
            print(f"  - {c.items[key].name}")
    print("Starter receipts:")
    for key in b.starters:
        print(f"  - {c.items[key].name}")
    print(f"Mailbox: {a.mailbox}")
    print("Start ToME and create a NEW Archipelago Adventurer. This is NOT an AP server connection.")
    with exclusive_bridge(a.mailbox/"bridge.lock"):
        try:
            bound_reported=False
            while True:
                revision+=1
                snapshot=client_snapshot(identity,contract,receipts,checked,revision,True,scouts)
                atomic_write_json(a.mailbox/"client.json",snapshot)
                atomic_write_json(cache,dict(demo_seed=seed,identity=identity.to_dict(),checks=sorted(checked),receipts=[r.to_dict() for r in receipts]))
                out=read_json(a.mailbox/"game.json")
                if out:
                    validate_game_snapshot(out,identity,set(placements))
                    if not bound_reported:
                        print(f"ToME handshake received: {out['applied_count']} receipts applied; {len(out['checks'])} checks currently complete")
                        bound_reported=True
                    if out.get("error"):
                        raise SystemExit("ToME integration error: "+str(out["error"]))
                    new=set(out["checks"])-checked
                    for loc in sorted(new):
                        checked.add(loc);receipts.append(Receipt(placements[loc],loc,1))
                    if new:
                        print(f"{len(new)} new checks; {len(checked)}/{len(placements)} complete; {len(receipts)} receipts")
                    if out["goal"]:
                        print("ToME reports native campaign victory.")
                        # Keep publishing so the game can apply final receipts.
                time.sleep(0.5)
        except KeyboardInterrupt:
            snapshot["connected"]=False
            atomic_write_json(a.mailbox/"client.json",snapshot)

if __name__=="__main__":main()
