import wx
import os
import steamsync
from io import StringIO
import sys
import tempfile
import traceback
import time
import wx.lib.agw.hyperlink as hl

# I'd like to apologize for the general mess that this file is
# I never did this before, and really didn't care too much

VERSION = "0.3.0"
SLUG = f"steamsync v{VERSION} - "


class LocationPicker(wx.Frame):
    def next(self, event):
        # check steam
        steamPath = self.steamLocation.GetPath()
        userdata = os.path.join(steamPath, "userdata")
        error = False

        if not os.path.exists(steamPath):
            error = f"The path `{steamPath}` does not seem to exist"
        elif not os.path.exists(userdata):
            error = f"The path `{userdata}` does not exist, is that actually a steam install directory?"

        if error:
            dialog = wx.MessageDialog(
                self.pnl,
                error,
                caption="Error",
                style=wx.OK | wx.CENTER | wx.ICON_ERROR,
                pos=wx.DefaultPosition,
            )
            dialog.ShowModal()

        # check egs
        legendaryPath = self.egsLocation.GetPath()
        egsPath = self.egsLocation.GetPath()
        manifests = os.path.join(egsPath, "Data", "Manifests")
        if not (os.path.exists(legendaryPath) or os.path.exists(egsPath)):
            error = f"The path `{legendaryPath or egsPath}` does not seem to exist"
        elif os.path.exists(egsPath) and not os.path.exists(manifests):
            error = f"The path `{manifests}` does not exist, is that actually an epic games store install directory?"

        if error:
            dialog = wx.MessageDialog(
                self.pnl,
                error,
                caption="Error",
                style=wx.OK | wx.CENTER | wx.ICON_ERROR,
                pos=wx.DefaultPosition,
            )
            dialog.ShowModal()
            return
        self.Hide()

        print("steampath", steamPath)
        print("manifestPath", manifests)

        self.mainFrame = MainFrame(steamPath, manifests, legendaryPath)
        self.mainFrame.Show()
        self.Destroy()
        pass

    def __init__(self, *args, **kw):
        super(LocationPicker, self).__init__(*args, **kw)

        global CAPTURE_ERRORS
        if CAPTURE_ERRORS:
            sys.excepthook = handleexception

        self.pnl = wx.Panel(self)
        st = wx.StaticText(self.pnl, label="Steam installation:")
        self.steamLocation = wx.DirPickerCtrl(
            self.pnl, path="C:\\Program Files (x86)\\Steam"
        )

        egst = wx.StaticText(self.pnl, label="Epic Games Store installation:")
        self.egsLocation = wx.DirPickerCtrl(
            self.pnl, path="C:\\ProgramData\\Epic\\EpicGamesLauncher"
        )

        legendarytT = wx.StaticText(self.pnl, label="Epic Games Store installation:")
        self.legendaryLocation = wx.DirPickerCtrl(
            self.pnl, path=""
        )

        nextButton = wx.Button(self.pnl, label="Next")
        nextButton.Bind(wx.EVT_BUTTON, self.next)

        sizer = wx.BoxSizer(wx.VERTICAL)
        flags = wx.EXPAND
        sizer.AddSpacer(15)
        sizer.Add(st, 0, flags)
        sizer.Add(self.steamLocation, 0, flags)
        sizer.AddSpacer(15)
        sizer.Add(egst, 0, flags)
        sizer.Add(self.egsLocation, 0, flags)
        sizer.Add(legendarytT, 0, flags)
        sizer.Add(self.legendaryLocation, 0, flags)
        sizer.AddSpacer(15)
        sizer.Add(nextButton, 0, flags)
        sizer.AddSpacer(15)
        sizer.Add(
            hl.HyperLinkCtrl(
                self.pnl,
                label="steamsync by Jayden Milne",
                URL="https://github.com/jaydenmilne/steamsync",
            ),
            0,
        )
        sizer.AddSpacer(15)

        self.pnl.SetSizer(sizer)

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        if self.mainFrame:
            self.mainFrame.Close(True)
        self.Close(True)
        self.DestroyChildren()
        self.Destroy()


