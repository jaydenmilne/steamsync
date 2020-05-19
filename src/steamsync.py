import argparse
import json
import os
from pathlib import Path
import time
import math

import vdf


class GameDefinition:
    """
    Data class to hold a game definition. Should be everything that the steamsync UI and that
    Steam itself needs to make a shortcut
    """

    def __init__(self, executable_path, display_name, app_name, install_folder, launch_arguments):
        self.app_name = app_name
        self.executable_path = executable_path
        self.display_name = display_name
        self.install_folder = install_folder
        self.launch_arguments = launch_arguments


class SteamAccount:
    """
    Data class to associate steamid and username
    """

    def __init__(self, steamid, username):
        self.steamid = steamid
        self.username = username


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Utility to import games from the Epic Games Store to your Steam library",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # TODO: make this path to egl root and not to manifests
    parser.add_argument(
        "--egs-manifests",
        default="C:\\ProgramData\\Epic\\EpicGamesLauncher\\Data\\Manifests",
        help="Path to search for Epic Games Store manifest files",
        required=False,
    )

    parser.add_argument(
        "--steam-path",
        default="C:\\Program Files (x86)\\Steam",
        help="Path to Steam installation",
        required=False,
    )

    parser.add_argument(
        "--all",
        default=False,
        help="Install all games found, do not prompt user to select which",
        required=False,
        action="store_true",
    )

    parser.add_argument(
        "--live-dangerously",
        default=False,
        help="Don't backup Steam's shortcuts.vdf file to shortcuts.vdf-{time}.bak",
        required=False,
        action="store_true",
    )

    parser.add_argument(
        "--steamid",
        default="",
        help="SteamID or username to install the shortcuts to, only needed if >1 accounts on this machine",
        required=False,
    )

    return parser.parse_args()


def egs_collect_games(egs_manifest_path):
    """
    Returns an array of GameDefinitions of all the installed EGS games
    """
    print(f"Scanning EGS manifest store ({egs_manifest_path})...")
    # loop over every .item fiile
    pathlist = Path(egs_manifest_path).glob("*.item")
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
                print(f"\tSkipping '{display_name}' since installation is incomplete")
                continue
            elif not item["bIsApplication"]:
                print(f"\tSkipping '{display_name}' since it isn't an application")
                continue
            elif "games" not in item["AppCategories"]:
                print(f"\tSkipping '{display_name}' since it doesn't have the category 'games'")
                continue

            if "InstallLocation" not in item:
                print(f"\tSkipping '{display_name}' since it apparently doesn't have an 'InstallLocation'")
                continue

            install_location = os.path.normpath(item["InstallLocation"])

            if "LaunchExecutable" not in item:
                print(f"\tSkipping '{display_name}' since it apparently doesn't have an executable")
                continue

            if "LaunchCommand" not in item:
                print(f"'{display_name}' doesn't have LaunchCommands?")
                launch_arguments = ""
            else:
                # I think this is for command line arguments...?
                launch_arguments = item["LaunchCommand"]

            launch_executable = os.path.normpath(item["LaunchExecutable"])

            # This causes trouble for some games
            # (D:\Epic Games\RiME + /RiME/SirenGame/Binaries/Win64/RiME.exe = D:/RiME/SirenGame/Binaries/Win64/RiME.exe ???)
            # complete_path = os.path.join(install_location, launch_executable)

            complete_path = (
                os.path.normpath(install_location) + os.path.sep + os.path.normpath(launch_executable)
            )

            if not os.path.exists(complete_path):
                print(install_location, launch_executable)
                print(f"\tWarning: path `{complete_path}` does not exist for game {display_name}, excluding!")
                continue
            games.append(
                GameDefinition(complete_path, display_name, app_name, install_location, launch_arguments,)
            )

    print(f"Collected {len(games)} games from the EGS manifest store")
    return games


def print_games(games):
    """
    games = list of GameDefinition
    """
    row_fmt = "{: >3} | {: <25} | {: <32} | {: <25}"
    print(row_fmt.format("Num", "Game Name", "App ID", "Install Path"))
    print("=" * ((25 + 3) * 2 + 50 + 6))
    for i, game in enumerate(games, start=1):
        print(row_fmt.format(i, game.display_name[:25], game.app_name, game.executable_path))


def filter_games(games):
    print("Which games do you want to install (blank = all, or comma seperated list of numbers from table)?")
    selection = input(": ").strip()
    if selection == "":
        return games

    selection = selection.split(",")

    selected = list()
    for idx in selection:
        idx = idx.strip()
        selected.append(games[int(idx) - 1])

    print(f"Selected {len(selected)} games to install")
    return selected


####################################################################################################
# Steam


