# LICENSE: AGPLv3. See LICENSE at root of repo

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
        icon = None
    ):
        self.app_name = app_name
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
