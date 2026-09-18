from worlds.LauncherComponents import Component, Type, components, launch


def run_client(*args: str) -> None:
    from .client import launch_tome_client
    launch(launch_tome_client, name="Tales of Maj'Eyal Client", args=args)


components.append(
    Component(
        "Tales of Maj'Eyal Client",
        func=run_client,
        game_name="Tales of Maj'Eyal",
        component_type=Type.CLIENT,
        supports_uri=True,
        cli=True,
        description="Bridge Archipelago to the Tales of Maj'Eyal addon mailbox.",
    )
)
