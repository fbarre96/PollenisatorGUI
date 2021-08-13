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

class Terminal:
    iconName = "tab_terminal.png"
    tabName = "   Terminal  "

    def __init__(self, parent, settings):
        self.settings = settings
        self.proc = None
        self.s = None
        manager = Manager()
        self.exiting = manager.Value('i', 0)

    def initUI(self, parent, nbk, treevw):
        lbl = tk.ttk.Label(parent, text="You can use the 'pollex' command in the terminal that opened to launch tools and auto-import results.")
        lbl.pack(pady=50)
        return

    def open(self):
        apiclient = APIClient.getInstance()
        if self.proc is None:
            password = os.environ.get("POLLEX_PASS", None)
            if password is None:
                characters = string.ascii_letters + string.digits + string.punctuation
                password = ''.join(random.choice(characters) for i in range(15))
            os.environ["POLLEX_PASS"] = password
            self.proc = Process(target=self.takeCommands, args=(apiclient, self.exiting))
            self.proc.daemon = True
            self.proc.start()
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

    def takeCommands(self, apiclient, exiting):
        APIClient.setInstance(apiclient)
        signal.signal(signal.SIGINT, self.onClosing)
        address = ('localhost', 10817)
        password = os.environ["POLLEX_PASS"]
        excludedCommands = ["echo"]
        # LISTEN
        self.s = Listener(address, authkey=password.encode())
        while not exiting.value:
            try:
                connection = self.s.accept()
            except:
                return False
            execCmd = connection.recv().decode()
            cmdName = os.path.splitext(os.path.basename(execCmd.split(" ")[0]))[0]
            if cmdName in excludedCommands:
                connection.close()
                continue
            args = shlex.join(shlex.split(execCmd)[1:])
            cmdName +="::"+str(time.time()).replace(" ","-")
            wave = Wave().initialize("Custom commands")
            wave.addInDb()
            tool = Tool()
            tool.initialize(cmdName, "Custom commands", "", None, None, None, "wave", execCmd, dated=datetime.now().strftime("%d/%m/%Y %H:%M:%S"), datef="None", scanner_ip="localhost")
            tool.updateInfos({"args":args})
            res, iid = tool.addInDb()
            if res:
                ret_code, outputfile = slave.executeCommand(apiclient, str(iid), "auto-detect", True, True)
            connection.send(outputfile)
            connection.close()
        self.s.close()
        return True