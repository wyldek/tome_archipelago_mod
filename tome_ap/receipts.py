"""Reference save model and indexed stream reconciler used by tests/simulator."""
from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
from .model import Receipt, Identity, ValidationError, integer

class ReceiptStream:
    def __init__(self):
        self.items: list[Receipt] = []
        self.need_sync = False

    def accept(self, index: int, incoming: list[Receipt]) -> bool:
        integer(index,"receive index")
        if index == 0:
            self.items = list(incoming)
            self.need_sync = False
            return True
        if index > len(self.items):
            self.need_sync = True
            return False
        overlap = min(len(incoming), len(self.items) - index)
        if self.items[index:index+overlap] != incoming[:overlap]:
            self.need_sync = True
            return False
        self.items.extend(incoming[overlap:])
        return True

@dataclass
class ReferenceSave:
    identity: Identity
    applied_count: int = 0
    receipt_ids: list[int] = field(default_factory=list)
    talent_ranks: dict[str,int] = field(default_factory=dict)
    stats: dict[str,int] = field(default_factory=lambda:dict.fromkeys(("str","dex","con","mag","wil","cun"),10))
    prodigies: set[str] = field(default_factory=set)
    checks: set[int] = field(default_factory=set)
    maximum_life_bonus: int = 0

    def apply(self, identity: Identity, history: list[Receipt], definitions: dict[int,dict]):
        if self.identity != identity:
            raise ValidationError("Cannot apply receipts from another session")
        if len(history) < self.applied_count:
            raise ValidationError("Server history is shorter than the saved cursor; resync first")
        if self.receipt_ids != [r.item for r in history[:self.applied_count]]:
            raise ValidationError("Previously applied receipt prefix changed")
        for receipt in history[self.applied_count:]:
            if receipt.item not in definitions:
                raise ValidationError("Unknown item: do not advance cursor")
            item=definitions[receipt.item]
            kind=item["kind"]
            if kind=="talent":
                self.talent_ranks[item["symbol"]]=min(item["cap"],self.talent_ranks.get(item["symbol"],0)+1)
            elif kind=="stat":
                self.stats[item["stat"]]=min(60,self.stats[item["stat"]]+item["amount"])
            elif kind=="prodigy":
                self.prodigies.add(item["symbol"])
            elif kind=="vitality":
                self.maximum_life_bonus+=item["amount"]
            else:
                raise ValidationError("Unknown grant kind")
            self.receipt_ids.append(receipt.item)
            self.applied_count+=1
