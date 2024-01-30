"""This class pop a dialog to select checks"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from PIL import ImageTk, Image
from pollenisatorgui.core.application.scrollableframexplateform import ScrollableFrameXPlateform
from pollenisatorgui.core.components.apiclient import APIClient
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.forms.formpanel import FormPanel
from pollenisatorgui.core.models.checkitem import CheckItem
from pollenisatorgui.core.models.command import Command


class ChildDialogSelectChecks:
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
        self.app.attributes("-type", "dialog")
        self.app.title("Choose checks")
        self.app.resizable(True, True)
        self.app.bind("<Escape>", self.cancel)
        self.rvalue = None
        appFrame = ScrollableFrameXPlateform(self.app)
        self.parent = None
        self.initUI(appFrame)
        ok_button = CTkButton(appFrame, text="OK")
        ok_button.pack(side="right", padx=5, pady=10)
        ok_button.bind('<Button-1>', self.okCallback)
        cancel_button = CTkButton(appFrame, text="Cancel", 
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
        cancel_button.pack(side="right", padx=5, pady=10)
        cancel_button.bind('<Button-1>', self.cancel)
        appFrame.pack(fill=tk.BOTH, ipady=10, ipadx=10, expand=True)

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

    def initUI(self, parent):
        self.parent = parent
        self.form = FormPanel()
        self.form.addFormLabel("Select checks to queue for autoscan")
        apiclient = APIClient.getInstance()
        check_items = CheckItem.fetchObjects({"check_type":"auto_commands"})
        commands = Command.getList({}, apiclient.getCurrentPentest())
        for check_item in check_items:
            collapsible = self.form.addFormPanel(check_item.title)
            check_commands = [command for command in commands if str(command.original_iid) in check_item.commands]
            for command in check_commands:
                collapsible.addFormCheckbox(command.name, command.name, True)
        self.form.constructView(parent)
            
            