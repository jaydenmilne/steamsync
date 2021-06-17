#! /usr/bin/env python3

# LICENSE: AGPLv3. See LICENSE at root of repo

from pathlib import Path
from xml.dom import minidom
import json
import subprocess

import defs


def _get_exe_from_config(path_to_config):
    """Get the exe file name (not full path) to launch from the config.

    _get_exe_from_config(Path) -> str
    """
    with path_to_config.open("r", encoding="utf-8") as f:
        doc = minidom.parse(f)
    exes = doc.getElementsByTagName("Executable")
    for exe in exes:
        return exe.getAttribute("Name")


def xbox_collect_games():
    """Collect a list of "Xbox" games from Microsoft Game Store.

    xbox_collect_games() -> List[GameDefinition]
    """
    games = []

    print("Scanning Xbox library...")
    # Run string instead of scriptfile to circumvent powershell ExecutionPolicy
    # ("cannot be loaded because running scripts is disabled on this system").
    script = Path(__file__).resolve().parent / "list_xbox_games.ps1"
    with script.open("r", encoding="utf-8") as f:
        script_code = "".join(f.readlines())
    output = subprocess.check_output(
        ["powershell.exe", str(script_code)], universal_newlines=True
    )
    applist = json.loads(output)

    for app in applist:
        game_name = app["PrettyName"]
        install = Path(app["InstallLocation"])
        config = install / "MicrosoftGame.config"
        # Hopefully filtering by MicrosoftGame excludes non-games. Older games
        # like Prey 2017 are Kind='App' instead of 'Game'.
        if not config.is_file():
            if app["Kind"] == "Game":
                print(
                    f"Warning: Failed to find MicrosoftGame.config file for game '{game_name}'. Expected: {config}"
                )
            continue

        exe_name = _get_exe_from_config(config)
        if not exe_name:
            continue

        exe = install / exe_name
        if not exe.is_file():
            print(
                f"Warning: Failed to find exe for game '{game_name}'. Expected: {exe}"
            )
            continue

        game_def = defs.GameDefinition(
            str(exe),
            game_name,
            app["Appid"],
            str(exe.parent),
            "",
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
