#! /usr/bin/env python

# LICENSE: AGPLv3. See LICENSE at root of repo

from datetime import datetime
from pathlib import Path
import binascii
import json
import os
import shutil

import requests
import vdf

k_applist_fname = "applist.json"


class SteamAccount:
    """
    Data class to associate steamid and username
    """

    def __init__(self, steamid, username):
        self.steamid = steamid
        self.username = username

    def get_grid_folder(self, steam_folder):
        return f"{steam_folder}/userdata/{self.steamid}/config/grid"

    def get_user_folder(self, steam_folder):
        return f"{steam_folder}/userdata/{self.steamid}"


class SteamDatabase:

    """Database of steam information."""

    def __init__(self, steam_path, cache_folder):
        """
        :steam_path: Path to folder containing steam.exe.
        :cache_folder: Where to store downloaded files.
        """
        self._steam_path = Path(steam_path)
        self._cache_folder = Path(cache_folder)
        self._apps = self._load_app_list()

    def enumerate_steam_accounts(self):
        """
        Returns a list of SteamAccounts that have signed into steam on this machine

        enumerate_steam_accounts() -> list(SteamAccount)
        """
        accounts = list()
        with os.scandir(self._steam_path / "userdata") as childs:
            for child in childs:
                if not child.is_dir():
                    continue

                steamid = os.fsdecode(child.name)

                # we need to look inside this user's localconfig.vdf to figure out their
                # display name

                localconfig_file = os.path.join(child.path, "config/localconfig.vdf")
                if not os.path.exists(localconfig_file):
                    continue

                # here we just replace any malformed characters since we are only doing this to get the
                # display name
                with open(
                    localconfig_file, "r", encoding="utf-8", errors="replace"
                ) as localconfig:
                    cfg = vdf.load(localconfig)
                    username = cfg["UserLocalConfigStore"]["friends"]["PersonaName"]
                    accounts.append(SteamAccount(steamid, username))

        return accounts

    def _load_app_list(self):
        """Load or download the app list.

        _load_app_list() -> dict
        """
        data = None
        now = datetime.utcnow()
        current_version = 1

        applist_file = self._cache_folder / k_applist_fname
        if applist_file.is_file():
            with applist_file.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if data["version"] != current_version:
                data = None
            else:
                write_date = datetime.fromisoformat(data["download_timestamp"])
                delta = now - write_date
                if delta.days > 7:
                    # Stale applist. Trigger re-download.
                    data = None

        if not data:
            print("Downloading latest app list from Steam...")
            response = requests.get(
                "http://api.steampowered.com/ISteamApps/GetAppList/v2"
            )
            apps = response.json()["applist"]["apps"]
            name_to_id = {g["name"]: g["appid"] for g in apps}
            data = {
                "version": current_version,
                "download_timestamp": now.isoformat(),
                "name_to_id": name_to_id,
            }
            applist_file.parent.mkdir(parents=True, exist_ok=True)
            with applist_file.open("w", encoding="utf-8") as file:
                file.write(json.dumps(data, indent=2))

        return data

    def guess_appid(self, name):
        name_to_id = self._apps["name_to_id"]
        appid = name_to_id.get(name)
        # Don't bother trying to be smart. Might return None.
        return appid

    def download_art_multiple(self, user, games, should_replace_existing):
        """Download art for a list of GameDefinitions

        download_art_multiple(SteamAccount, list[GameDefinition], bool) -> None
        """
        count = 0
        for game in games:
            success = self.download_art(user, game, should_replace_existing)
            if success:
                count += 1
        return count

    def _try_copy_art_to(self, art_fname, dest):
        """Duplicate downloaded art.
        Sometimes the best art is the same as some other art.

        _try_copy_art_to(Path, Path) -> None
        """
        dest = dest.with_suffix(art_fname.suffix)
        if not dest.is_file():
            shutil.copy(art_fname, dest)

    def download_art(self, user, game, should_replace_existing):
        targets = self._get_grid_art_destinations(game, user)
        targets["boxart"].parent.mkdir(exist_ok=True, parents=True)
        appid = self.guess_appid(game.display_name)
        downloaded_art = False
        found_art = 0
        expected_art = len(targets)
        logs = []
        if appid:
            urls = self._get_art_urls(appid)

            for k, url in urls.items():
                did_download, fname, msg = self._try_download_image(
                    url, targets[k], should_replace_existing
                )
                downloaded_art |= did_download
                if fname:
                    found_art += 1
                else:
                    logs.append(msg)

        if found_art < expected_art:
            print(f"Found {found_art}/{expected_art} art for '{game.display_name}'")
            print(" ", "\n  ".join(logs))
        return downloaded_art

    def _get_art_urls(self, appid):
        """Get the hero, boxart, and logo art urls for the input appid.

        _get_art_urls(int) -> dict[str,str]
        """
        return {
            "boxart": f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/library_600x900_2x.jpg",
            "hero": f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/library_hero.jpg",
            "logo": f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/logo.png",
            "10foot": f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg",
        }

    def _try_download_image(self, url, dest_fname, should_replace_existing):
        url_path = Path(url)
        fname = dest_fname.with_suffix(url_path.suffix)
        if not fname.is_file() or should_replace_existing:
            return self._download_image(url, fname)
        return False, fname, "Already exists"

    def _download_image(self, url, dest_fname):
        """Download an image to dest_fname.

        Returns:
        * did we download something
        * the image file on disk (if downloaded or already existed)
        * status message

        _download_image(str, Path) -> (bool,str,str)
        """
        page = requests.get(url)
        if page.status_code == 200:
            with dest_fname.open("wb") as f:
                f.write(page.content)
            return True, dest_fname, f"Downloaded '{url}' to '{dest_fname}'."
        return False, None, f"Error {page.status_code} for '{url}'."

    def _get_steam_shortcut_id(self, exe, appname):
        """Get short id for non-steam shortcut.

        _get_steam_shortcut_id(str, str) -> int
        """
        # Using the same method as steamgrid
        # https://github.com/boppreh/steamgrid/blob/c796e612c67925413317f4012bdc771326f173c8/games.go#L100-L137
        unique_id = "".join([exe, appname])
        id_int = binascii.crc32(str.encode(unique_id)) | 0x80000000
        return id_int

    def _get_grid_art_destinations(self, game, user):
        """Get filepaths for the grid images for the input shortcut.

        _get_grid_art_destinations(GameDefinition, SteamAccount) -> dict[str,Path]
        """
        grid = Path(user.get_grid_folder(self._steam_path))
        shortcut = self._get_steam_shortcut_id(game.executable_path, game.display_name)
        # For some reason Big Picture uses 64 bit ids.
        # See https://github.com/scottrice/Ice/blob/7130b54c8d2fa7d0e2c0994ca1f2aa3fb2a27ba9/ice/steam_grid.py#L49-L64
        bp_shortcut = (shortcut << 32) | 0x02000000
        return {
            "boxart": grid / f"{shortcut}p.jpg",
            "hero": grid / f"{shortcut}_hero.jpg",
            "logo": grid / f"{shortcut}_logo.png",
            "10foot": grid / f"{bp_shortcut}.png",
        }


def _test():
    import pprint

    db = SteamDatabase(
        "C:/Program Files (x86)/Steam", os.path.expandvars("$TEMP/steamsync")
    )
    user = db.enumerate_steam_accounts()[0]
    pprint.pp([user.steamid, user.username])
    game_name = "Overland"
    appid = db.guess_appid(game_name)
    print(game_name, appid)


if __name__ == "__main__":
    _test()
