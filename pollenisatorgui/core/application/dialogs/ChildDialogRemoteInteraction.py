"""Ask the user to select a file or directory and then parse it with the selected parser"""
import tkinter as tk
import tkinter.ttk as ttk
import traceback
from customtkinter import *
from pollenisatorgui.core.components.apiclient import APIClient
import threading
import pollenisatorgui.core.components.utils as utils

class ChildDialogRemoteInteraction:
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
        self.app = CTkToplevel(parent)
        self.app.protocol("WM_DELETE_WINDOW", self.onError)
        self.app.title("Remote interaction with "+str(toolController.getDetailedString()))
        self.toolController = toolController
        self.rvalue = None
        appFrame = CTkFrame(self.app)
        self.text_area = CTkTextbox(appFrame, font=("Consolas", 14), width=800, height=600, fg_color="#000000", text_color="#00ff00")
        self.text_area.insert(tk.END, toolController.getDetailedString()+"\n"+str(toolController.getData().get("infos",{}).get("cmdline", ""))+"\n")
        self.text_area.pack(expand=True)     
        self.text_area.focus_force()
        btn = CTkButton(appFrame, text="Quit", command=self.onError)
        btn.pack()
        self.app.bind("<Escape>", self.onError)
        appFrame.pack(expand=True)
        self.sm = scanManager
        self.timer = threading.Timer(0.5, self.getProgress)
        self.timer.start()
        try:
            self.app.wait_visibility()
            self.app.focus_force()
            self.app.grab_set()
            self.app.lift()
        except tk.TclError:
            pass
            
    
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
            elif isinstance(result, bytes):
                self.text_area.insert(tk.END, result.decode("utf-8").replace("\r","\n"))
            elif result is None:
                return True
            else:
                tk.messagebox.showerror("Could not get progress", result[1], parent=self.app)
                self.onError()
                return False
        except Exception as e:
            tk.messagebox.showerror("Could not get progress", str(e), parent=self.app)
            traceback.print_exc()
            self.onError()
            return False
        self.timer = threading.Timer(2, self.getProgress)
        self.timer.start()
        #self.sio.emit("remoteInteractionGet", {"name":apiclient.getUser(), "db": apiclient.getCurrentPentest(),"id":str(self.toolController.getDbId())})
        return True

    def quit(self):
        #self.sio.disconnect()
        #self.sio.eio.disconnect()
        #self.sio = None
        self.timer.cancel()

    def onError(self, _event=None):
        self.rvalue = None
        self.quit()

        self.app.destroy()

    def onOk(self, _event=None):
        """
        Called when the user clicked the validation button.
        launch parsing with selected parser on selected file/directory.
        Close the window.

        Args:
            _event: not used but mandatory
        """
        self.quit()
        self.app.destroy()
        
