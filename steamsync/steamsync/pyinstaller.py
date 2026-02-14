import PyInstaller.__main__
from pathlib import Path

HERE = Path(__file__).parent.absolute()
path_to_main = str(HERE / "steamsync.py")

def install():
    PyInstaller.__main__.run([
        path_to_main,
        '--console',
        '--onefile',
        '--icon',
        str(HERE.parent / 'logo.ico')
    ])