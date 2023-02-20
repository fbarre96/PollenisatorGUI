"""Describe tkinter switch with default common args"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.forms.form import Form


class FormSwitch(Form):
    """
    Form field representing a switch.
    Default setted values: 
        if pack : padx = pady = 5, side = right
        if grid: row = column = 0 sticky = "west"
    Kwargs:
        binds:  a dictionnary of tkinter binding with shortcut as key and callback as value
    """
    def __init__(self, name, text, default, **kwargs):
        """
        Constructor for a form switch
        
        Args:
            name: the switch name (id).
            text: the text on the switch
            default: boolean indicating if the switch should be checked by default.
            kwargs: same keyword args as you would give to CTkSwitch
        """
        super().__init__(name)
        self.text = text
        self.default = bool(default)
        self.kwargs = kwargs
        self.chk = None

    def constructView(self, parent):
        """
        Create the switch view inside the parent view given

        Args:
            parent: parent form panel.
        """
        self.val = tk.IntVar()
        if self.default:
            self.val.set(1)
        else:
            self.val.set(0)
        self.chk = CTkSwitch(
            parent.panel, text=self.text, variable=self.val)
        binds = self.getKw("binds", {})
        for bind in binds:
            self.chk.bind(bind, binds[bind])
        command = self.getKw("command", None)
        if command is not None:
            self.chk.configure(command=command)
        
        if parent.gridLayout:
            self.chk.grid(row=self.getKw("row", 0), column=self.getKw("column", 0), sticky=self.getKw("sticky", tk.W), **self.kwargs)
        else:
            self.chk.pack(side=self.getKw("side", "right"), padx=self.getKw("padx", 10), pady=self.getKw("pady", 5), **self.kwargs)

    def getValue(self):
        """
        Return the form value. Required for a form.

        Returns:
            Return True if the switch was checked, False otherwise.
        """
        return self.val.get() == 1

    def checkForm(self):
        """
        Check if this form is correctly filled. A switch cannot be malformed.

        Returns:
            {
                "correct": True if the form is correctly filled, False otherwise.
                "msg": A message indicating what is not correctly filled.
            }
        """
        return True, ""

    def setFocus(self):
        """Set the focus to the ttk checkbutton."""
        self.chk.focus_set()

    