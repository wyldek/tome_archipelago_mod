"""Record explicit operator acknowledgement on systems without our Windows helper.
This does NOT block networking; configure the OS/game beforehand.
"""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tome_ap.mailbox import atomic_write_json
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--mailbox",type=Path,required=True)
p.add_argument("--i-have-disabled-tome-networking",action="store_true",required=True)
a=p.parse_args()
atomic_write_json(a.mailbox/"offline-policy.json",dict(schema=1,mode="operator_confirmed",confirmed=True))
print("Acknowledgement recorded. This utility did not modify your firewall or ToME settings.")
