import sys
from threading import Thread
from time import sleep
import tkinter.ttk as ttk
import tkinter as tk
import requests
from PIL import Image, ImageTk


sys.path.append("..")
from _version import __version__
from Logging import logger
from Globals import app_icon, app_name, gClass
from utils.Helper import OpenUrl, nativeNotify
from .Tooltip import CreateToolTip

# Classes
class AboutWindow:
    """About Window"""

    # ----------------------------------------------------------------------
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("About Speech Translate")
        self.root.geometry("375x220")
        self.root.wm_withdraw()

        # Top frame
        self.topFrame = tk.Frame(self.root, bg="white")
        self.topFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.bottomFrame = tk.Frame(self.root, bg="#F0F0F0")
        self.bottomFrame.pack(side=tk.BOTTOM, fill=tk.X, expand=False)

        self.bottomLeft = tk.Frame(self.bottomFrame, bg="#F0F0F0")
        self.bottomLeft.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.botLeftTop = tk.Frame(self.bottomLeft, bg="#F0F0F0")
        self.botLeftTop.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.botLeftBottom = tk.Frame(self.bottomLeft, bg="#F0F0F0")
        self.botLeftBottom.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.bottomRight = tk.Frame(self.bottomFrame, bg="#F0F0F0")
        self.bottomRight.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Top frame
        try:  # Try catch the logo so if logo not found it can still run
            self.canvasImg = tk.Canvas(self.topFrame, width=98, height=98, bg="white")
            self.canvasImg.pack(side=tk.TOP, padx=5, pady=5)
            self.imgObj = Image.open(app_icon)
            self.imgObj = self.imgObj.resize((100, 100), Image.ANTIALIAS)

            self.img = ImageTk.PhotoImage(self.imgObj, master=self.canvasImg)
            self.canvasImg.create_image(2, 50, anchor=tk.W, image=self.img)
        except Exception:
            self.logoNotFoud = tk.Label(self.topFrame, text="Fail To Load Logo, Logo not found", bg="white", fg="red")
            self.logoNotFoud.pack(side=tk.TOP, padx=5, pady=5)
            self.root.geometry("375x325")

        self.titleLabel = tk.Label(self.topFrame, text="Speech Translate", bg="white", font=("Helvetica", 12, "bold"))
        self.titleLabel.pack(padx=5, pady=2, side=tk.TOP)

        self.contentLabel = tk.Label(
            self.topFrame,
            text="An open source Speech Transcription and Translation tool.\nMade using Whisper OpenAI and some translation API.",
            bg="white",
        )
        self.contentLabel.pack(padx=5, pady=0, side=tk.TOP)

        # Label for version
        self.versionLabel = tk.Label(self.botLeftTop, text=f"Version: {__version__}", font=("Segoe UI", 8))
        self.versionLabel.pack(padx=5, pady=2, ipadx=0, side=tk.LEFT)

        # Label for Icons credit
        self.checkUpdateLabelText = "Click to check for update"
        self.checkUpdateLabelFg = "blue"
        self.checkUpdateLabelFunc = self.check_for_update
        self.checkUpdateLabel = tk.Label(self.botLeftBottom, text=self.checkUpdateLabelText, font=("Segoe UI", 8), fg=self.checkUpdateLabelFg)
        self.checkUpdateLabel.pack(padx=5, pady=0, side=tk.LEFT)
        self.checkUpdateLabel.bind("<Button-1>", self.checkUpdateLabelFunc)
        self.tooltipCheckUpdate = CreateToolTip(self.checkUpdateLabel, "Click to check for update")

        # Button
        self.okBtn = ttk.Button(self.bottomRight, text="Close", command=self.on_closing, width=10)
        self.okBtn.pack(padx=5, pady=5, side=tk.RIGHT)

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ------------------------------
        gClass.about = self  # type: ignore
        self.checking = False
        self.checkedGet = None

    # Show/Hide
    def show(self):
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    # Open link
    def open_dl_link(self, _event=None):
        OpenUrl("https://github.com/Dadangdut33/Speech-Translate/releases/tag/latest")

    def check_for_update(self, _event=None):
        if self.checking:
            return

        self.checking = True
        self.checkUpdateLabelText = "Checking..."
        self.checkUpdateLabelFg = "black"
        self.tooltipCheckUpdate.text = "Checking... Please wait"
        self.checkUpdateLabel.config(text=self.checkUpdateLabelText, fg=self.checkUpdateLabelFg)
        self.root.update()
        logger.info("Checking for update...")

        Thread(target=self.req_update_check, daemon=True).start()
        self.root.after(250, self.checking_thread)

    def checking_thread(self):
        if not self.checking:
            logger.info("Checking done")
            if self.checkedGet is not None and self.checkedGet.status_code == 200:
                data = self.checkedGet.json()
                latest_version = data["tag_name"]
                if latest_version == __version__:
                    logger.info("No update available")
                    self.checkUpdateLabelText = "You are using the latest version"
                    self.checkUpdateLabelFg = "green"
                    self.checkUpdateLabelFunc = self.check_for_update
                    self.tooltipCheckUpdate.text = "Up to date"
                else:
                    logger.info(f"New version found: {latest_version}")
                    self.checkUpdateLabelText = "New version available"
                    self.checkUpdateLabelFg = "blue"
                    self.checkUpdateLabelFunc = self.open_dl_link
                    self.tooltipCheckUpdate.text = "Click to go to the latest release page"
                    nativeNotify("New version available", "Click to go to the latest release page", app_icon, app_name)
            else:
                logger.error("Failed to check for update")
                self.checkUpdateLabelText = "Fail to check for update!"
                self.checkUpdateLabelFg = "red"
                self.checkUpdateLabelFunc = self.check_for_update
                self.tooltipCheckUpdate.text = "Click to try again"
                nativeNotify("Fail to check for update!", "Click to try again", app_icon, app_name)

            # update after checking done
            self.checkUpdateLabel.config(text=self.checkUpdateLabelText, fg=self.checkUpdateLabelFg)
            self.checkUpdateLabel.bind("<Button-1>", self.checkUpdateLabelFunc)

            return

        # logger.debug("Checking...")
        self.root.after(250, self.checking_thread)

    def req_update_check(self):
        try:
            # request to github api, compare version. If not same tell user to update
            self.checkedGet = requests.get("https://api.github.com/repos/Dadangdut33/Speech-Translate/releases/latest")
        except Exception as e:
            logger.exception(e)
        finally:
            self.checking = False