"""Ask the user to select a file or directory and then parse it with the selected parser"""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
import tkinterdnd2
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.forms.formpanel import FormPanel
import pollenisatorgui.core.components.utilsUI as utilsUI


class ChildDialogAskFile(CTk, tkinterdnd2.TkinterDnD.DnDWrapper):
    """
    Open a child dialog of a tkinter application to ask details about
    existing files parsing.
    """
    def _init_tkdnd(master: tk.Tk) -> None: #HACK to make work tkdnd with CTk
        """Add the tkdnd package to the auto_path, and import it"""
        return tkinterdnd2.TkinterDnD._require(master)


    def __init__(self, parent, info="Choose a file", default_path=""):
        """
        Open a child dialog of a tkinter application to ask details about
        existing files parsing.

        Args:
            default_path: a default path to be added
        """
        super().__init__()
        self.TkDnDVersion = self._init_tkdnd()  #HACK to make work tkdnd with CTk
        self.settings = Settings()
        utilsUI.setStyle(self, self.settings.local_settings.get("dark_mode", False))
        self.title(info)
        self.bind("<Escape>", self.onError)
        self.rvalue = None
        self.default = default_path
        appFrame = CTkFrame(self)
        self.form = FormPanel()
        self.form.addFormLabel(
            "Choose one file", info, side=tk.TOP)
        self.fileForm = self.form.addFormFile("File", ".+", '', width=50,
                              side=tk.TOP, mode="file")
        self.button = self.form.addFormButton("Cancel", self.onError, side=tk.RIGHT, 
                               fg_color=utilsUI.getBackgroundColor(), text_color=utilsUI.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
        self.form.addFormButton("OK", self.onOk, side=tk.RIGHT)

        self.form.constructView(appFrame)
        appFrame.pack(ipadx=10, ipady=10)

        try:
            self.wait_visibility()
            self.focus_force()
            self.grab_set()
            self.lift()
        except tk.TclError:
            pass
        self.mainloop()
    def quit(self):
        super().quit()
        self.destroy()

    def onError(self, _event=None):
        self.rvalue = None
        self.quit()

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
                "Form not validated", msg, parent=self)
            return
        files_paths = self.fileForm.getValue()
        try:
            filepath = files_paths[0]
        except IndexError:
            self.rvalue = None
            tk.messagebox.showwarning(
                "Form not validated", "At least one file is asked", parent=self)
            return
        self.rvalue = filepath
        self.quit()
        return
