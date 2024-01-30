"""Defines a dialog window for choosing 1 between option many thourgh a combobox"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
import pollenisatorgui.core.components.utils as utils

class ChildDialogCombo:
    """
    Open a child dialog of a tkinter application with a combobox.
    """
    def __init__(self, parent, options, displayMsg="Choose a database to open", default=None, **kwargs):
        """
        Open a child dialog of a tkinter application to ask a combobox option.

        Args:
            parent: the tkinter parent view to use for this window construction.
            options: A list of string correspondig to options of the combobox
            displayMsg: The message that will explain to the user what he is choosing.
            default: Choose a default selected option (one of the string in options). default is None
        """
        self.app = CTkToplevel(parent, fg_color=utils.getBackgroundColor())
        self.app.title("Choose option")
        self.app.attributes("-type", "dialog")
        self.app.resizable(False, False)
        self.app.bind("<Escape>", self.onError)
        appFrame = CTkFrame(self.app)
        self.rvalue = None
        self.parent = parent
        if options is None:
            self.onError()
        lbl = CTkLabel(appFrame, text=displayMsg)
        lbl.pack(pady=5)
        kw = {}
        if kwargs.get('width', None) is not None:
            kw["width"] = int(kwargs["width"])
        self.box_template = CTkComboBox(
            appFrame, values=tuple(options), state="readonly",  **kw)
        if default is not None:
            self.box_template.set(default)
        self.box_template.pack(padx=10, pady=5)
        self.box_template.focus_set()
        self.ok_button = CTkButton(appFrame, text="OK", command=self.onOk)
        self.ok_button.bind('<Return>', self.onOk)
        self.ok_button.pack(padx=10, pady=5)
        appFrame.pack(ipadx=10, ipady=5)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.grab_set()
            self.app.focus_force()
            self.app.lift()
        except tk.TclError:
            pass
        self.box_template.after(50, self.openCombo)

    def openCombo(self):
        self.box_template.event_generate('<Button-1>')

    def onOk(self, event=""):
        """
        Called when the user clicked the validation button. Set the rvalue attributes to the value selected and close the window.
        """
        # send the data to the parent
        self.rvalue = self.box_template.get()
        self.app.destroy()

    def onError(self, _event=None):
        """
        Close the dialog and set rvalue to None
        """
        self.rvalue = None
        self.app.destroy()
