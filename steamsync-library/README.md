# steamsync cli
[![PyPI version](https://badge.fury.io/py/steamsync.svg)](https://badge.fury.io/py/steamsync) 

Simple command line tool (and poorly documented library!) to automatically add 
games from the Epic Games Launcher to Steam.

Makes playing all of those free EGS games in Big Picture Mode a lot easier. In my experience,
when launching from Big Picture Mode, Steam Input works as expected (even in Fortnite!).

steamsync will scan all of the Epic Games Store games installed on your computer and 
add them to your Steam Library. If a shortcut with the same path already exists, it will
skip it, so it's safe to import all of your games over and over.

steamsync attempts to be simple. It does not attempt to fetch any banner art, it
 simply uses the executable's icon as the icon in steam. 
 
## Installation (brief)
Requires > Python 3.6 and Windows

```console
$ pip install steamsync
$ steamsync.py
```
If you have issues with running `steamsync.py`, try running `python -m steamsync`

## Installation and Usage (for beginners)

1. [Download Python 3.8](https://www.python.org/downloads/)
2. Choose the latest version of Python 3.8, and get the "Windows x86-64 executable installer" option
3. When installing Python, make sure to install pip and to *add Python to your PATH*
4. Open Commmand Prompt (search Start Menu for cmd.exe)
5. Type `pip install steamsync`, press enter. 
6. Make sure Steam is not running!
7. Type `steamsync.py`, press enter. The tool will walk you through everything else.
   Press ctrl+c if you get scared and want to abort.

## Usage
```
$ steamsync.py -h
usage: steamsync.py [-h] [--egs-manifests EGS_MANIFESTS] [--steam-path STEAM_PATH] [--all] [--live-dangerously] [--steamid STEAMID] [--use-uri]

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
  --use-uri             Use a launcher URI (`com.epicgames.launcher://apps/fortnite?action=launch&silent=true`) instead of the path to the executable 
                        (eg `C:\Fortnite\Fortnite.exe`). Some games with online functionality (eg GTAV) require being launched through the EGS. Other 
                        games work better with Steam game streaming (eg Steam Link or Big Picture) using the path to the executable. (default: False)
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
Weird, right? Mine did that too ¯\\_(ツ)_/¯. Maybe loading 52 shortcuts at once
was too much for it.

#### I want to go back to the way it was
steamsync will backup your `shortcuts.vdf` file by default every time you run it.

Go to `C:\Program Files (x86)\Steam\userdata\{your steam userid}\config`. You will see some
`shortcuts.vdf-DATE.bak` files. Delete `shortcuts.vdf` (this is the one steamsync modified),
and rename the `.bak` file you want to use to `shortcuts.vdf`, restart steam. 

#### I got a `could not find shortcuts file at ...` error
Try making a shortcut in Steam (Library ➡ ➕ Add Game ➡ Add a Non-Steam Game...) first. 
steamsync will not make a `shortcuts.vdf` file for you if it isn't already there.

#### Can this run automagically?
Yes, yes it can! (you may need to adjust paths below)

1. Open Task Scheduler (start + type "task...")
2. Action Menu ➡ Create Basic Task
3. Fill in a name and description
4. Set the trigger you want to use (daily, log in, etc), Next
5. Action = Start a Program
6. Program/Script is `pythonw`
7. Add arguments `C:\Users\{username}\AppData\Local\Programs\Python\Python38\Scripts\steamsync.py --all --steamid={steam id}`, Next
8. Make sure to restart Steam once in a while

TADA!
