import subprocess
import json
import os

import defs


def legendary_collect_games(executable_cmd):
    """
    Returns an array of GameDefinitions of all the installed EGS games that 'legendary' knows about
    """
    games_dict = {}
    # populate info for all installable games
    games_raw_json = subprocess.Popen([executable_cmd, "list-games", "--json"], stdout=subprocess.PIPE).communicate()[0].decode()
    games_json = json.loads(games_raw_json)
    for entry in games_json:
        # TODO: Map other useful information, like tags?
        games_dict[entry['app_name']] = {
            'art': entry['metadata']['keyImages'][0]
        }
    games = list()
    raw_json = subprocess.Popen([executable_cmd, "list-installed", "--json"], stdout=subprocess.PIPE).communicate()[0].decode()
    parsed_json = json.loads(raw_json)
    for entry in parsed_json:
        app_name = entry['app_name']
        launch_args = ' launch ' + app_name
        display_name = entry['title']
        install_location = entry['install_path']
        art_url = None
        icon = os.path.join(install_location, entry['executable'])
        if app_name in games_dict:
             art_url = games_dict[app_name]['art']

        games.append(
            defs.GameDefinition(
                executable_cmd,
                display_name,
                app_name,
                install_location,
                launch_args,
                art_url,
                defs.TAG_LEGENDARY,
                icon
            )
        )
    return games