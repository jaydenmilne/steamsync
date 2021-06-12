#! /usr/bin/env python

# LICENSE: AGPLv3. See LICENSE at root of repo

import gzip
import json
from pathlib import Path

import defs


def _load_receipt(path_to_receipt):
    """Load itch's receipt.json.gz.

    _load_receipt(str) -> dict
    """
    with gzip.open(path_to_receipt, "r") as f:
        json_bytes = f.read()

    json_str = json_bytes.decode("utf-8")
    return json.loads(json_str)


def _might_be_exe(exe):
    """Return true if the input might be the exe for a game.

    _might_be_exe(Path) -> bool
    """
    path = str(exe).lower()
    meta_executables = [
        # be sure to lowercase!
        "dxwebsetup",
        "framework",
        "install",
        "notification_helper",
        "unitycrashhandler",
    ]
    is_meta = any(meta for meta in meta_executables if meta in path)
    return not is_meta


def itch_collect_games(path_to_library):
    """Add games in the given path to steam library.

    itch_collect_games(str) -> list(defs.GameDefinition)
    """
    print(f"Scanning itch library folder ({path_to_library})...")
    root = Path(path_to_library)
    games = []
    for receipt in root.glob("*/.itch/receipt.json.gz"):
        r = _load_receipt(receipt)
        g = r["game"]
        title = g["title"]
        if g["classification"] != "game":
            # print(f"Skipping nongame '{title}' -- '{g['classification']}'.")
            continue

        game_root_dir = receipt.parent.parent
        exes = [exe for exe in game_root_dir.glob("*.exe") if _might_be_exe(exe.name)]
        if not exes:
            # Look one level deeper.
            exes = [
                exe for exe in game_root_dir.glob("*/*.exe") if _might_be_exe(exe.name)
            ]
        if not exes:
            print(f"Warning: Failed to find executable for game '{title}'.")
            continue
        if len(exes) > 1:
            exes_list = "\n".join(str(e) for e in exes)
            print(
                f"Warning: Found multiple executables for game '{title}':\n{exes_list}"
            )
            continue

        exe = exes[0]
        # must be folder containing parent for some games (baba is you)
        working_dir = str(exe.parent)
        game_def = defs.GameDefinition(
            str(exe),
            title,
            game_root_dir.name,
            working_dir,
            "",
            defs.TAG_ITCH,
        )
        games.append(game_def)
    if not games:
        if any(f.is_file() for f in root.glob("itch*.exe")):
            print(
                "Use --itch-library to pass the itch app's Install Location (see itch app's Preferences), not the location of itch.exe"
            )
        elif root.is_dir():
            print(
                "The --itch-library argument only supports itch games installed by the itch app. https://itch.io/app"
            )

    print(f"Collected {len(games)} games from the itch library")
    return games


def test():
    import pprint, os

    games = itch_collect_games(os.path.expandvars("$APPDATA/itch/apps"))
    pprint.pprint([g.display_name for g in games])


if __name__ == "__main__":
    test()
