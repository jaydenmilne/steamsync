from pathlib import Path
import json
import os

import steamsync.defs as defs

import steamsync.launchers.launcher as launcher


class EpicGamesStoreLauncher(launcher.Launcher):
    def __init__(self, egs_manifest_path: str):
        self.egs_manifest_path = egs_manifest_path

    def collect_games(self) -> list[defs.GameDefinition]:
        print(f"\nScanning EGS manifest store ({self.egs_manifest_path})...")
        # loop over every .item fiile
        pathlist = Path(self.egs_manifest_path).glob("*.item")
        games = list()

        for path in pathlist:
            # EGS seems to write their json files out as utf-8
            with open(path, "r", encoding="utf-8") as f:
                item = json.load(f)

                app_name = path
                display_name = path

                if "AppName" in item:
                    app_name = item["AppName"]
                if "DisplayName" in item:
                    display_name = item["DisplayName"]

                if item["bIsIncompleteInstall"]:
                    print(
                        f"\t- Skipping '{display_name}' since installation is incomplete"
                    )
                    continue
                elif not item["bIsApplication"]:
                    print(
                        f"\t- Skipping '{display_name}' since it isn't an application"
                    )
                    continue
                elif "games" not in item["AppCategories"]:
                    print(
                        f"\t- Skipping '{display_name}' since it doesn't have the category 'games'"
                    )
                    continue

                if "InstallLocation" not in item:
                    print(
                        f"\t- Skipping '{display_name}' since it apparently doesn't have an 'InstallLocation'"
                    )
                    continue

                install_location = os.path.normpath(item["InstallLocation"])

                if "LaunchExecutable" not in item:
                    print(
                        f"\t- Skipping '{display_name}' since it apparently doesn't have an executable"
                    )
                    continue

                if "LaunchCommand" not in item:
                    print(f"\t- '{display_name}' doesn't have LaunchCommands?")
                    launch_arguments = ""
                else:
                    # I think this is for command line arguments...?
                    launch_arguments = item["LaunchCommand"]

                launch_executable = os.path.normpath(item["LaunchExecutable"])

                if launch_executable[0] in "/\\":
                    # Sanitize bad paths. RiME uses
                    # "/RiME/SirenGame/Binaries/Win64/RiME.exe", which looks
                    # absolute but it isn't.
                    launch_executable = launch_executable[1:]

                executable_path = os.path.join(install_location, launch_executable)

                # found by looking creating a shortcut on the desktop in the EGL and inspecting it
                # using the URI instead of executable_path allows some games with online services
                # to work (eg GTAV)

                if not os.path.exists(executable_path):
                    print(
                        f"\t- Warning: path `{executable_path}` does not exist for game {display_name}, skipping!"
                    )
                    continue

                games.append(
                    defs.GameDefinition(
                        executable_path,
                        display_name,
                        app_name,
                        install_location,
                        launch_arguments,
                        None,
                        defs.TAG_EPIC,
                    )
                )

        print(f"Collected {len(games)} games from the EGS manifest store")
        games.sort()
        return games

    def get_store_id(self) -> str:
        return defs.TAG_EPIC

    def get_display_name(self) -> str:
        return "Epic Games Store"

    def is_installed(self) -> bool:
        return True  # todo
