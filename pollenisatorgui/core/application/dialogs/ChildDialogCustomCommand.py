"""Deprecated.
Ask the user to enter a command and select a worker and plugin to launch it."""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.application.pollenisatorentry import PopoEntry

class ChildDialogCustomCommand:
    """
    Open a child dialog of a tkinter application to ask details about
    a custom command to launch on target.
    """

    def __init__(self, parent, workers, default_worker="localhost"):
        """
        Open a child dialog of a tkinter application to ask details about
        a custom command to launch on target.

        Args:
            parent: the tkinter parent view to use for this window construction.
            workers: A list of workers registered.
            default_worker: a worker to be selected by default.
        """
        self.app = CTkToplevel(parent)
        self.app.attributes("-type", "dialog")
        self.app.title("Custom command")
        appFrame = CTkFrame(self.app)
        self.app.bind("<Escape>", self.onError)
        self.app.resizable(False, False)
        self.rvalue = None
        self.parent = parent
        lbl = CTkLabel(appFrame, text="Enter the custom command Name")
        lbl.pack()
        self.ent_customCommandName = PopoEntry(appFrame, width=50)
        self.ent_customCommandName.pack()
        lbl = CTkLabel(
            appFrame, text="Enter the custom command to launch")
        lbl.pack()
        self.ent_customCommand = PopoEntry(appFrame, width=50)
        self.ent_customCommand.pack()
        lbl2 = CTkLabel(appFrame, text="Select the parser")
        lbl2.pack()
        apiclient = APIClient.getInstance()
        parsers = apiclient.getPlugins()
        self.box_template = CTkComboBox(
            appFrame, values=tuple([x["plugin"] for x in parsers]), state="readonly")
        self.box_template.set("Default")
        self.box_template.pack()
        lbl3 = CTkLabel(appFrame, text="Select the worker")
        lbl3.pack()
        self.box_workers = CTkComboBox(
            appFrame, values=tuple(workers), state="readonly")
        self.box_workers.set(default_worker)
        self.box_workers.pack()
        self.ok_button = CTkButton(appFrame, text="OK", command=self.onOk)
        self.ok_button.pack(side=tk.BOTTOM, pady=5)
        appFrame.pack(ipady=10, ipadx=10)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.focus_force()
            self.app.grab_set()
            self.app.lift()
        except tk.TclError:
            pass

    def onError(self, event=None):
        self.app.destroy()
        return
    
    def onOk(self):
        """
        Called when the user clicked the validation button. Set the rvalue attributes to the value selected and close the window.
        """
        # send the data to the parent
        self.rvalue = (self.ent_customCommandName.get(), self.ent_customCommand.get(
        ), self.box_template.get(), self.box_workers.get())
        self.app.destroy()
