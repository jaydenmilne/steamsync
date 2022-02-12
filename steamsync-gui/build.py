import os

VERSION = "0.3.0"
filename = f"steamsync-{VERSION}.exe"

os.system(
    f"pyinstaller --onefile .\main.py --name {filename} --noconsole --icon logo.ico"
)
