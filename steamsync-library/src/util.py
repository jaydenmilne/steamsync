#! /usr/bin/env python
# LICENSE: AGPLv3. See LICENSE at root of repo

import os


def is_executable_game(game_path):
    """Is the input path a real file that we have access to?

    is_executable_game(Path) -> bool
    """
    try:
        return game_path.is_file() and os.access(game_path, os.R_OK)
    except OSError:
        return False
