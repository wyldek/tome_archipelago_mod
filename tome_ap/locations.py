"""Stable additive ToME accomplishments used as Archipelago locations.

These do not replace native drops, quest rewards, XP, or artifacts. The Lua
addon only observes the accomplishment and reports the corresponding AP check.

`logic_level` is descriptive pacing metadata. `placement` controls Archipelago
fill behavior (default/priority/non_progression), while `early` identifies locations
that are safe targets for another world's explicit ``early_items`` request.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

PRIMARY_ID_BASE = 790_000
ZONE_ID_BASE = 791_000
QUEST_ID_BASE = 792_000
SHOP_ID_BASE = 793_000


@dataclass(frozen=True)
class PrimaryLocation:
    name: str
    code: int
    event: str
    trigger: dict[str, Any]
    logic_level: int = 0
    placement: str = "default"
    early: bool = False

    def to_location_kwargs(self) -> dict[str, Any]:
        return dict(
            name=self.name,
            code=self.code,
            level=self.logic_level,
            reward=1,
            event=self.event,
            trigger=self.trigger,
            placement=self.placement,
            early=self.early,
        )


# Bosses ---------------------------------------------------------------------
# The ten standard T1/T2 guardians are deliberately PRIORITY locations and are
# also part of the early-safe location band.
BOSS_LOCATIONS: tuple[PrimaryLocation, ...] = (
    PrimaryLocation("Trollmire — Guardian Defeated", 790_101, "boss", {
        "zone": "trollmire", "names": ["Prox the Mighty", "Shax the Slimy"]}, 7, "priority", True),
    PrimaryLocation("Norgos Lair — Guardian Defeated", 790_113, "boss", {
        "zone": "norgos-lair", "names": ["Norgos, the Guardian", "Norgos, the Frozen"]}, 7, "priority", True),
    PrimaryLocation("Kor'Pul — Guardian Defeated", 790_102, "boss", {
        "zone": "ruins-kor-pul", "names": ["The Shade", "The Possessed"]}, 7, "priority", True),
    PrimaryLocation("Scintillating Caves — Guardian Defeated", 790_114, "boss", {
        "zone": "scintillating-caves", "names": ["Spellblaze Crystal"]}, 7, "priority", True),
    PrimaryLocation("Rhaloren Camp — Guardian Defeated", 790_115, "boss", {
        "zone": "rhaloren-camp", "names": ["Rhaloren Inquisitor"]}, 7, "priority", True),
    PrimaryLocation("Heart of the Gloom — Guardian Defeated", 790_116, "boss", {
        "zone": "heart-gloom", "names": ["The Withering Thing", "The Dreaming One"]}, 7, "priority", True),
    PrimaryLocation("Old Forest — Guardian Defeated", 790_103, "boss", {
        "zone": "old-forest", "names": ["Wrathroot", "Shardskin"]}, 12, "priority", True),
    PrimaryLocation("The Maze — Guardian Defeated", 790_104, "boss", {
        "zone": "maze", "names": ["Minotaur of the Labyrinth", "Horned Horror"]}, 12, "priority", True),
    PrimaryLocation("Daikara — Guardian Defeated", 790_105, "boss", {
        "zone": "daikara", "names": ["Rantha the Worm", "Varsha the Writhing"]}, 12, "priority", True),
    PrimaryLocation("Sandworm Lair — Sandworm Queen Defeated", 790_106, "boss", {
        "zone": "sandworm-lair", "names": ["Sandworm Queen"]}, 15, "priority", True),

    PrimaryLocation("Dreadfell — The Master Defeated", 790_107, "boss", {
        "zone": "dreadfell", "names": ["The Master"]}, 23),
    PrimaryLocation("Reknor — Golbug Defeated", 790_108, "boss", {
        "zone": "reknor", "names": ["Golbug the Destroyer"]}, 28),
    PrimaryLocation("Rak'Shor Pride — Cleared", 790_109, "boss", {
        "zone": "rak-shor-pride", "names": ["Rak'shor, Grand Necromancer of the Pride"]}, 35),
    PrimaryLocation("Vor Pride — Cleared", 790_110, "boss", {
        "zone": "vor-pride", "names": ["Vor, Grand Geomancer of the Pride"]}, 40),
    PrimaryLocation("Gorbat Pride — Cleared", 790_111, "boss", {
        "zone": "gorbat-pride", "names": ["Gorbat, Supreme Wyrmic of the Pride"]}, 40),
    PrimaryLocation("Grushnak Pride — Cleared", 790_112, "boss", {
        "zone": "grushnak-pride", "names": ["Grushnak, Battlemaster of the Pride"]}, 45),
)


# Zone exploration -----------------------------------------------------------
# A zone check is awarded the first time the AP character enters that zone.
# All T1/T2 dungeon entries are early-safe; later campaign dungeons are normal.
ZONE_LOCATIONS: tuple[PrimaryLocation, ...] = (
    PrimaryLocation("Trollmire — Explored", 791_101, "zone", {"zone": "trollmire"}, 1, "default", True),
    PrimaryLocation("Norgos Lair — Explored", 791_102, "zone", {"zone": "norgos-lair"}, 1, "default", True),
    PrimaryLocation("Ruins of Kor'Pul — Explored", 791_103, "zone", {"zone": "ruins-kor-pul"}, 1, "default", True),
    PrimaryLocation("Scintillating Caves — Explored", 791_104, "zone", {"zone": "scintillating-caves"}, 1, "default", True),
    PrimaryLocation("Rhaloren Camp — Explored", 791_105, "zone", {"zone": "rhaloren-camp"}, 1, "default", True),
    PrimaryLocation("Heart of the Gloom — Explored", 791_106, "zone", {"zone": "heart-gloom"}, 1, "default", True),
    PrimaryLocation("The Maze — Explored", 791_107, "zone", {"zone": "maze"}, 8, "default", True),
    PrimaryLocation("Sandworm Lair — Explored", 791_108, "zone", {"zone": "sandworm-lair"}, 8, "default", True),
    PrimaryLocation("Daikara — Explored", 791_109, "zone", {"zone": "daikara"}, 8, "default", True),
    PrimaryLocation("Old Forest — Explored", 791_110, "zone", {"zone": "old-forest"}, 8, "default", True),

    PrimaryLocation("Dreadfell — Explored", 791_201, "zone", {"zone": "dreadfell"}, 20),
    PrimaryLocation("Reknor — Explored", 791_202, "zone", {"zone": "reknor"}, 25),
    PrimaryLocation("Gates of Morning — Reached", 791_203, "zone", {"zone": "town-gates-of-morning"}, 30),
    PrimaryLocation("Rak'Shor Pride — Explored", 791_204, "zone", {"zone": "rak-shor-pride"}, 32),
    PrimaryLocation("Vor Pride — Explored", 791_205, "zone", {"zone": "vor-pride"}, 32),
    PrimaryLocation("Gorbat Pride — Explored", 791_206, "zone", {"zone": "gorbat-pride"}, 32),
    PrimaryLocation("Grushnak Pride — Explored", 791_207, "zone", {"zone": "grushnak-pride"}, 32),
    PrimaryLocation("High Peak — Explored", 791_208, "zone", {"zone": "high-peak"}, 45),
)


# Major / zone quest checks --------------------------------------------------
# Only deterministic campaign milestones are normal locations. The four T2
# starter-zone objectives are early-safe. Choice-dependent East Portal branches
# collapse to one check through a `subs` list.
ZONE_QUEST_LOCATIONS: tuple[PrimaryLocation, ...] = (
    PrimaryLocation("Old Forest — Zone Quest Completed", 792_101, "quest", {
        "quest": "starter-zones", "sub": "old-forest", "status": "completed"}, 12, "default", True),
    PrimaryLocation("The Maze — Zone Quest Completed", 792_102, "quest", {
        "quest": "starter-zones", "sub": "maze", "status": "completed"}, 12, "default", True),
    PrimaryLocation("Sandworm Lair — Zone Quest Completed", 792_103, "quest", {
        "quest": "starter-zones", "sub": "sandworm-lair", "status": "completed"}, 15, "default", True),
    PrimaryLocation("Daikara — Zone Quest Completed", 792_104, "quest", {
        "quest": "starter-zones", "sub": "daikara", "status": "completed"}, 15, "default", True),
)

MAJOR_QUEST_LOCATIONS: tuple[PrimaryLocation, ...] = (
    PrimaryLocation("Starter Zones — Tier 2 Campaign Quest Completed", 792_201, "quest", {
        "quest": "starter-zones", "status": "done"}, 16),
    PrimaryLocation("Dreadfell — Quest Completed", 792_202, "quest", {
        "quest": "dreadfell", "status": "done"}, 23),
    PrimaryLocation("Staff of Absorption — Orc Ambush Survived", 792_203, "quest", {
        "quest": "staff-absorption", "sub": "survived-ukruk", "status": "completed"}, 25),
    PrimaryLocation("East Portal — Orb Secured", 792_204, "quest", {
        "quest": "east-portal", "subs": ["gave-orb", "withheld-orb"], "status": "completed"}, 27),
    PrimaryLocation("Journey East — Reached the Far East", 792_205, "quest", {
        "quest": "wild-wild-east", "status": "done"}, 30),
    PrimaryLocation("Orc Prides — Campaign Quest Completed", 792_206, "quest", {
        "quest": "orc-pride", "status": "done"}, 42),
    PrimaryLocation("High Peak — Orb Command Completed", 792_207, "quest", {
        "quest": "orb-command", "status": "done"}, 45),
)


QUEST_LOCATIONS: tuple[PrimaryLocation, ...] = ZONE_QUEST_LOCATIONS + MAJOR_QUEST_LOCATIONS

# Paid shop parcels ----------------------------------------------------------
# These are optional gold sinks. Their APWorld item rule forbids progression but
# allows useful/filler/trap items. Special/quest-gated cities and quest-specific merchants are not in
# this list.  Prices are exact AP prices, not normal store multipliers.
SHOP_TOWNS: tuple[tuple[str, str, int, int, tuple[tuple[str, str], ...]], ...] = (
    ("Derth", "town-derth", 50, 2, (
        ("Armoury", "HEAVY_ARMOR"), ("Tanner", "LIGHT_ARMOR"), ("Swordsmith", "SWORD_WEAPON"),
        ("Knives and daggers", "KNIFE_WEAPON"), ("Death from Afar", "ARCHER_WEAPON"),
        ("Herbalist", "POTION"), ("Jewelry", "GEMSTORE"),
    )),
    ("Last Hope", "town-last-hope", 100, 10, (
        ("Hormond & Son Plates", "HEAVY_ARMOR"), ("Rila's Leather", "LIGHT_ARMOR"),
        ("Toxar Alchemical Tailor", "CLOTH_ARMOR"), ("Herk's Cutting Edge", "SWORD_WEAPON"),
        ("Yulek's Tools of the Night", "KNIFE_WEAPON"), ("Vortal's Trees Choppers", "AXE_WEAPON"),
        ("Raber's Blunt Paradise", "MAUL_WEAPON"), ("Dala's Far Reaching Implements", "ARCHER_WEAPON"),
        ("Sarah's Herbal Infusions", "POTION"), ("Sook's Runes and other Harmless Contraptions", "SCROLL"),
        ("Library", "LAST_HOPE_LIBRARY"),
    )),
    ("Elvala", "town-elvala", 50, 2, (
        ("Tailor", "CLOTH_ARMOR"), ("Tanner", "LIGHT_ARMOR"), ("Swordsmith", "SWORD_WEAPON"),
        ("Staff carver", "STAFF_WEAPON"), ("Runemaster", "SCROLL"), ("Shady Library", "ELVALA_LIBRARY"),
    )),
    ("Shatur", "town-shatur", 50, 2, (
        ("Armoury", "HEAVY_ARMOR"), ("Tanner", "LIGHT_ARMOR"), ("Swordsmith", "SWORD_WEAPON"),
        ("Nature's Punch", "MAUL_WEAPON"), ("Silent Hunter", "ARCHER_WEAPON"),
        ("Herbalist", "POTION"), ("Night's Star", "MINDSTAR"),
    )),
    ("Gates of Morning", "town-gates-of-morning", 250, 30, (
        ("Impenetrable Plates", "HEAVY_ARMOR"), ("Quality Leather", "LIGHT_ARMOR"),
        ("Arcane Cloth", "CLOTH_ARMOR"), ("Swordmaster", "SWORD_WEAPON"),
        ("Night Affairs", "KNIFE_WEAPON"), ("Orc Cutters", "AXE_WEAPON"),
        ("Mauling for Brutes", "MAUL_WEAPON"), ("Bows and Slings", "ARCHER_WEAPON"),
        ("Sook's Arcane Goodness", "STAFF_WEAPON"), ("Sarah's Herbal Infusions", "POTION"),
        ("Sook's Runes and other Harmless Contraptions", "SCROLL"),
    )),
)

def _shop_locations() -> tuple[PrimaryLocation, ...]:
    out: list[PrimaryLocation] = []
    shop_index = 0
    multipliers = (1, 2, 4)
    for town, zone, base_price, logic_level, shops in SHOP_TOWNS:
        for shop, store_id in shops:
            shop_index += 1
            for parcel, mult in enumerate(multipliers, 1):
                code = SHOP_ID_BASE + shop_index * 10 + parcel
                price = base_price * mult
                out.append(PrimaryLocation(
                    f"{town} — {shop} — Archipelago Parcel {parcel}",
                    code,
                    "shop",
                    {"zone": zone, "shop": shop, "store": store_id, "parcel": parcel, "price": price},
                    logic_level,
                    "non_progression",
                    False,
                ))
    return tuple(out)


SHOP_LOCATIONS = _shop_locations()
SHOP_LOCATION_COUNT = len(SHOP_LOCATIONS)
assert SHOP_LOCATION_COUNT == 126

VICTORY_LOCATION = PrimaryLocation("Age of Ascendancy — Victory", 790_000, "victory", {}, 0)

PRIMARY_LOCATIONS: tuple[PrimaryLocation, ...] = (
    BOSS_LOCATIONS + ZONE_LOCATIONS + QUEST_LOCATIONS + SHOP_LOCATIONS + (VICTORY_LOCATION,)
)

PRIMARY_NAME_TO_ID = {loc.name: loc.code for loc in PRIMARY_LOCATIONS}
PRIMARY_ID_TO_DEF = {loc.code: loc for loc in PRIMARY_LOCATIONS}
assert len(PRIMARY_NAME_TO_ID) == len(PRIMARY_LOCATIONS)
assert len(PRIMARY_ID_TO_DEF) == len(PRIMARY_LOCATIONS)
