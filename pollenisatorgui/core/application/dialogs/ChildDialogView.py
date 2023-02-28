"""This class pop a defect view form in a subdialog"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.scrollableframexplateform import ScrollableFrameXPlateform
class ChildDialogView:
    """
    Open a child dialog of a tkinter application to answer a question.
    """
    def __init__(self, parent, title):
        """
        Open a child dialog of a tkinter application to choose autoscan settings.

        Args:
            parent: the tkinter parent view to use for this window construction.
            model : A Defect model object to load default values. None to have empty fields, default is None.
        """
        self.app = CTkToplevel(parent)
        self.app.title(title)
        self.parent = parent
        self.app.resizable(True, True)
        self.app.geometry("800x800")
        self.appFrame = ScrollableFrameXPlateform(self.app)
        self.appFrame.columnconfigure(0, weight=1)
        self.appFrame.rowconfigure(0, weight=1)
        self.rvalue = None
        
    def completeDialogView(self, addButtons=True):
        if addButtons:
            ok_button = CTkButton(self.appFrame, text="OK")
            ok_button.pack(side="right", padx=5, pady=10)
            ok_button.bind('<Button-1>', self.okCallback)
            cancel_button = CTkButton(self.appFrame, text="Cancel")
            cancel_button.pack(side="right", padx=5, pady=10, ipadx=10)
            cancel_button.bind('<Button-1>', self.cancel)
        self.appFrame.pack(fill=tk.BOTH, ipady=10, ipadx=10, expand=True)

        # self.appFrame.pack(fill=tk.X, ipady=10, ipadx=10, expand=True) this break the canvas drawing with scrollbar
        try:
            self.app.wait_visibility()
            self.app.transient(self.parent)
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
        self.rvalue = False
        self.appFrame.unboundToMousewheel()
        self.app.destroy()

    def okCallback(self, _event=None):
        """called when pressing the validating button
        Close the window if the form is valid.
        Set rvalue to True and perform the defect update/insert if validated.
        To be overriden
        Args:
            _event: Not used but mandatory"""
        
        pass

