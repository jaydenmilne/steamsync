#! /usr/bin/env python

# LICENSE: AGPLv3. See LICENSE at root of repo

import gzip
import json
from pathlib import Path

import steamsync.defs as defs
import steamsync.launchers.launcher as launcher
import steamsync.util as util
import toml


class ItchLauncher(launcher.Launcher):
    """Support for the Itch launcher.

    See https://itch.io/app
    """

    def __init__(self, library_path: str):
        self.library_path = library_path

    def collect_games(self) -> list[defs.GameDefinition]:
        print(f"\nScanning itch library folder ({self.library_path})...")
        root = Path(self.library_path)
        games = []
        for receipt in root.glob("*/.itch/receipt.json.gz"):
            r = _load_receipt(receipt)
            g = r["game"]
            title = g["title"]
            if g["classification"] != "game":
                # print(f"Skipping nongame '{title}' -- '{g['classification']}'.")
                continue

            game_root_dir = receipt.parent.parent
            exe, args, label = _get_exe_from_manifest(game_root_dir / ".itch.toml")
            if not exe:
                label = ""
                args = ""
                exes = [
                    exe for exe in game_root_dir.glob("*.exe") if _might_be_exe(exe)
                ]
                if not exes:
                    # Look one level deeper.
                    exes = [
                        exe
                        for exe in game_root_dir.glob("*/*.exe")
                        if _might_be_exe(exe)
                    ]
                if not exes:
                    print(f"Warning: Failed to find executable for game '{title}'.")
                    continue
                if len(exes) > 1:
                    exes_list = "\n".join(str(e) for e in exes)
                    print(
                        f"Warning: Skipping game '{title}' with multiple executables:\n{exes_list}"
                    )
                    continue

                exe = exes[0]

            # must be folder containing parent for some games (baba is you)
            working_dir = str(exe.parent)
            game_def = defs.GameDefinition(
                str(exe),
                title,
                f"{game_root_dir.name}{label}",
                working_dir,
                args,
                g.get("coverUrl"),
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
        games.sort()
        return games

    def get_store_id(self) -> str:
        return defs.TAG_ITCH

    def get_display_name(self) -> str:
        return "itch.io"

    def is_installed(self) -> bool:
        return True  # TODO


def _load_receipt(path_to_receipt: str) -> dict:
    """Load itch's receipt.json.gz.

    _load_receipt(str) -> dict
    """
    with gzip.open(path_to_receipt, "r") as f:
        json_bytes = f.read()

    json_str = json_bytes.decode("utf-8")
    return json.loads(json_str)


def _get_exe_from_manifest(manifest_path):
    """If the manifest exists and contains an action, return that exe.

    _get_exe_from_manifest(Path) -> Path
    """
    if manifest_path.is_file():
        manifest = toml.load(manifest_path)
        platform = "windows"
        available_actions = [
            a for a in manifest["actions"] if a.get("platform", platform) == platform
        ]

        for a in available_actions:
            exe_name = a["path"]
            # {{EXT}} is not documented, but used by itch's sample-evil-app demo.
            exe_name = exe_name.replace(r"{{EXT}}", ".exe")
            a["path"] = manifest_path.parent / exe_name

        available_actions = [
            a for a in available_actions if util.is_executable_game(a["path"])
        ]

        try:
            # 'play' is a "well-known" name: https://itch.io/docs/itch/integrating/manifest-actions.html
            action = next(a for a in available_actions if a["name"] == "play")
        except StopIteration:
            # Fallback to the first action which hopefully would be the game.
            action = available_actions[0]
        args = action.get("args", [])
        args = " ".join(args)
        return action["path"], args, f" ({action['name']})"

    return None, None, None


def _might_be_exe(exe):
    """Return true if the input might be the exe for a game.

    _might_be_exe(Path) -> bool
    """
    if not util.is_executable_game(exe):
        return False
    exe_name = str(exe.name).lower()
    meta_executables = [
        # be sure to lowercase!
        "dxwebsetup",
        "framework",
        "install",
        "notification_helper",
        "unitycrashhandler",
    ]
    is_meta = any(meta for meta in meta_executables if meta in exe_name)
    return not is_meta
