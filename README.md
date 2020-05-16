# steamsync
[![PyPI version](https://badge.fury.io/py/steamsync.svg)](https://badge.fury.io/py/steamsync) 

Simple command line tool to automatically add games from the Epic Games Launcher
to Steam.

Makes playing all of those free EGS games in Big Picture Mode a lot easier.

## Installation (brief)
Requires > Python 3.6 and Windows

```console
$ pip install steamsync
$ steamsync.py
```

## Installation and Usage (command lines are scary!)

1. [Download Python 3.8](https://www.python.org/downloads/)
2. Choose the latest version of Python 3.8, and get the "Windows x86-64 executable installer" option
3. When installing Python, make sure to install pip and to *add Python to your PATH*
4. Open Commmand Prompt (search Start Menu for cmd.exe)
5. Type `pip install steamsync`, press enter. 
6. Type `steamsync.py`, press enter. The tool will walk you through everything else.
   Press ctrl+c if you get scared

### FAQ
#### Does this work on OSX?
First of all, wow Mac gamers exist. Second of all, it *should* work if you supply
`--egs-manifests` and `--steam-path`, maybe. Good luck

#### What about Linux?
If you get EGS working on Linux, you probably don't need this tool.

#### It doesn't work!
Open an issue on GitHub.
