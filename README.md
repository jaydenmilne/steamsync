# steamsync
[![PyPI version](https://badge.fury.io/py/steamsync.svg)](https://badge.fury.io/py/steamsync) 

Simple command line tool to automatically add games from the Epic Games Launcher
to Steam.

Makes playing all of those free EGS games in Big Picture Mode a lot easier.

steamsync will scan all of the Epic Games Store games installed on your computer and 
add them to your Steam Library. If a shortcut with the same path already exists, you can
skip it. 
## Installation (brief)
Requires > Python 3.6 and Windows

```console
$ pip install steamsync
$ steamsync.py
```

## Installation and Usage (for beginners, command lines are scary!)

1. [Download Python 3.8](https://www.python.org/downloads/)
2. Choose the latest version of Python 3.8, and get the "Windows x86-64 executable installer" option
3. When installing Python, make sure to install pip and to *add Python to your PATH*
4. Open Commmand Prompt (search Start Menu for cmd.exe)
5. Type `pip install steamsync`, press enter. 
6. Make sure Steam is not running!
7. Type `steamsync.py`, press enter. The tool will walk you through everything else.
   Press ctrl+c if you get scared

## Usage
```
python steamsync.py -h
usage: steamsync.py [-h] [--egs-manifests EGS_MANIFESTS] [--steam-path STEAM_PATH] [--all] [--live-dangerously] [--steamid STEAMID]

Utility to import games from the Epic Games Store to your Steam library

optional arguments:
  -h, --help            show this help message and exit
  --egs-manifests EGS_MANIFESTS
                        Path to search for Epic Games Store manifest files (default: C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests)
  --steam-path STEAM_PATH
                        Path to Steam installation (default: C:\Program Files (x86)\Steam)
  --all                 Install all games found, do not prompt user to select which (default: False)
  --live-dangerously    Don't backup Steam's shortcuts.vdf file to shortcuts.vdf-{time}.bak (default: False)
  --steamid STEAMID     SteamID or username to install the shortcuts to, only needed if >1 accounts on this machine (default: )
  ```

### FAQ
#### Does this work on OSX?
First of all, wow Mac gamers exist. Second of all, it *should* work if you supply
`--egs-manifests` and `--steam-path`, maybe. Good luck

#### What about Linux?
If you get EGS working on Linux, you probably don't need this tool.

#### It doesn't work!
Open an issue on GitHub.

#### Steam crashed after opening my library the first time, but worked after that
Weird, I know. Mine did that too ¯\_(ツ)_/¯
