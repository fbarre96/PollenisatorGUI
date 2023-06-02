"""This class pop a dialog to view scan history"""

import tkinter as tk
from customtkinter import *
from pollenisatorgui.core.application.scrollableframexplateform import ScrollableFrameXPlateform
from pollenisatorgui.core.application.scrollabletreeview import ScrollableTreeview
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.models.checkinstance import CheckInstance
from pollenisatorgui.core.models.tool import Tool
from bson.objectid import ObjectId

class ChildDialogScanHistory:
    """
    Open a child dialog of a tkinter application
    """
    def __init__(self, parent):
        """
        Open a child dialog of a tkinter application to choose autoscan checks.

        Args:
            parent: the tkinter parent view to use for this window construction.
        """
        self.app = CTkToplevel(parent)
        #self.app.geometry("800x650")
        self.app.title("Scan history")
        self.app.resizable(True, True)
        self.app.bind("<Escape>", self.cancel)
        self.rvalue = None
        appFrame = CTkFrame(self.app)
        self.parent = None
        self.initUI(appFrame)
        frame_buttons = CTkFrame(self.app)
        ok_button = CTkButton(frame_buttons, text="OK")
        ok_button.pack(side=tk.RIGHT, padx=5)
        ok_button.bind('<Button-1>', self.okCallback)
        cancel_button = CTkButton(frame_buttons, text="Cancel", 
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
        cancel_button.pack(side=tk.RIGHT, padx=5)
        cancel_button.bind('<Button-1>', self.cancel)
        frame_buttons.pack(side=tk.BOTTOM, anchor=tk.SE , padx=5 , pady=5)
        appFrame.pack(fill=tk.BOTH, pady=10, padx=10, expand="yes")

        self.app.transient(parent)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.grab_set()
            self.app.focus_force()
            self.app.lift()
        except tk.TclError:
            pass

    def cancel(self, _event=None):
        """called when canceling the window.
        Close the window and set rvalue to False
        Args:
            _event: Not used but mandatory"""
        self.rvalue = None
        self.app.destroy()

    def okCallback(self, _event=None):
        """called when pressing the validating button
        Close the window if the form is valid.
        Set rvalue to True and perform the defect update/insert if validated.
        Args:
            _event: Not used but mandatory"""
        
        self.rvalue = []
        self.app.destroy()

    def initUI(self, frame):
        self.histoScanTv = ScrollableTreeview(frame, ('History category', 'Name', 'Ended at'), height=25, keys=(None, None, utils.stringToDate))
        self.histoScanTv.pack(fill=tk.BOTH, expand="yes", padx=10, pady=10)
        self.refreshUI()

    def refreshUI(self):
        done_scans = list(Tool.fetchObjects({"status":"done"}))
        checks = CheckInstance.fetchObjects([ObjectId(done_scan.check_iid) for done_scan in done_scans if done_scan.check_iid != ""])
        mapping = {}
        for check in checks:
            mapping[str(check._id)] = check
        self.histoScanTv.reset()
        for done_scan in done_scans:
            check = mapping.get(str(done_scan.check_iid), None)
            group_name = "" if check is None else check.check_m.title
            try:
                self.histoScanTv.insert('',0, done_scan.getId(), text=group_name, values=(done_scan.name, done_scan.datef))
            except tk.TclError as e:
                print(e)
        