def enumerate_steam_accounts(steam_path):
    """
    Returns a list of SteamAccounts that have signed into steam on this machine
    """
    accounts = list()
    with os.scandir(os.path.join(steam_path, "userdata")) as childs:
        for child in childs:
            if not child.is_dir():
                continue
            steamid = os.fsdecode(child.name)

            # we need to look inside this user's localconfig.vdf to figure out their
            # display name

            # here we just replace any malformed characters since we are only doing this to get the
            # display name
            with open(
                os.path.join(child.path, "config/localconfig.vdf"), "r", encoding="utf-8", errors="replace"
            ) as localconfig:
                cfg = vdf.load(localconfig)
                username = cfg["UserLocalConfigStore"]["friends"]["PersonaName"]
                accounts.append(SteamAccount(steamid, username))

    return accounts


def prompt_for_steam_account(accounts):
    """
    Has the user choose a steam account from the list. If there is only one, returns
    that one.

    Returns a steamid
    """
    if len(accounts) == 1:
        return accounts[0][0]

    print("Found multiple Steam accounts:")
    row_fmt = "{: >3} | {: <17} | {: <25}"
    print(row_fmt.format("Num", "SteamID", "Display Name"))
    print("=" * ((7 + 3) + 25 + 3 + 17 + 3))
    for i, account in enumerate(accounts, start=1):
        print(row_fmt.format(i, account.steamid, account.username))

    print(f"Leave empty for `{accounts[0].username}`, or input a steamid, or the Num from the list")
    choice = input(": ").strip()

    if choice == "":
        return accounts[0].steamid
    elif choice in [account.steamid for account in accounts]:
        return choice
    elif int(choice) <= len(accounts):
        return accounts[int(choice) - 1].steamid
    else:
        print("You done messed up AARON")
        exit(-1)


def to_shortcut(game):
    """
    Turns the given GameDefinition into a shortcut dict, suitable to injecting
    into Steam's shortcuts.vdf
    """
    return {
        "appname": game.display_name,
        "Exe": game.executable_path,
        "StartDir": game.install_folder,
        "icon": "",
        "ShortcutPath": "",
        "LaunchOptions": game.launch_arguments,
        "IsHidden": 0,
        "AllowDesktopConfig": 1,
        "AllowOverlay": 1,
        "openvr": 0,
        "Devkit": 0,
        "DevkitGameID": "",
        "LastPlayTime": 0,  # todo - is this right? if we really wanted we could parse this in from EGS manifest files...
        "tags": {"0": "steamsync", "1": "epicgamesstore"},
    }


def add_games_to_shortcut_file(steam_path, steamid, games, skip_backup):
    shortcut_file_path = os.path.join(steam_path, "userdata", steamid, "config", "shortcuts.vdf")

    if not os.path.exists(shortcut_file_path):
        print(f"Could not find shortcuts file at `{shortcut_file_path}`")
        exit(-2)

    # read in the shortcuts file
    with open(shortcut_file_path, "rb") as sf:
        shortcuts = vdf.binary_load(sf)

    # Make a set that contains the path of every shortcut installed. If a path is already in the
    # shortuts file, we won't add another one (ie the path is what makes a shortcut unique)
    all_paths = set()

    for k, v in shortcuts["shortcuts"].items():
        all_paths.add(v["Exe"])

    # the shortcuts "list" is actually a dict of "index": value
    # find the last one so we can add on to the end
    added = 0
    last_index = int(max(shortcuts["shortcuts"].keys()))
    for game in games:
        if game.executable_path in all_paths:
            print(f"Not creating shortcut for `{game.display_name}` since it already has one")
            continue
        last_index += 1
        shortcuts["shortcuts"][str(last_index)] = to_shortcut(game)
        added += 1

    print(f"Added {added} new games")
    if added == 0:
        print(f"No need to update `shortcuts.vdf`")
        return

    if skip_backup:
        print("Not backing up `shortcuts.vdf` since you enjoy danger")
        os.remove(shortcut_file_path)
    else:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        new_filename = shortcut_file_path + f"-{timestamp}.bak"

        print(f"Backing up `shortcuts.vdf` to `{new_filename}`")
        os.rename(shortcut_file_path, new_filename)

    new_bytes = vdf.binary_dumps(shortcuts)
    with open(shortcut_file_path, "wb") as shortcut_file:
        shortcut_file.write(new_bytes)

    print("Updated `shortcuts.vdf` successfully!")


####################################################################################################
# Main

if __name__ == "__main__":
    args = parse_arguments()
    games = egs_collect_games(args.egs_manifests)
    print_games(games)

    if not args.all:
        games = filter_games(games)

    # add more GameDefinitions to games as needed...

    # Write shortcuts to steam!
    steamid = args.steamid
    accounts = enumerate_steam_accounts(args.steam_path)

    # if they gave a username, find the steamid associated with it
    if not steamid.isdigit() and steamid != "":
        username = steamid
        for account in accounts:
            if username == account.username:
                steamid = account.steamid
        if username == steamid:
            # bit hackish, triggers selection below if the username wasn't found
            print(f"!!! SteamID for `{steamid}` not found.")
            steamid = ""

    if steamid == "":
        steamid = prompt_for_steam_account(accounts)

    print(f"Installing shortcuts for SteamID `{steamid}`")
    add_games_to_shortcut_file(args.steam_path, steamid, games, args.live_dangerously)
