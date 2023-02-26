import subprocess
import json
import os

import steamsync.defs as defs
import steamsync.launchers.launcher as launcher


class LegendaryLauncher(launcher.Launcher):
    """Support for the Legendary launcher

    https://github.com/derrod/legendary"""

    def __init__(self, legendary_command: str = "legendary"):
        self.legendary_command = legendary_command

    def collect_games(self) -> list[defs.GameDefinition]:
        games_dict = {}
        # populate info for all installable games
        games_raw_json = (
            subprocess.Popen(
                [self.legendary_command, "list-games", "--json"], stdout=subprocess.PIPE
            )
            .communicate()[0]
            .decode()
        )
        games_json = json.loads(games_raw_json)
        for entry in games_json:
            # TODO: Map other useful information, like tags?
            games_dict[entry["app_name"]] = {"art": entry["metadata"]["keyImages"][0]}
        games = list()
        raw_json = (
            subprocess.Popen(
                [self.legendary_command, "list-installed", "--json"],
                stdout=subprocess.PIPE,
            )
            .communicate()[0]
            .decode()
        )
        parsed_json = json.loads(raw_json)
        for entry in parsed_json:
            app_name = entry["app_name"]
            launch_args = " launch " + app_name
            display_name = entry["title"]
            install_location = entry["install_path"]
            art_url = None
            icon = os.path.join(install_location, entry["executable"])
            if app_name in games_dict:
                art_url = games_dict[app_name]["art"]

            games.append(
                defs.GameDefinition(
                    self.legendary_command,
                    display_name,
                    app_name,
                    install_location,
                    launch_args,
                    art_url,
                    defs.TAG_LEGENDARY,
                    icon,
                )
            )
        return games

    def get_store_id(self) -> str:
        return defs.TAG_LEGENDARY

    def get_display_name(self) -> str:
        return "legendary"

    def is_installed(self) -> bool:
        return True  # TODO
