# LICENSE: AGPLv3. See LICENSE at root of repo

TAG_EPIC = "epicstore"
TAG_ITCH = "itchio"
TAG_XBOX = "xbox"
TAGS = [
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
        storetag,
    ):
        self.app_name = app_name
        self.executable_path = executable_path
        self.icon = executable_path
        self.display_name = display_name
        self.install_folder = install_folder
        self.launch_arguments = launch_arguments
        if storetag == TAG_EPIC:
            self.uri = (
                f"com.epicgames.launcher://apps/{app_name}?action=launch&silent=true"
            )
        else:
            self.uri = None
        self.storetag = storetag
