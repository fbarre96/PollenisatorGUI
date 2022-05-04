import os
import subprocess
import tkinter as tk
from multiprocessing import Manager
from shutil import which

import pollenisatorgui.core.Components.Utils as Utils
from PIL import Image, ImageTk
from pollenisatorgui.core.Components.apiclient import APIClient
from pollenisatorgui.core.Components.Settings import Settings
from pollenisatorgui.core.Views.WaveView import WaveView
from pollenisatorgui.core.Views.IpView import IpView
from pollenisatorgui.core.Views.PortView import PortView
from pollenisatorgui.core.Views.ScopeView import ScopeView


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

    def initUI(self, parent, nbk, treevw, tkApp):
        self.treevw = treevw
        if self.settings.isTrapCommand():
            settings_text = "Setting trap command is ON\nEvery command typed here will be executed through pollenisator and will be logged / imported depending on the tools called.\nYou can disable the trap setting in the Settings to change this behaviour."
        else:
            settings_text = "Setting trap command is OFF\ntype 'pollex <YOUR COMMAND with --args>' to execute it through pollenisator\n(plugins will autocomplete the output file and import it once done).\n You can enable the trap setting in the Settings to auto-import each commands without prepending pollex."
        frame = tk.ttk.Frame(parent)
        s = tk.ttk.Style()
        s.configure('big.TLabel', font=('Helvetica', 12), background="white")
        lbl = tk.ttk.Label(frame, image=self.img)
        lbl.pack(anchor=tk.CENTER, side=tk.LEFT)
        lbl = tk.ttk.Label(frame, text=settings_text,  style='big.TLabel')
        lbl.pack(anchor=tk.CENTER, side=tk.RIGHT)
        frame.place(relx=.5, rely=.5, anchor="c")
        return

    def open(self):
        self.__class__.openTerminal()
        return True

    @classmethod
    def openTerminal(cls, default_target=""):
        settings = Settings()
        favorite = settings.getFavoriteTerm()
        if favorite is None:
            tk.messagebox.showerror(
                "Terminal settings invalid", "None of the terminals given in the settings are installed on this computer.")
            return False
        if which(favorite) is not None:
            terms = settings.getTerms()
            terms_dict = {}
            for term in terms:
                terms_dict[term.split(" ")[0]] = term
            command_term = terms_dict.get(favorite, None)
            if command_term is not None:
                if settings.isTrapCommand():
                    term_comm = terms_dict[favorite].replace("setupTerminalForPentest.sh", os.path.join(
                        Utils.getMainDir(), "setupTerminalForPentest.sh"))
                else:
                    term_comm = term
                env = {
                    **os.environ,
                    "POLLENISATOR_DEFAULT_TARGET": default_target,
                }
                subprocess.Popen(term_comm, shell=True, env=env)
            else:
                tk.messagebox.showerror(
                    "Terminal settings invalid", "Check your terminal settings")
        else:
            tk.messagebox.showerror(
                "Terminal settings invalid", f"{favorite} terminal is not available on this computer. Choose a different one in the settings module.")
        return False

    def onClosing(self, _signum=None, _frame=None):
        self.exiting.value = 1
        if self.s:
            self.s.close()

    def _initContextualsMenus(self, parentFrame):
        """
        Create a contextual menu
        """
        self.contextualMenu = tk.Menu(parentFrame, tearoff=0, background='#A8CF4D',
                                      foreground='black', activebackground='#A8CF4D', activeforeground='white')
        self.contextualMenu.add_command(
            label="Attack from terminal", command=self.attackFromTerminal)
        return self.contextualMenu

    def attackFromTerminal(self, _event=None):
        for selected in self.treevw.selection():
            view_o = self.treevw.getViewFromId(selected)
            if view_o is not None:
                lvl = "network" if isinstance(view_o, ScopeView) else None
                lvl = "wave" if isinstance(view_o, WaveView) else lvl
                lvl = "ip" if isinstance(view_o, IpView) else lvl
                lvl = "port" if isinstance(view_o, PortView) else lvl
                if lvl is not None:
                    inst = view_o.controller.getData()
                    Terminal.openTerminal(lvl+"|"+inst.get("wave", "Imported")+"|"+inst.get(
                        "scope", "")+"|"+inst.get("ip", "")+"|"+inst.get("port", "")+"|"+inst.get("proto", ""))
                else:
                    tk.messagebox.showerror(
                        "ERROR : Wrong selection", "You have to select a object that may have tools")
