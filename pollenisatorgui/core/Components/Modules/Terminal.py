import os
from multiprocessing.connection import Listener
from multiprocessing import Process, Manager
import pollenisatorgui.core.Components.Utils as Utils
from pollenisatorgui.core.Components.apiclient import APIClient
import time
import shlex
import pollenisatorgui.AutoScanWorker as slave
from pollenisatorgui.core.Models.Wave import Wave
from pollenisatorgui.core.Models.Tool import Tool
from datetime import datetime
import tkinter as tk
import random
import string
from shutil import which
import subprocess
import signal
from PIL import ImageTk, Image

class Terminal:
    iconName = "tab_terminal.png"
    tabName = "   Terminal  "

    def __init__(self, parent, settings):
        self.settings = settings
        self.proc = None
        self.s = None
        self.img = ImageTk.PhotoImage(Image.open(Utils.getIcon("help.png")))
        manager = Manager()
        self.exiting = manager.Value('i', 0)

    def initUI(self, parent, nbk, treevw):
        if self.settings.isTrapCommand():
            settings_text = "Setting trap command is ON\nEvery command typed here will be executed through pollenisator and will be logged / imported depending on the tools called.\nYou can disable the trap setting in the Settings to change this behaviour."
        else:
            settings_text = "Setting trap command is OFF\ntype 'pollex <YOUR COMMAND with --args>' to execute it through pollenisator\n(plugins will autocomplete the output file and import it once done).\n You can enable the trap setting in the Settings to auto-import each commands without prepending pollex."
        frame = tk.ttk.Frame(parent)
        s = tk.ttk.Style()
        s.configure('big.TLabel', font=('Helvetica', 12), background="white")
        lbl = tk.ttk.Label(frame, image = self.img)
        lbl.pack(anchor=tk.CENTER, side=tk.LEFT)
        lbl = tk.ttk.Label(frame, text = settings_text,  style='big.TLabel')
        lbl.pack(anchor=tk.CENTER, side=tk.RIGHT)
        frame.place(relx=.5, rely=.5, anchor="c")
        return

    def open(self):
        apiclient = APIClient.getInstance()
        favorite = self.settings.getFavoriteTerm()
        if favorite is None:
            tk.messagebox.showerror("Terminal settings invalid", "None of the terminals given in the settings are installed on this computer.")
            return False
        if which(favorite) is not None:
            terms = self.settings.getTerms()
            terms_dict = {}
            for term in terms:
                terms_dict[term.split(" ")[0]] = term
            command_term = terms_dict.get(favorite, None)
            if command_term is not None:
                if self.settings.isTrapCommand():
                    term_comm = terms_dict[favorite].replace("setupTerminalForPentest.sh", os.path.join(Utils.getMainDir(), "setupTerminalForPentest.sh"))
                else:
                    term_comm = term
                subprocess.Popen(term_comm, shell=True)
            else:
                tk.messagebox.showerror("Terminal settings invalid", "Check your terminal settings")
        else:
            tk.messagebox.showerror("Terminal settings invalid", f"{favorite} terminal is not available on this computer. Choose a different one in the settings module.")
        return False

        

    def onClosing(self, _signum=None, _frame=None):
        self.exiting.value = 1
        if self.s:
            self.s.close()

   