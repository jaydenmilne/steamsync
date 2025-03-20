# LICENSE: AGPLv3. See LICENSE at root of repo

import argparse
import os
import platform
import pprint
import time
from pathlib import Path

import appdirs
import vdf

import steamsync.defs as defs
import steamsync.steameditor as steameditor
from steamsync.launchers.egs import EpicGamesStoreLauncher
from steamsync.launchers.itch import ItchLauncher
from steamsync.launchers.launcher import Launcher
from steamsync.launchers.legendary import LegendaryLauncher
from steamsync.launchers.xbox import XboxLauncher


def get_default_steam_path():
    if platform.system() == "Linux":
        return os.path.expanduser("~") + "/.steam/steam"
    return "C:\\Program Files (x86)\\Steam"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Utility to import games from the Epic Games Store, Microsoft Store (Xbox for Windows), and itch.io to your Steam library",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--source",
        action="append",
        choices=defs.TAGS,
        help="Storefronts with games to add to Steam. If unspecified, uses all sources. Use argument multiple times to select multiple sources (--source itchio --source xbox).",
        required=False,
    )

    # TODO: make this path to egl root and not to manifests
    parser.add_argument(
        "--egs-manifests",
        default="C:\\ProgramData\\Epic\\EpicGamesLauncher\\Data\\Manifests",
        help="Path to search for Epic Games Store manifest files",
        required=False,
    )

    parser.add_argument(
        "--legendary-command",
        help="Command/Path to run 'legendary' executable",
        default="legendary",
        required=False,
    )

    parser.add_argument(
        "--itch-library",
        default=os.path.join(appdirs.user_config_dir("itch", roaming=True), "apps"),
        help="Path where the itch.io app installs games",
        required=False,
    )

    parser.add_argument(
        "--steam-path",
        default=get_default_steam_path(),
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
        "--replace-existing",
        default=False,
        help="Instead of skipping existing shortcuts (ones with the same path), overwrite them with new data. Useful to repair broken shortcuts.",
        required=False,
        action="store_true",
    )

    parser.add_argument(
        "--remove-missing",
        default=False,
        help="Remove shortcuts to games that no longer exist. Uses selected sources to determine if games without executables (uri or Xbox) still exist. i.e., if you don't include xbox source all xbox games will appear to be missing.",
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

    parser.add_argument(
        "--use-uri",
        default=False,
        action="store_true",
        help="Use a launcher URI (`com.epicgames.launcher://apps/fortnite?action=launch&silent=true`) instead of the path to the executable (eg `C:\\Fortnite\\Fortnite.exe`). Some games with online functionality (eg GTAV) require being launched through the EGS. Other games work better with Steam game streaming (eg Steam Link or Big Picture) using the path to the executable.",
        required=False,
    )

    parser.add_argument(
        "--download-art",
        default=False,
        action="store_true",
        help="Download Steam grid and Big Picture art from steam's servers for games we're adding. Only downloads art that we haven't already downloaded.",
        required=False,
    )

    parser.add_argument(
        "--download-art-all-shortcuts",
        default=False,
        action="store_true",
        help="Download Steam grid and Big Picture art for all non-steam game shortcuts. Only downloads art that we haven't already downloaded. Implies --download-art",
        required=False,
    )

    parser.add_argument(
        "--init-shortcuts-file",
        default=False,
        action="store_true",
        help="Initialize Steam shortcuts.vdf file if it doesn't exist. EXPERIMENTAL!!",
        required=False,
    )

    parser.add_argument(
        "--dump-shortcut-vdf",
        default=False,
        action="store_true",
        help="For debugging. Print the Steam shortcuts.vdf as text and exit.",
        required=False,
    )

    args = parser.parse_args()
    if not args.source:
        args.source = defs.TAGS
    if args.download_art_all_shortcuts:
        args.download_art = True
    return args


def print_games(games, use_uri):
    """
    games = list of GameDefinition
    """
    row_fmt = "{: >3} | {: <25} | {: <10} | {: <45} | {: <25}"
    print(row_fmt.format("Num", "Game Name", "Source", "App ID", "Executable"))
    print("=" * (3 + 25 + 10 + 45 + 25))
    for i, game in enumerate(games, start=1):
        exe, launch_args = game.get_launcher(use_uri)
        print(
            row_fmt.format(
                i,
                game.display_name[:25],
                game.storetag,
                game.app_name[:45],
                f"{exe} {launch_args}"[:256],
            )
        )


def filter_games(games):
    print(
        "Which games do you want to install (blank = all, comma separated list of numbers from table, q to quit)?"
    )
    selection = input(": ").strip()
    if selection == "":
        return games
    if selection[0] == "q":
        return False

    selection = selection.split(",")

    selected = list()
    for idx in selection:
        idx = idx.strip()
        try:
            selected.append(games[int(idx) - 1])
        except ValueError as e:
            # Assuming: invalid literal for int() with base 10
            print(f"Error: Expected number (1 for the first game) and not: '{idx}'")
            return None

    print(f"Selected {len(selected)} games to install")
    return selected


####################################################################################################
# Steam


def prompt_for_steam_account(accounts):
    """
    Has the user choose a steam account from the list. If there is only one, returns
    that one.

    Returns a steamid
    """
    if len(accounts) == 1:
        return accounts[0].steamid

    print("Found multiple Steam accounts:")
    row_fmt = "{: >3} | {: <17} | {: <25}"
    print(row_fmt.format("Num", "SteamID", "Display Name"))
    print("=" * ((7 + 3) + 25 + 3 + 17 + 3))
    for i, account in enumerate(accounts, start=1):
        print(row_fmt.format(i, account.steamid, account.username))

    print(
        f"Leave empty for `{accounts[0].username}`, or input a steamid, or the Num from the list"
    )
    choice = input(": ").strip()

    if choice == "":
        return accounts[0].steamid
    elif choice in [account.steamid for account in accounts]:
        return choice

    try:
        idx = int(choice)
        if idx <= len(accounts):
            return accounts[idx - 1].steamid
    except ValueError as e:
        # Assuming: invalid literal for int() with base 10
        print(f"Error: Expected number (1 for the first user) and not: '{choice}'")
    return None


def to_shortcut(game, use_uri):
    """
    Turns the given GameDefinition into a shortcut dict, suitable to injecting
    into Steam's shortcuts.vdf
    """

    shortcut, launch_args = game.get_launcher(use_uri)

    return {
        "appname": game.display_name,
        "appid": game.get_shortcut_id_signed(),
        "Exe": shortcut,
        "StartDir": game.install_folder,
        "icon": game.icon,
        "ShortcutPath": "",
        "LaunchOptions": launch_args,
        "IsHidden": 0,
        "AllowDesktopConfig": 1,
        "AllowOverlay": 1,
        "openvr": 0,
        "Devkit": 0,
        "DevkitGameID": "",
        "LastPlayTime": 0,  # todo - is this right? if we really wanted we could parse this in from EGS manifest files...
        "tags": {"0": "steamsync", "1": game.storetag},
    }


def get_exe_from_shortcut(shortcut):
    exe = shortcut.get("Exe")
    if not exe:
        exe = shortcut.get("exe")
    # May return None
    return exe


def add_games_to_shortcut_file(
    steamdb,
    user,
    games,
    shortcuts,
    use_uri,
    replace_existing,
    download_art_unsupported,
):
    """Add the given games to the shortcut file

    Args:
        steamdb (SteamDatabase): steam wrapper object
        user (SteamAccount): user to add shortcuts to
        games ([GameDefinition]): games to add
        shortcuts (dict): loaded shortcuts vdf file content to modify
        use_uri (bool): if we should use the EGS uri, or the path to the executable
        replace_existing (bool): if a shortcut already exists, clobber it with new data for that game
        download_art_unsupported (bool): download art for unsupported games

    Returns:
        (([string], integer), string): First element of tuple is a tuple of an array of "results" to display and the number of games added,
                                         The second is an error text if something went wrong
    """
    if use_uri:
        print()
        print("⚠ ⚠ NOTICE: ⚠ ⚠")
        print("Using a URI instead of executable path")
        print("You may experience issues with game streaming")
        print()
    else:
        print()
        print("⚠ ⚠ NOTICE: ⚠ ⚠")
        print("Using the path to the executable instead of the Epic Games Launcher URI")
        print("You may experience issues with online games (eg GTAV!)")
        print()

    # Make a lookup of the path of every shortcut installed to their index in
    # the shortcuts file. If a path is already in the shortcuts file, we won't
    # add another one (ie the path is what makes a shortcut unique) or if we
    # want to force updating, we can clobber the existing entry.
    path_to_index = {}

    art_downloads = 0
    if download_art_unsupported:
        print("Downloading art for existing shortcuts...")

    supported_games = {}
    for game in games:
        exe, _ = game.get_launcher(use_uri)
        supported_games[exe] = game

    for k, v in shortcuts["shortcuts"].items():
        exe = get_exe_from_shortcut(v)
        if not exe:
            print(
                "Warning: Entry in shortcuts.vdf has no `Exe` field! Is this a malformed entry?"
            )
            print(v)
            continue
        launch_args = v.get("LaunchOptions", "")
        # Include args to handle mulitple explorer.exe options for xbox.
        path = f"{exe}|{launch_args}"
        path_to_index[path] = k
        if download_art_unsupported and exe not in supported_games:
            appname = v.get("appname")
            # Create a temp definition to specify info required to download.
            game = defs.GameDefinition(
                exe,
                appname,
                appname,  # No alternative name.
                str(Path(exe).parent),
                "",
                None,
                "ignore tag",
                shortcut_id=v.get("appid"),  # may not exist yet
            )
            success = steamdb.download_art(user, game, should_replace_existing=False)
            if success:
                art_downloads += 1

    if download_art_unsupported:
        print(f"Downloaded new art for {art_downloads} games.")
        print()

    # the shortcuts "list" is actually a dict of "index": value
    # find the last one so we can add on to the end
    added = 0

    all_indexes = shortcuts["shortcuts"].keys()
    if len(all_indexes) == 0:
        last_index = 0
    else:
        last_index = max(int(idx) for idx in all_indexes)

    game_results = []
    for game in games:
        shortcut, launch_args = game.get_launcher(use_uri)
        path = f"{shortcut}|{launch_args}"
        i = path_to_index.get(path, None)
        if not i:
            # Detect old xbox exe shortcuts so we can migrate them.
            path = f"{game.executable_path}|"
            i = path_to_index.get(path, None)
        if i:
            old_shortcut = shortcuts["shortcuts"][i]
            # Preserve the appid stored in shortcuts so existing art still
            # matches. (Steam generates these ids if we don't assign them.)
            game.shortcut_id = old_shortcut.get("appid")
            if replace_existing:
                new_shortcut = to_shortcut(game, use_uri)
                print(
                    f"Replacing {old_shortcut['appname']} ({get_exe_from_shortcut(old_shortcut)} {old_shortcut.get('LaunchOptions', '')})\n     with {new_shortcut['appname']} ({get_exe_from_shortcut(new_shortcut)} {new_shortcut.get('LaunchOptions', '')})"
                )
                shortcuts["shortcuts"][i] = new_shortcut
                added += 1

            else:
                msg = f"{game.display_name}: Not creating shortcut since it already has one"
                print(msg)
                game_results.append(msg)
            continue
        last_index += 1
        shortcuts["shortcuts"][str(last_index)] = to_shortcut(game, use_uri)
        added += 1

    print(f"Added {added} new games")
    if added == 0:
        msg = "No need to update `shortcuts.vdf` - nothing new to add"
        print(msg)
        return None, msg

    return (game_results, added), None


def remove_missing_games_from_shortcut_file(
    steamdb,
    user,
    games,
    shortcuts,
):
    """Remove games without executables from the shortcut file

    Args:
        steamdb (SteamDatabase): steam wrapper object
        user (SteamAccount): user to add shortcuts to
        games ([GameDefinition]): all known games (for uri/xbox checking)
        shortcuts (dict): loaded shortcuts vdf file content to modify

    Returns:
        (([string], integer), string): First element of tuple is a tuple of an
        array of "results" to display and the number of games removed. The
        second is an error text if something went wrong.
    """

    print()

    game_results = []

    found_shortcuts = []
    missing_shortcuts = []
    for k, v in shortcuts["shortcuts"].items():
        exe = get_exe_from_shortcut(v)
        if not exe:
            print(
                "Warning: Entry in shortcuts.vdf has no `Exe` field! Is this a malformed entry?"
            )
            print(v)
            # Don't remove anything we don't understand.
            found_shortcuts.append(v)
            continue

        exists = False

        is_uri = "://" in exe or exe.lower().endswith("explorer.exe")
        if is_uri:
            args = v.get("LaunchOptions", "")
            exists |= any(g for g in games if g.uri == exe)  # epic uri
            exists |= any(g for g in games if g.uri == args)  # xbox uri
        else:
            exe_path = Path(exe)
            if not exe_path.is_file():
                # Manually added shortcuts may have additional quotes.
                exe_path = Path(exe.strip('"'))

            exists = exe_path.is_file()

        if exists:
            found_shortcuts.append(v)
        else:
            missing_shortcuts.append(v)
            appname = v.get("appname")
            msg = f"Removing '{appname}'. Missing exe: {exe}"
            print(msg)
            game_results.append(msg)

    shortcuts["shortcuts"] = {}
    for i, v in enumerate(found_shortcuts):
        shortcuts["shortcuts"][str(i)] = v

    print(f"Removed {len(missing_shortcuts)} missing games")
    if not missing_shortcuts:
        msg = "No need to update `shortcuts.vdf` - nothing missing"
        print(msg)
        return None, msg

    return (game_results, len(missing_shortcuts)), None


def collect_all_games(args):
    """Collect games from every enabled store"""
    launchers: dict[str, Launcher] = {
        defs.TAG_XBOX: XboxLauncher(),
        defs.TAG_LEGENDARY: LegendaryLauncher(legendary_command=args.legendary_command),
        defs.TAG_EPIC: EpicGamesStoreLauncher(egs_manifest_path=args.egs_manifests),
        defs.TAG_ITCH: ItchLauncher(library_path=args.itch_library),
    }

    # remove launchers they didn't ask for
    for l in list(launchers):
        if l not in args.source:
            del launchers[l]

    games: list[defs.GameDefinition] = []

    for l in launchers.values():
        if not l.is_installed():
            print(f"{l.get_display_name()} appears to not be installed")
            continue
        print(f"Collecting games from {l.get_display_name()}")

        try:
            games.extend(l.collect_games())
        except Exception as e:
            print(f"Unexpected failure collecting games from {l.get_display_name()}")
            print(e)

    return games


def get_steam_user(
    steamdb: steameditor.SteamDatabase, steam_path: str, provided_steamid: str
):
    try:
        accounts_on_machine = steamdb.enumerate_steam_accounts()
    except FileNotFoundError as e:
        print(
            f"Steam path not found: '{steam_path}'. Use --steam-path for non-standard installs.",
        )
        raise e

    if len(accounts_on_machine) == 1 and provided_steamid != "":
        print(
            "FYI: There is only one Steam account found on your computer, so you don't need to provide --steamid"
        )

    numeric_steamid = None
    if provided_steamid.isdigit():
        # they gave us a numeric steam ID. Validate that is on the machine
        numeric_steamid = next(
            (
                user.steamid
                for user in accounts_on_machine
                if user.steamid == provided_steamid
            ),
            None,
        )

        if numeric_steamid is None:
            print(
                f"The numeric --steamid you provided ({provided_steamid}) was not found on your computer. Pick from below"
            )
    elif provided_steamid != "":
        # gave us a username
        numeric_steamid = next(
            (
                user.steamid
                for user in accounts_on_machine
                if user.username == provided_steamid
            ),
            None,
        )

        if numeric_steamid is None:
            print(
                f"The username (--steamid) you provided ({provided_steamid}) was not found on your computer. Pick from below"
            )

    if numeric_steamid is None:
        while not numeric_steamid:
            numeric_steamid = prompt_for_steam_account(accounts_on_machine)

    user = next(user for user in accounts_on_machine if user.steamid == numeric_steamid)
    return user


####################################################################################################
# Main


def _load_shortcuts(shortcut_file_path, can_init_on_missing):
    """Load the user's shortcuts.vdf file.

    _load_shortcuts(str, bool) -> dict, str
    """
    if not os.path.exists(shortcut_file_path) and not can_init_on_missing:
        message = f"Could not find shortcuts file at `{shortcut_file_path}`\nEither make a shortcut in Steam (Library ➡ ➕ Add Game ➡ Add a Non-Steam Game...) first.\nOr enable option to initialize shortcuts  file. (--init-shortcuts-file)\nAborting."
        print(message)
        return
    elif can_init_on_missing:
        shortcuts = {"shortcuts": {}}
    else:
        # read in the shortcuts file
        with open(shortcut_file_path, "rb") as sf:
            shortcuts = vdf.binary_load(sf)

    return shortcuts


def main():
    args = parse_arguments()

    steamdb = steameditor.SteamDatabase(
        args.steam_path,
        appdirs.user_cache_dir("steamsync"),
        args.use_uri,
    )

    if args.dump_shortcut_vdf:
        # Do this early to avoid showing game list.
        user = get_steam_user(steamdb, args.steam_path, args.steamid)
        shortcut_file_path = user.get_shortcut_filepath(steamdb._steam_path)
        shortcuts = _load_shortcuts(shortcut_file_path, args.init_shortcuts_file)
        print("Contents of", shortcut_file_path)
        pprint.pprint(shortcuts)
        return 0

    # 1. Collect all games from every enabled store
    all_games = collect_all_games(args)

    # 2. Print out the list of games we got
    print_games(all_games, args.use_uri)

    # 3. Have the user select the games they want
    games = all_games

    if not args.all:
        picks = None
        while not picks:
            picks = filter_games(games)
            if picks is False:
                print("Quitting...")
                return 0

        games = picks

    # 4. Pick the account to add shortcuts to (if needed)
    user = get_steam_user(steamdb, args.steam_path, args.steamid)

    # 5. Write shortcuts to steam!

    print(f"Installing shortcuts for SteamID {user.username} `{user.steamid}`")

    shortcut_file_path = user.get_shortcut_filepath(steamdb._steam_path)
    shortcuts = _load_shortcuts(shortcut_file_path, args.init_shortcuts_file)
    if not shortcuts:
        return 1

    should_write_vdf = False
    if args.remove_missing:
        result, msg = remove_missing_games_from_shortcut_file(
            steamdb,
            user,
            all_games,
            shortcuts,
        )
        should_write_vdf |= result is not None

    result, msg = add_games_to_shortcut_file(
        steamdb,
        user,
        games,
        shortcuts,
        args.use_uri,
        args.replace_existing,
        args.download_art_all_shortcuts,
    )
    should_write_vdf |= result is not None

    # Steam stores shortcut ids in shortcuts.vdf, so we can't download art
    # until after merging new games into shortcuts.
    if args.download_art:
        if args.download_art_all_shortcuts:
            get_art_for_games = all_games
            print("\nDownloading art for all detected games...")
        else:
            get_art_for_games = games
            print("\nDownloading art for selected games...")

        if args.replace_existing:
            # We don't have an argument for replacing art and replacing
            # shortcuts is pretty different, so explain the better path.
            print(
                f"To replace existing art, delete the images in {user.get_grid_folder(steamdb._steam_path)}"
            )
        count = steamdb.download_art_multiple(
            user, get_art_for_games, should_replace_existing=False
        )
        print(f"Downloaded new art for {count} games.")
        print()

    if should_write_vdf:
        print()
        if args.live_dangerously:
            print("Not backing up `shortcuts.vdf` since you enjoy danger")
            os.remove(shortcut_file_path)
        elif os.path.exists(shortcut_file_path):
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            new_filename = shortcut_file_path + f"-{timestamp}.bak"

            print(f"Backing up `shortcuts.vdf` to `{new_filename}`")
            os.rename(shortcut_file_path, new_filename)

        new_bytes = vdf.binary_dumps(shortcuts)
        with open(shortcut_file_path, "wb") as shortcut_file:
            shortcut_file.write(new_bytes)

        print("Wrote `shortcuts.vdf` successfully!")
        print()
        print("➡   Restart Steam!")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    main()
