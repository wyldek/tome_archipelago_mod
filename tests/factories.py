from tome_ap.catalog import compile_catalog


def fixture_export(classes=24, generics=20):
    trees, talents, player_trees = [], [], []
    for kind, count in (("class", classes), ("generic", generics)):
        for n in range(count):
            key = f"fixture/{kind}-{n}"
            symbols = [f"T_FIXTURE_{kind.upper()}_{n}_{i}" for i in range(4)]
            trees.append(dict(
                key=key, name=f"Fixture {kind} {n}", generic=kind == "generic",
                symbols=symbols, resources=["mana"], allow_random=True, source="@vanilla@",
            ))
            talents.extend(dict(
                symbol=s, name=f"Skill {i}", cap=5, prodigy=False,
                mode="activated", hide=None, starter=(kind == "class" and i == 0), resources=["mana"],
            ) for i, s in enumerate(symbols))
            player_trees.append(key)

    # Mandatory Combat Training deliberately has seven 5-rank talents like ToME.
    combat = "technique/combat-training"
    combat_symbols = [f"T_FIXTURE_COMBAT_{i}" for i in range(7)]
    trees.append(dict(
        key=combat, name="combat training", generic=True, symbols=combat_symbols,
        resources=["stamina"], allow_random=True, source="@vanilla@",
    ))
    talents.extend(dict(
        symbol=s, name=f"Combat {i}", cap=5, prodigy=False,
        mode="passive", hide=None, starter=False, resources=["stamina"],
    ) for i, s in enumerate(combat_symbols))
    player_trees.append(combat)

    for i in range(12):
        symbol = f"T_FIXTURE_PRODIGY_{i}"
        talents.append(dict(
            symbol=symbol, name=f"Fixture Prodigy {i}", cap=1, prodigy=True,
            mode="passive", hide=None, starter=False, resources=[],
        ))

    export = dict(
        schema=2, fixture=True, game_version="1.7.6", trees=trees, talents=talents,
        player_trees=player_trees,
        resources=[dict(short_name="mana", name="Mana"), dict(short_name="stamina", name="Stamina")],
    )
    profile = dict(
        name="TEST FIXTURE — NOT PLAYABLE",
        mode="runtime-player-trees",
        mandatory_trees=[combat],
        exclude_trees=[], exclude_prodigies=[], prodigy_rules={}, support_dependencies={},
    )
    return export, profile


def fixture_catalog(classes=24, generics=20):
    export, profile = fixture_export(classes, generics)
    return compile_catalog(export, profile)
