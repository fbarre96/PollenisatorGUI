"""Frame for remote terminal emulation"""
import tkinter as tk
import tkinter.ttk as ttk
import traceback
from customtkinter import *
from pollenisatorgui.core.components.apiclient import APIClient
import threading
import pollenisatorgui.core.components.utils as utils


class PseudoTermFrame(CTkFrame):
    """
    Open a child dialog of a tkinter application to show a text area.
    """

    def __init__(self, parent, toolController, scanManager):
        """
        Open a child dialog of a tkinter application to ask details about
        existing files parsing.

        Args:
            default_path: a default path to be added
        """
        super().__init__(parent)
        self.parent = parent
        self.toolController = toolController
        self.rvalue = None
        self.text_area = CTkTextbox(self, font=("Consolas", 14), fg_color="#000000", text_color="#00ff00")
        self.text_area.insert(tk.END, toolController.getDetailedString()+"\n"+str(toolController.getData().get("infos",{}).get("cmdline", ""))+"\n")
        self.text_area.pack(expand=True, fill=tk.BOTH)     
        self.text_area.focus_force()
        self.pack(expand=True)
        self.sm = scanManager
        self.timer = threading.Timer(0.5, self.getProgress)
        self.timer.start()
            
    
    def getProgress(self):
        # Print the key that was pressed
        if self.sm.is_local_launched(str(self.toolController.getDbId())):
            result = self.sm.getToolProgress(str(self.toolController.getDbId()))
        else:
            apiclient = APIClient.getInstance()
            result = apiclient.getToolProgress(str(self.toolController.getDbId()))
        try:
            if isinstance(result, str):
                self.text_area.insert(tk.END, result.replace("\r","\n"))
            elif isinstance(result, bool) and result:
                self.text_area.insert(tk.END, "Scan ended. You can quit and download result file.")
                return True
            elif isinstance(result, bool) and not result:
                pass #
            elif isinstance(result, bytes):
                self.text_area.insert(tk.END, result.decode("utf-8").replace("\r","\n"))
            elif result is None:
                return True
            else:
                self.text_area.insert(tk.END, f"Could not get progress : {result[1]}")
                return False
        except Exception as e:
            self.text_area.insert(tk.END, f"Could not get progress : {e}")
            traceback.print_exc()
            self.timer.cancel()
            return False
        self.timer = threading.Timer(0.2, self.getProgress)
        self.timer.start()
        #self.sio.emit("remoteInteractionGet", {"name":apiclient.getUser(), "db": apiclient.getCurrentPentest(),"id":str(self.toolController.getDbId())})
        return True

    def quit(self):
        if self.timer is not None:
            self.timer.cancel()
            