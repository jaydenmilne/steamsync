# LICENSE: AGPLv3. See LICENSE at root of repo

import binascii
import ctypes
import os
from pathlib import Path

TAG_LEGENDARY = "legendary"
TAG_EPIC = "epicstore"
TAG_ITCH = "itchio"
TAG_XBOX = "xbox"
TAGS = [
    TAG_LEGENDARY,
    TAG_EPIC,
    TAG_ITCH,
    TAG_XBOX,
]


def _get_steam_shortcut_id(exe, appname):
    """Generate a short id for non-steam shortcut.

    _get_steam_shortcut_id(str, str) -> int
    """
    # This is the old method that steamgrid used, but now steam stores the id
    # in shortcuts.vdf. Keep this around to populate new shortcuts.
    # https://github.com/boppreh/steamgrid/blob/c796e612c67925413317f4012bdc771326f173c8/games.go#L100-L137
    unique_id = "".join([exe, appname])
    id_int = binascii.crc32(str.encode(unique_id)) | 0x80000000
    signed = ctypes.c_int(id_int)
    return signed.value


class GameDefinition:
    """
    Data class to hold a game definition. Should be everything that the steamsync UI and that
    Steam itself needs to make a shortcut
    """

    def __init__(
        self,
        executable_path,
        display_name,
        app_name,
        install_folder,
        launch_arguments,
        art_url,
        storetag,
        shortcut_id=None,
        icon=None,
    ):
        self.app_name = app_name
        self.shortcut_id = shortcut_id
        self.executable_path = executable_path
        self.icon = icon or executable_path
        self.display_name = display_name
        self.install_folder = install_folder
        self.launch_arguments = launch_arguments
        if storetag == TAG_EPIC:
            self.uri = (
                f"com.epicgames.launcher://apps/{app_name}?action=launch&silent=true"
            )
        elif storetag == TAG_XBOX:
            self.uri = f"shell:appsFolder\\{app_name}"
        else:
            self.uri = None
        self.art_url = art_url
        self.storetag = storetag

    def __lt__(self, other):
        # Sort by display_name
        return self.display_name < other.display_name

    def get_launcher(self, use_uri):
        exe = self.executable_path
        args = self.launch_arguments
        if self.storetag == TAG_XBOX:
            # Xbox games put their version number in their path, so we can't rely
            # on running the exe directly. We need to use explorer to launch by id.
            # Unlike Epic, we can't use this uri directly -- steam will
            # successfully launch the game but also give a "Failed to launch"
            # error.
            exe_path = Path(os.path.expandvars("$WinDir")) / "explorer.exe"
            exe = exe_path.as_posix()
            args = self.uri
        elif use_uri and self.uri:
            exe = self.uri
        return exe, args

    def get_shortcut_id_signed(self):
        """Get the "appid" for the shortcut as a signed int.

        If it doesn't already exist, we'll generate it with the old algorithm
        so we can inject it into shortcuts.vdf and be able to assign art on
        creation.

        get_shortcut_id_signed() -> str
        """
        if self.shortcut_id:
            return self.shortcut_id
        else:
            # Generate at the last second so we can always tell whether it came
            # from shortcuts.vdf.
            return _get_steam_shortcut_id(self.executable_path, self.app_name)

    def get_shortcut_id_unsigned(self):
        """Get the "appid" for the shortcut as an unsigned int.

        get_shortcut_id_unsigned() -> str
        """
        unsigned = ctypes.c_uint(self.get_shortcut_id_signed())
        return unsigned.value
