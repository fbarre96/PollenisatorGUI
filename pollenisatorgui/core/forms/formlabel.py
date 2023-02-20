"""Describe tkinter Label with default common args"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.forms.form import Form


class FormLabel(Form):
    """
    Form field representing a label.
    Default setted values:
        width=500
        if pack : padx = pady = 5, side = left
        if grid: row = column = 0 sticky = "East"
    """
    def __init__(self, name, text, **kwargs):
        """
        Constructor for a form label
        Args:
            name: the label name.
            text: the text showed by the label.
            kwargs: same keyword args as you would give to CTkLabel
        """
        super().__init__(name)
        self.text = text
        self.kwargs = kwargs

    def constructView(self, parent):
        """
        Create the label view inside the parent view given

        Args:
            parent: parent FormPanel.
        """
        if self.text == "":
            self.text = self.name + " : "
        width=self.getKw("width", None)
        kwargs = {}
        if width is not None:
            kwargs["width"] = int(width)
        lbl = CTkLabel(parent.panel, text=self.text, justify=tk.LEFT, **kwargs)
        if parent.gridLayout:
    
            lbl.grid(column=self.getKw("column", 0), row=self.getKw("row", 0), sticky=self.getKw("sticky", tk.E) , padx=self.getKw("padx", 5), pady=self.getKw("pady", 5), **self.kwargs)
        else:
            lbl.pack(side=self.getKw("side", "left"), padx=self.getKw("padx", 10), pady=self.getKw("pady", 5), **self.kwargs)

    def getValue(self):
        """
        Return the form value. Required for a form.

        Returns:
            Return the label text.
        """
        return self.text
    
    def setValue(self, _newval):
        """nothing to set so overwrite
        Args:
            _newval: not used"""
        return