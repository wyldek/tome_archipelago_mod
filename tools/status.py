import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tome_ap.mailbox import read_json
p=argparse.ArgumentParser()
p.add_argument("--mailbox",type=Path,required=True)
a=p.parse_args()
client=read_json(a.mailbox/"client.json")
game=read_json(a.mailbox/"game.json")
if not client:
    raise SystemExit("No complete client snapshot found")
print("Seed / slot:",client.get("identity"))
print("Bridge online:",client.get("connected"))
print("Trees:",", ".join(t["key"] for t in client["contract"]["trees"]))
print("Budget:",client["contract"]["shuffled_count"],"network locations")
print("Received:",len(client.get("receipts",[])))
if game:
    print("Applied:",game.get("applied_count"))
    print("Reported checks:",len(game.get("checks",[])))
    print("Goal:",game.get("goal"))
    print("Engine error:",game.get("error"))
else:
    print("No game snapshot yet; check addon enablement, mailbox path, and te4_log.txt")
