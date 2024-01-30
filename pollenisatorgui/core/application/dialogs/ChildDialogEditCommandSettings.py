"""Defines a dialog window for filling a tool settings"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.forms.formpanel import FormPanel
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.views.viewelement import ViewElement
import pollenisatorgui.core.components.utils as utils

class ChildDialogEditCommandSettings:
    """
    Open a child dialog of a tkinter application to fill settings for a command
    """

    def __init__(self, parent, displayMsg="Choose a database to open", default=None):
        """
        Open a child dialog of a tkinter application to ask a combobox option.

        Args:
            parent: the tkinter parent view to use for this window construction.
            options: A list of string correspondig to options of the combobox
            displayMsg: The message that will explain to the user what he is choosing.
            default: Choose a default selected option (one of the string in options). default is None
        """
        self.app = CTkToplevel(parent)
        self.app.attributes("-type", "dialog")
        self.app.title("Edit command settings")
        self.rvalue = None
        self.parent = parent
        appFrame = CTkFrame(self.app)
        self.app.bind("<Escape>", self.onError)
        self.form = FormPanel()
        self.form.addFormLabel(displayMsg, side=tk.TOP)
        optionsFrame = self.form.addFormPanel(grid=True)
        optionsFrame.addFormLabel("Remote bin path", row=0, column=0)
        optionsFrame.addFormStr("bin", r".+", row=0, column=1)
        optionsFrame.addFormLabel("Plugin", row=1, column=0)
        apiclient = APIClient.getInstance()
        optionsFrame.addFormCombo("plugin", tuple([x["plugin"] for x in apiclient.getPlugins()]), row=1, column=1)
        self.form.addFormButton("Cancel", self.onError, 
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
        self.form.addFormButton("OK", self.onOk)
        self.form.constructView(appFrame)
        appFrame.pack(ipadx=10, ipady=10)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.focus_force()
            self.app.grab_set()
            self.app.lift()
        except tk.TclError:
            pass

    def onOk(self, _event=None):
        """
        Called when the user clicked the validation button. Set the rvalue attributes to the value selected and close the window.
        """
        # send the data to the parent
        res, msg = self.form.checkForm()
        if not res:
            tk.messagebox.showwarning(
                "Form not validated", msg, parent=self.app)
            return
        form_values = self.form.getValue()
        form_values_as_dicts = ViewElement.list_tuple_to_dict(form_values)
        self.rvalue = (form_values_as_dicts["bin"], form_values_as_dicts["plugin"])
        self.app.destroy()

    def onError(self, _event=None):
        """
        Close the dialog and set rvalue to None
        """
        self.rvalue = None
        self.app.destroy()
