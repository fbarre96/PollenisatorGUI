"""Ask the user to select a file or directory and then parse it with the selected parser"""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
import tkinterDnD
from pollenisatorgui.core.forms.formpanel import FormPanel
import pollenisatorgui.core.components.utils as utils


class ChildDialogAskFile:
    """
    Open a child dialog of a tkinter application to ask details about
    existing files parsing.
    """

    def __init__(self, parent, info="Choose a file", default_path=""):
        """
        Open a child dialog of a tkinter application to ask details about
        existing files parsing.

        Args:
            default_path: a default path to be added
        """
        self.app = tkinterDnD.Tk()
        utils.setStyle(self.app)
        self.app.title(info)
        self.rvalue = None
        self.default = default_path
        appFrame = CTkFrame(self.app)
        self.form = FormPanel()
        self.form.addFormLabel(
            "Choose one file", info, side=tk.TOP)
        self.fileForm = self.form.addFormFile("File", ".+", '', width=50,
                              side=tk.TOP, mode="file")
        self.button = self.form.addFormButton("Cancel", self.onError, side=tk.RIGHT)
        self.form.addFormButton("OK", self.onOk, side=tk.RIGHT)

        self.form.constructView(appFrame)
        appFrame.pack(ipadx=10, ipady=10)

        try:
            self.app.wait_visibility()
            self.app.focus_force()
            self.app.grab_set()
            self.app.lift()
        except tk.TclError:
            pass
        self.app.mainloop()
        self.app.destroy()

    def onError(self, _event=None):
        self.rvalue = None
        self.app.quit()

    def onOk(self, _event=None):
        """
        Called when the user clicked the validation button.
        launch parsing with selected parser on selected file/directory.
        Close the window.

        Args:
            _event: not used but mandatory
        """
        res, msg = self.form.checkForm()
        if not res:
            tk.messagebox.showwarning(
                "Form not validated", msg, parent=self.app)
            return
        files_paths = self.fileForm.getValue()
        try:
            filepath = files_paths[0]
        except IndexError:
            self.rvalue = None
            tk.messagebox.showwarning(
                "Form not validated", "At least one file is asked", parent=self.app)
            return
        self.rvalue = filepath
        self.app.quit()
        return
