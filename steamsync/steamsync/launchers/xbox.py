#! /usr/bin/env python3

# LICENSE: AGPLv3. See LICENSE at root of repo

import json
import os
import subprocess
import xml.parsers.expat
from pathlib import Path
from xml.dom import minidom


import steamsync.defs as defs
import steamsync.defs as defssteams
import steamsync.util as util

import steamsync.launchers.launcher as launcher


class XboxLauncher(launcher.Launcher):
    def collect_games(self) -> list[defs.GameDefinition]:
        """Collect a list of "Xbox" games from Microsoft Game Store."""
        games = []
        applist = []

        print("\nScanning Xbox library...")
        # Run string instead of scriptfile to circumvent powershell ExecutionPolicy
        # ("cannot be loaded because running scripts is disabled on this system").
        script_path = os.path.join(
            Path(__file__).resolve().parent, "static", "list_xbox_games.ps1"
        )
        with open(script_path, "r", encoding="utf-8") as f:
            script_code = "".join(f.readlines())
        try:
            output = subprocess.check_output(
                ["powershell.exe", str(script_code)], universal_newlines=True
            )
            applist = json.loads(output)
        except FileNotFoundError as e:
            print(
                "Couldn't find PowerShell executable, skipping collecting Xbox games."
            )
            raise e

        for app in applist:
            args = ""
            game_name = app["PrettyName"]
            install = Path(app["InstallLocation"])
            # Can't filter on Kind='Game' because older games like Prey 2017 are
            # Kind='App' and some put their name there! Most games have a
            # MicrosoftGame.config.
            config = install / "MicrosoftGame.config"
            if config.is_file():
                exe_name, game_name = _get_details_from_config(config)
            else:
                is_game = app["Kind"] == "Game"
                if is_game:
                    print(
                        f"Warning: Failed to find {config.name} file for game '{game_name}'. Expected: {config}"
                    )

                # Unfortunately, some games (Spiritfarer) don't have a
                # MicrosoftGame file, so we need to try harder. Everything should
                # have a manifest.
                config = install / "AppxManifest.xml"
                if not config.is_file():
                    print(
                        f"Warning: Failed to find {config.name} file for '{game_name}'. Expected: {config}"
                    )
                    continue

                if not is_game and not _is_game_judging_by_manifest(config):
                    continue

                # We have a game, but don't have an exe path (an older game).
                # Doesn't matter because we launch by id.
                exe_name = None

            if exe_name:
                # We only store the exe to validate the game is real and for
                # migration to uri-based launching.
                exe = install / exe_name

                if not exe.is_file():
                    print(
                        f"Warning: Failed to find exe for game '{game_name}'. Expected: {exe}"
                    )
                    continue
                if not util.is_executable_game(exe):
                    print(
                        f"Warning: No permissions to access exe for game: '{game_name}'. Tried to read: {exe}."
                    )
                    continue
                working_dir = (
                    exe.parent.anchor
                )  # minimal valid path since we won't launch via exe

            else:
                exe = ""
                working_dir = Path("/")

            game_def = defs.GameDefinition(
                str(exe),
                game_name,
                app["Aumid"],
                str(working_dir),
                args,
                None,
                defs.TAG_XBOX,
            )
            icon = Path(app["Icon"])
            if not icon.is_file():
                # Spiritfarer actually had Square44x44Logo.targetsize-48.png
                ext = icon.suffix
                icon = icon.with_suffix(".targetsize-48" + ext)
            if not icon.is_file():
                icon = exe
            game_def.icon = str(icon)
            games.append(game_def)

        print(f"Collected {len(games)} games from the Xbox library")
        games.sort()
        return games

    def get_store_id(self) -> str:
        return defs.TAG_XBOX

    def get_display_name(self) -> str:
        return "Xbox"

    def is_installed(self) -> bool:
        return True  # techinically installed for every windows PC


def _get_details_from_config(path_to_config):
    """Get the exe file name (not full path) to launch from the config.

    _get_details_from_config(Path) -> str,str
    """
    with path_to_config.open("r", encoding="utf-8") as f:
        doc = minidom.parse(f)
    # "Tetris® Effect: Connected" instead of "Tetrisr Effect: Connected" from list_xbox_games.
    display_name = doc.getElementsByTagName("ShellVisuals")[0].getAttribute(
        "DefaultDisplayName"
    )
    exes = doc.getElementsByTagName("Executable")
    for exe in exes:
        return exe.getAttribute("Name"), display_name


def _is_game_judging_by_manifest(path_to_manifest):
    """Determine if app looks like a game from its AppxManifest.

    _is_game_judging_by_manifest(Path) -> bool
    """
    with path_to_manifest.open("r", encoding="utf-8", errors="ignore") as f:
        try:
            doc = minidom.parse(f)
        except xml.parsers.expat.ExpatError as e:
            # If unparsable, then it failed to tell us it's a game.
            print(f"Failed to parse manifest and assuming not a game: '{path_to_manifest.as_posix()}'")
            return None

    # Exclude Xbox apps which may otherwise look like a game
    name = [
        e.getAttribute("DisplayName").lower()
        for e in doc.getElementsByTagName("uap:VisualElements")
    ]
    if any(e for e in name if "xbox" in e):
        return None

    # Exclude non-desktop apps
    family = [
        e.getAttribute("Name").lower()
        for e in doc.getElementsByTagName("TargetDeviceFamily")
    ]
    if "windows.desktop" not in family:
        return None

    # Assume anything using Unity or Xbox are a game.
    libs = [e.firstChild.nodeValue for e in doc.getElementsByTagName("Path")]
    game_services = "Microsoft.Xbox.Services.dll" in libs
    unity_game = "UnityPlayer.dll" in libs
    if not game_services and not unity_game:
        # Run out of ways to determine if this is a game, so assume not.
        # print(f"App determined to be not game {path_to_manifest.parent.name}")
        return None
    exes = doc.getElementsByTagName("Application")
    for exe in exes:
        exe_name = exe.getAttribute("Executable")
        return exe_name and not exe_name.isspace()
