"""Widget with no display that holds a value"""
from pollenisatorgui.core.forms.form import Form
from tkinter import ttk
import tkinter as tk 

class FormSeparator(Form):
    """
    Form field hidden, to store a value.
    """

    def __init__(self, **kwargs):
        """
        Constructor for a hidden form.

        Args:
            name: the form name.
            default: a default value to store in it.
        """
        super().__init__("Separator")
        self.kwargs = kwargs


    def constructView(self, parent):
        """
        Create the button view inside the parent view given

        Args:
            parent: parent form panel.
        """
        self.sep = ttk.Separator(parent.panel,  orient=self.getKw("orient", "horizontal"))
        if parent.gridLayout:
            self.sep.grid(row=self.getKw("row", 0), column=self.getKw("column", 0), columnspan=self.getKw("columnspan", 1), sticky=self.getKw("sticky", tk.W), **self.kwargs)
        else:
            self.sep.pack(side=self.getKw("side", "top"), padx=self.getKw("padx", 5), pady=self.getKw("pady", 5), fill=self.getKw("fill", tk.X),**self.kwargs)

