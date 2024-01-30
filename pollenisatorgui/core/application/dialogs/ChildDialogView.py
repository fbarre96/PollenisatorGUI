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
    def __init__(self, parent, title, scrollable=False):
        """
        Open a child dialog of a tkinter application to choose autoscan settings.

        Args:
            parent: the tkinter parent view to use for this window construction.
            model : A Defect model object to load default values. None to have empty fields, default is None.
        """
        self.app = CTkToplevel(parent)
        self.app.attributes("-type", "dialog")
        self.app.title(title)
        self.parent = parent
        self.app.resizable(True, True)
        self.app.bind("<Escape>", self.cancel)
        #self.app.geometry("1000x1000")
        if scrollable:
            self.appFrame = ScrollableFrameXPlateform(self.app)
        else:
            self.appFrame = CTkFrame(self.app)
        self.appFrame.columnconfigure(0, weight=1)
        self.appFrame.rowconfigure(0, weight=1)
        self.rvalue = None
        
    def completeDialogView(self, **kwargs):
        if kwargs.get("addButtons", True):
            ok_button = CTkButton(self.appFrame, text=kwargs.get("text_ok", "OK"))
            ok_button.pack(side="right", padx=5, pady=10)
            ok_button.bind('<Button-1>', self.okCallback)
            cancel_button = CTkButton(self.appFrame, text="Cancel", fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
            cancel_button.pack(side="right", padx=5, pady=10, ipadx=3)
            cancel_button.bind('<Button-1>', self.cancel)
        self.appFrame.pack(fill=tk.BOTH, ipady=10, ipadx=10, expand=True)
        self.app.update()
        # self.appFrame.pack(fill=tk.X, ipady=10, ipadx=3, expand=True) this break the canvas drawing with scrollbar
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
        self.app.destroy()

    def okCallback(self, _event=None):  
        """called when pressing the validating button
        Close the window if the form is valid.
        Set rvalue to True and perform the defect update/insert if validated.
        To be overriden
        Args:
            _event: Not used but mandatory"""
        
        pass

