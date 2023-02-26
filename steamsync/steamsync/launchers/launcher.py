import abc

from steamsync.defs import GameDefinition


class Launcher(abc.ABC):
    """Base class for all of the launchers we support

    To add a launcher, create a subclass and hook it up as needed in steamsync.py.

    Note that your __init__ methods should specify defaults for all arguments
    """

    @abc.abstractmethod
    def collect_games(self) -> list[GameDefinition]:
        """Collect and return all of the games for this launcher"""
        return []

    @abc.abstractmethod
    def get_store_id(self) -> str:
        """Return the unique store ID for this launcher"""
        return ""

    @abc.abstractmethod
    def get_display_name(self) -> str:
        """Return the pretty display name for this launcher"""
        return ""

    @abc.abstractmethod
    def is_installed(self) -> bool:
        """Return if this store appears to be installed or not"""
        return False
