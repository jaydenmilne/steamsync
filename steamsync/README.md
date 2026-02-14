## steamsync cli
[![PyPI version](https://badge.fury.io/py/steamsync.svg)](https://badge.fury.io/py/steamsync)

Simple command line tool (and poorly documented library!) to automatically add
games from the Epic Games Launcher, Legendary, Xbox/Microsoft Store, or itch.io
to Steam.

Makes playing all of those free EGS games in Big Picture Mode a lot easier. In my experience,
when launching from Big Picture Mode, Steam Input works as expected (even in Fortnite!).

steamsync will scan all supported storefronts for games installed on your computer and
add them to your Steam Library. If a shortcut with the same path already exists, it will
skip it, so it's safe to import all of your games over and over.

By default, steamsync attempts to be simple and doesn't fetch any art. But
there are options for downloading art, removing missing games, and lots more.

### Installation (brief)
Requires Python >=3.10

```console
$ pip install steamsync
$ steamsync
```

## Installation and Usage (for beginners)

1. [Download Python 3.10](https://www.python.org/downloads/)
2. Choose the latest version of Python 3.10, and get the "Windows x86-64 executable installer" option
3. When installing Python, make sure to install pip and to *add Python to your PATH*
4. Open Commmand Prompt (search Start Menu for cmd.exe)
5. Type `pip install steamsync`, press enter.
6. Make sure Steam is not running!
7. Type `steamsync.py`, press enter. The tool will walk you through everything else.
   Press ctrl+c if you get scared and want to abort.

## Usage
```
steamsync -h
usage: steamsync [-h] [--source {legendary,epicstore,itchio,xbox}]
                 [--egs-manifests EGS_MANIFESTS]
                 [--legendary-command LEGENDARY_COMMAND]
                 [--itch-library ITCH_LIBRARY] [--steam-path STEAM_PATH]      
                 [--all] [--steam-api-key STEAM_API_KEY]
                 [--replace-existing] [--remove-missing]
                 [--live-dangerously] [--steamid STEAMID] [--use-uri]
                 [--download-art] [--download-art-all-shortcuts]
                 [--init-shortcuts-file] [--dump-shortcut-vdf]

Utility to import games from the Epic Games Store, Microsoft Store (Xbox for  
Windows), and itch.io to your Steam library

options:
  -h, --help            show this help message and exit
  --source {legendary,epicstore,itchio,xbox}
                        Storefronts with games to add to Steam. If
                        unspecified, uses all sources. Use argument multiple  
                        times to select multiple sources (--source itchio     
                        --source xbox). (default: None)
  --egs-manifests EGS_MANIFESTS
                        Path to search for Epic Games Store manifest files    
                        (default: C:\ProgramData\Epic\EpicGamesLauncher\Data  
                        \Manifests)
  --legendary-command LEGENDARY_COMMAND
                        Command/Path to run 'legendary' executable (default:  
                        legendary)
  --itch-library ITCH_LIBRARY
                        Path where the itch.io app installs games (default:   
                        C:\Users\jayde\AppData\Roaming\itch\itch\apps)        
  --steam-path STEAM_PATH
                        Path to Steam installation (default: C:\Program       
                        Files (x86)\Steam)
  --all                 Install all games found, do not prompt user to        
                        select which (default: False)
  --steam-api-key STEAM_API_KEY
                        Steam API key for fetching app definitions. Required  
                        when you're downloading art. (default: None)
  --replace-existing    Instead of skipping existing shortcuts (ones with     
                        the same path), overwrite them with new data. Useful  
                        to repair broken shortcuts. (default: False)
  --remove-missing      Remove shortcuts to games that no longer exist. Uses  
                        selected sources to determine if games without        
                        executables (uri or Xbox) still exist. i.e., if you   
                        don't include xbox source all xbox games will appear  
                        to be missing. (default: False)
  --live-dangerously    Don't backup Steam's shortcuts.vdf file to
                        shortcuts.vdf-{time}.bak (default: False)
  --steamid STEAMID     SteamID or username to install the shortcuts to,      
                        only needed if >1 accounts on this machine (default:  
                        )
  --use-uri             Use a launcher URI (`com.epicgames.launcher://apps/f  
                        ortnite?action=launch&silent=true`) instead of the    
                        path to the executable (eg
                        `C:\Fortnite\Fortnite.exe`). Some games with online   
                        functionality (eg GTAV) require being launched        
                        through the EGS. Other games work better with Steam   
                        game streaming (eg Steam Link or Big Picture) using   
                        the path to the executable. (default: False)
  --download-art        Download Steam grid and Big Picture art from steam's  
                        servers for games we're adding. Only downloads art    
                        that we haven't already downloaded. (default: False)  
  --download-art-all-shortcuts
                        Download Steam grid and Big Picture art for all non-  
                        steam game shortcuts. Only downloads art that we      
                        haven't already downloaded. Implies --download-art    
                        (default: False)
  --init-shortcuts-file
                        Initialize Steam shortcuts.vdf file if it doesn't     
                        exist. EXPERIMENTAL!! (default: False)
  --dump-shortcut-vdf   For debugging. Print the Steam shortcuts.vdf as text  
                        and exit. (default: False)
```

### FAQ
#### Does this work on OSX?
Probably not. You may have luck with `--egs-manifests` and `--steam-path`, maybe
MRs are welcome

#### What about Linux?
When using [Legendary](https://github.com/derrod/legendary) or [Heroic](https://github.com/Heroic-Games-Launcher/HeroicGamesLauncher) steamsync should work.
Use `--legendary-command` option to path to correct binary if not already in `PATH`.
Not tested with [Rare](https://github.com/Dummerle/Rare)
Not tested with EGS running through Wine.

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
By default steamsync will not make a `shortcuts.vdf` file for you if it isn't already there.
You can enable the experimental functionality for automatically initializing the
`shortcuts.vdf` file with the `--init-shortcuts-file` option.

#### Can this run automagically?
Yes, yes it can! (you may need to adjust paths below)

1. Open Task Scheduler (start + type "task...")
2. Action Menu ➡ Create Basic Task
3. Fill in a name and description
4. Set the trigger you want to use (daily, log in, etc), Next
5. Action = Start a Program
6. Program/Script is `pythonw`
7. Add arguments `C:\Users\{username}\AppData\Local\Programs\Python\Python38\Scripts\steamsync.py --all --steamid={steam id} --remove-missing --download-art`, Next
8. Make sure to restart Steam once in a while

TADA!

## Developing

* `poetry install`
* `poetry run steamsync`
* `potry publish --build`
