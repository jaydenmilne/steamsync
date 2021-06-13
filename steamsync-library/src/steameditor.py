#! /usr/bin/env python

# LICENSE: AGPLv3. See LICENSE at root of repo
from pathlib import Path
import os

import vdf


class SteamAccount:
    """
    Data class to associate steamid and username
    """

    def __init__(self, steamid, username):
        self.steamid = steamid
        self.username = username


class SteamDatabase:

    """Database of steam information."""

    def __init__(self, steam_path, cache_folder):
        """
        :steam_path: Path to folder containing steam.exe.
        """
        self._steam_path = Path(steam_path)

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
