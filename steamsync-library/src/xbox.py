#! /usr/bin/env python3

# LICENSE: AGPLv3. See LICENSE at root of repo

import json
import os
import subprocess
from pathlib import Path
from xml.dom import minidom

import defs
import util


def _is_game_judging_by_manifest(path_to_manifest, aumid):
    """Determine if app looks like a game from its AppxManifest.

    _is_game_judging_by_manifest(Path) -> str(exe_name), str(encoded_display_name)
    """

    # First, check if this is a Microsoft app
    if "Microsoft.Microsoft" in aumid:
        return None, None

    with path_to_manifest.open("r", encoding="utf-8") as f:
        doc = minidom.parse(f)

    # Check for the Xbox live protocol to determine if it is a game
    protocol = [e.getAttribute("Name").lower() for e in doc.getElementsByTagName("uap:Protocol")]
    if not any(e for e in protocol if "ms-xbl" in e):
        return None, None

    # Get the properly encoded display name eg. # "Tetris® Effect: Connected" instead of "Tetrisr Effect: Connected"
    display_name = doc.getElementsByTagName("uap:VisualElements")[0].getAttribute("DisplayName")
    display_name = str(display_name)
    if "ms-resource" in display_name or "DisplayName" in display_name:
        # Fall back to application name and check again
        display_name = doc.getElementsByTagName("DisplayName")[0].childNodes[0].data
        if "ms-resource" in display_name or "DisplayName" in display_name:
            display_name = None

    exes = doc.getElementsByTagName("Application")
    for exe in exes:
        exe_name = exe.getAttribute("Executable")
        if exe_name and not exe_name.isspace():
            return exe_name, display_name


def xbox_collect_games():
    """Collect a list of "Xbox" games from Microsoft Game Store.

    xbox_collect_games() -> List[GameDefinition]
    """
    games = []

    print("\nScanning Xbox library...")
    # Run string instead of scriptfile to circumvent powershell ExecutionPolicy
    # ("cannot be loaded because running scripts is disabled on this system").
    script = Path(__file__).resolve().parent / "list_xbox_games.ps1"
    with script.open("r", encoding="utf-8") as f:
        script_code = "".join(f.readlines())
    output = subprocess.check_output(["powershell.exe", str(script_code)], universal_newlines=True)
    applist = json.loads(output)

    # Initial filter - Microsoft games usually have a unique "Kind" so if the "Kind" contains App, then we know to ignore it
    filtered = []
    for app in applist:
        if app["Aumid"] is None or app["Kind"] is None:
            continue
        if not ("Microsoft" in app["Aumid"] and "App" in app["Kind"]):
            filtered.append(app)

    for app in filtered:
        args = ""
        game_name = app["PrettyName"]
        install = Path(app["InstallLocation"])

        # Everything should have a manifest.
        config = install / "AppxManifest.xml"
        if not config.is_file():
            print(f"Warning: Failed to find {config.name} file for '{game_name}'. Expected: {config}")
            continue

        exe_name, proper_display_name = _is_game_judging_by_manifest(config, app["Aumid"])
        if not exe_name:
            continue

        # Replace the name with an encoded name if found
        if proper_display_name:
            game_name = proper_display_name

        # We only store the exe to validate the game is real and for
        # migration to uri-based launching.
        exe = install / exe_name

        if not exe.is_file():
            print(f"Warning: Failed to find exe for game '{game_name}'. Expected: {exe}")
            continue
        if not util.is_executable_game(exe):
            print(f"Warning: No permissions to access exe for game: '{game_name}'. Tried to read: {exe}.")
            continue
        working_dir = exe.parent.anchor  # minimal valid path since we won't launch via exe

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


def _test():
    import pprint

    pprint.pprint(
        [
            (
                g.display_name,
                g.executable_path,
                g.app_name,
            )
            for g in xbox_collect_games()
        ]
    )


if __name__ == "__main__":
    _test()
