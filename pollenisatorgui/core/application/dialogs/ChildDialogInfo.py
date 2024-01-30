"""Display a simple information for the user.
"""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *


class ChildDialogInfo:
    """
    Open a child dialog of a tkinter application to inform the user.
    """

    def __init__(self, parent, title, msg):
        """
        Open a child dialog of a tkinter application to choose autoscan settings.

        Args:
            parent: the tkinter parent view to use for this window construction.
            title: title of the popup window
            msg: Message to show to the user
        """
        self.app = CTkToplevel(parent)
        self.app.attributes("-type", "dialog")
        self.app.resizable(False, False)
        self.app.title(title)
        self.app.bind("<Escape>", self.destroy)
        appFrame = CTkFrame(self.app)
        self.rvalue = None
        self.parent = parent
        lbl = CTkLabel(appFrame, text=msg)
        lbl.pack(side=tk.TOP, padx=10, pady=10, fill=tk.X)
        appFrame.pack(fill=tk.BOTH)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.focus_force()
            #self.app.grab_set()
            self.app.lift()
        except tk.TclError:
            pass

    def show(self):
        """Start displaying this window."""
        self.app.update()

    def destroy(self, _event=None):
        """
        Close the window.
        """
        # send the data to the parent
        self.rvalue = None
        self.app.destroy()
