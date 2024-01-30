"""Ask the user to select a file or directory and then parse it with the selected parser"""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
import pollenisatorgui.core.components.utils as utils


class ChildDialogAskText:
    """
    Open a child dialog of a tkinter application to ask a text area.
    """

    def __init__(self, parent, info="Input text", default='' , multiline=True, **kwargs):
        """
        Open a child dialog of a tkinter application to ask details about
        existing files parsing.

        Args:
            default_path: a default path to be added
        """
        from pollenisatorgui.core.forms.formpanel import FormPanel
        self.app = CTkToplevel(parent, fg_color=utils.getBackgroundColor())
        self.app.attributes("-type", "dialog")
        fullscreen = False
        if kwargs.get("fullscreen", False):
            fullscreen = True
            monitor = utils.get_screen_where_widget(parent)
            self.app.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
            del kwargs["fullscreen"]
        self.app.title(info)
        self.rvalue = None
        is_markdown = False
        if "markdown" in kwargs:
            is_markdown = kwargs.get("markdown", True)
            del kwargs["markdown"]
        self.save_on_close = False
        if "save_on_close" in kwargs:
            self.save_on_close = kwargs.get("save_on_close", True)
            del kwargs["save_on_close"]
        self.save_on_close = kwargs.get("save_on_close", True)
        appFrame = CTkFrame(self.app)
        self.form = FormPanel(fill=tk.BOTH, expand=1)
        if not is_markdown:
            self.form.addFormLabel(
                "Input text", text=info, side=tk.TOP)
        if multiline or is_markdown:
            if is_markdown:
                self.formText = self.form.addFormMarkdown(info, "", default,
                                side=tk.TOP, fill=tk.BOTH, expand=1, just_editor=True, allow_maximize=not fullscreen, **kwargs)
            else:
                self.formText = self.form.addFormText(info, "", default,
                                side=tk.TOP, fill=tk.BOTH, expand=1,**kwargs)
        else:
            show = "*" if kwargs.get("secret") else None
            self.formText = self.form.addFormStr(info, "", default, side=tk.TOP, show=show, **kwargs)
        btn = self.form.addFormButton("OK", self.onOk, side=tk.RIGHT)
        self.button = self.form.addFormButton("Cancel", self.onError, side=tk.RIGHT, 
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")

        self.form.constructView(appFrame)
        if not (multiline or is_markdown):
            self.app.bind("<Return>", self.onOk)
        self.app.bind("<Escape>", self.onClose)
        appFrame.pack(ipadx=10, ipady=10, fill=tk.BOTH, expand=1)

        try:
            self.app.wait_visibility()
            self.app.focus_force()
            self.app.grab_set()
            self.app.lift()
        except tk.TclError:
            pass
        self.formText.setFocus()

    def onClose(self, _event=None):
        if self.save_on_close:
            self.onOk()
        else:
            self.onError()

    def onError(self, _event=None):
        self.rvalue = None
        self.app.destroy()

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
        text = self.formText.getValue()
        self.rvalue = text
        self.app.destroy()