USE_URI = "Use Epic Games Store URL (works best with games with launchers, GTAV)"
USE_PATH = "Use path to game (works best with Big Picture + Steam Input)"


class MainFrame(wx.Frame):
    def add_shortcuts(self, event):

        checked = self.checkListBox.GetCheckedStrings()
        # this is a list of strings, we want to turn it into a list of games
        lookup = {x.display_name: x for x in self.allGames}
        selected_games = []
        for item in checked:
            selected_games.append(lookup[item])

        # get if we want to use paths or not
        use_uri = (
            True
            if self.path_mode_radio.GetString(self.path_mode_radio.GetSelection())
            == USE_URI
            else False
        )

        selected_username = self.user_radio.GetString(self.user_radio.GetSelection())
        # figure out the steam id of the username that is selected
        for user in self.users:
            if user.username == selected_username:
                steam_id = user.steamid
                break

        game_results_tuple, error = steamsync.add_games_to_shortcut_file(
            self.steam_path, steam_id, selected_games, False, use_uri
        )

        if error is not None:
            # display the modal
            dialog = wx.MessageDialog(
                self.pnl,
                error,
                caption="Error",
                style=wx.OK | wx.CENTER | wx.ICON_ERROR,
                pos=wx.DefaultPosition,
            )
            dialog.ShowModal()
            dialog.Destroy()
            return

        results, num = game_results_tuple
        game_results_str = f"Great success! Added {num} games"
        if len(results) != 0:

            for r in results:
                game_results_str += f"\r\n{r}"

        # this really probably should be another window, but for maximum laziness, let's just do it here!
        dialog = wx.MessageDialog(
            self.pnl,
            game_results_str,
            caption="Did Something!",
            style=wx.OK | wx.CENTER,
            pos=wx.DefaultPosition,
        )
        dialog.ShowModal()
        dialog.Destroy()
        dialog = wx.MessageDialog(
            self.pnl,
            "Please restart Steam!\r\nNote that if you imported a lot of games, Steam may lock up while loading all the icons",
            caption="Restart Steam",
            style=wx.OK | wx.CENTER,
            pos=wx.DefaultPosition,
        )
        dialog.ShowModal()
        dialog.Destroy()

    def selectAll(self, event):
        self.checkListBox.SetCheckedItems(range(0, len(self.allGames)))

    def selectNone(self, event):
        self.checkListBox.SetCheckedItems([])

    def __init__(self, steam_path, manifests, legendaryPath):
        super(MainFrame, self).__init__(
            None, title=SLUG + "Select Games", size=(600, 1000)
        )

        global CAPTURE_ERRORS
        if CAPTURE_ERRORS:
            sys.excepthook = handleexception

        self.pnl = wx.Panel(self)
        self.steam_path = steam_path
        self.users = steamsync.enumerate_steam_accounts(steam_path)
        self.user_radio = wx.RadioBox(
            self.pnl,
            id=wx.ID_ANY,
            style=wx.RA_SPECIFY_ROWS,
            choices=sorted([sa.username for sa in self.users]),
            label="Steam Account",
        )

        self.path_mode_radio = wx.RadioBox(
            self.pnl,
            id=wx.ID_ANY,
            style=wx.RA_SPECIFY_ROWS,
            choices=[USE_PATH, USE_URI],
            label="Shortcut Path Mode",
        )

        if legendaryPath:
            # TODO: Get user input if they want art
            self.allGames = steamsync.egs_collect_games(legendaryPath, True)
        else:
            self.allGames = steamsync.egs_collect_games(manifests)
        self.checkListBox = wx.CheckListBox(
            self.pnl,
            id=wx.ID_ANY,
            choices=sorted([f"{g.display_name}" for g in self.allGames]),
        )
        st = wx.StaticText(
            self.pnl, label=f"Collected {len(self.allGames)} Epic Games Store games"
        )

        addShortcutsBtn = wx.Button(
            self.pnl,
            label="Add Shortcuts To Steam",
        )
        addShortcutsBtn.Bind(wx.EVT_BUTTON, self.add_shortcuts)

        selectAllBtn = wx.Button(self.pnl, label="Select All")
        selectAllBtn.Bind(wx.EVT_BUTTON, self.selectAll)
        selectNoneBtn = wx.Button(self.pnl, label="Select None")
        selectNoneBtn.Bind(wx.EVT_BUTTON, self.selectNone)

        btnbar = wx.BoxSizer(wx.HORIZONTAL)
        btnbar.Add(selectAllBtn, 1, wx.EXPAND)
        btnbar.Add(selectNoneBtn, 1, wx.EXPAND)

        headingFont = wx.Font(wx.FontInfo(13).Bold())

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(15)
        heading1 = wx.StaticText(self.pnl, label="1. Select a Steam Account:")
        heading1.SetFont(headingFont)
        sizer.Add(heading1)
        sizer.Add(self.user_radio, 0, wx.EXPAND)
        sizer.AddSpacer(15)
        heading2 = wx.StaticText(self.pnl, label="2. Select path mode:")
        heading2.SetFont(headingFont)
        sizer.Add(heading2)

        sizer.Add(self.path_mode_radio, 0, wx.EXPAND)
        sizer.AddSpacer(15)
        heading3 = wx.StaticText(self.pnl, label="3. Select Games:")
        heading3.SetFont(headingFont)
        sizer.Add(heading3)
        sizer.Add(btnbar, 0)
        sizer.Add(self.checkListBox, 1, wx.ALL | wx.LEFT | wx.RIGHT | wx.EXPAND)
        sizer.Add(st, 0)
        sizer.AddSpacer(15)
        heading4 = wx.StaticText(self.pnl, label="4. Submit when done:")
        heading4.SetFont(headingFont)
        sizer.Add(heading4)
        addShortcutsBtn.SetFont(headingFont)
        sizer.Add(
            addShortcutsBtn,
            0,
            wx.EXPAND,
        )
        sizer.AddSpacer(15)
        sizer.Add(
            hl.HyperLinkCtrl(
                self.pnl,
                label="steamsync by Jayden Milne",
                URL="https://github.com/jaydenmilne/steamsync",
            ),
            0,
        )
        sizer.AddSpacer(15)
        self.pnl.SetSizer(sizer)

        self.selectAll(None)

    def load(self, steamPath, userdata, egsManifests):
        self.user_radio.Add

    def OnExit(self, event):
        self.Close(True)
        self.DestroyChildren()
        self.Destroy()


# redirect stdout to buffer for logging
old_stdout = sys.stdout
sys.stdout = mystdout = StringIO()


# handle exceptions to pop up notepad and show log when something bad happens
def handleexception(etype, value, trace):
    print("Exception!!!")
    global mystdout
    tmp = "\r\n".join(traceback.format_exception(etype, value, trace))
    output = f"{SLUG} Encountered An Error. Please submit a bug report at https://github.com/jaydenmilne/steamsync/issues with this log!\r\n{tmp}\r\n\r\nLog:\r\n\r\n{mystdout.getvalue()}"
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.write(bytearray(output, "utf-8"))
    name = tf.name
    tf.close()
    time.sleep(1)
    os.system(f"notepad {name}")
    sys.stdout = old_stdout
    sys.exit(1)


# this may not actually work
CAPTURE_ERRORS = True

if CAPTURE_ERRORS:
    sys.excepthook = handleexception

if __name__ == "__main__":
    app = wx.App()
    frm = LocationPicker(None, title=SLUG + "Choose Directories")
    frm.Show()
    app.MainLoop()
