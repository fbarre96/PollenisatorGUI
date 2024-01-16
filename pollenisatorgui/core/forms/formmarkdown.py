"""Describe tkinter Text with default common args and an attached scrollbar"""

import tkinter as tk
from customtkinter import *
from pollenisatorgui.core.application.mdframe import TkintermdFrame
from tkinter.constants import *
from pollenisatorgui.core.forms.form import Form
import pollenisatorgui.core.components.utils as utils


class FormMarkdown(Form):
    """
    Form field representing a multi-lined input.
    Default setted values:
        width=20, height=20
        if pack : padx = pady = 5, side = left
        if grid: row = column = 0 sticky = "East"
    """

    def __init__(self, name, validation="", default="", contextualMenu=None, **kwargs):
        """
        Constructor for a form text

        Args:
            name: the entry name (id).
            validation: a regex used to check the input
                             in the checkForm function. default is "" or a callback function
            default: a default value for the Entry, default is ""
            contextualMenu: (Opt.) a contextualMenu to open when right clicked. default is None
            kwargs: same keyword args as you would give to ttk.Text
        """
        super().__init__(name)
        self.validation = validation
        self.default = default
        self.contextualMenu = contextualMenu
        self.kwargs = kwargs
        self.text = None
        self.widgetMenuOpen = None
        self.just_editor = self.getKw("just_editor", False)
        self.enable_preview = self.getKw("enable_preview", True)
        self.style_change = self.getKw("style_change", False)
        self.allow_maximize = self.getKw("allow_maximize", True)

    def close(self):
        """Option of the contextual menu : Close the contextual menu by doing nothing
        """
        pass

    def sanitize(self, string):
        """remove unwanted things in text"""
        return string.replace("\r","")

    def constructView(self, parent):
        """
        Create the text view inside the parent view given

        Args:
            parent: parent FormPanel.
        """
        state = self.getKw("state", "normal")
        dark_mode = self.getKw("dark_mode", False)
        self.mdFrame = TkintermdFrame(parent.panel, default_text=self.default, just_editor=self.just_editor, style_change=self.style_change,
                                       enable_preview=self.enable_preview, height=self.getKw("height", 0), binds=self.getKw("binds", {}),
                                       enable_maximize=self.allow_maximize)
        from pollenisatorgui.core.components.settings import Settings
        s = Settings()
        if dark_mode:
            editor_style = s.local_settings.get("editor_dark_theme", "material")
        else:
            editor_style = s.local_settings.get("editor_light_style","stata-light")
        self.mdFrame.load_style(editor_style)
        if state == "disabled":
            self.mdFrame.text_area.configure(state="disabled")
        if parent.gridLayout:
            self.mdFrame.grid(row=self.getKw("row", 0), column=self.getKw(
                "column", 0), sticky=self.getKw("sticky", tk.EW), **self.kwargs)
        else:
            self.mdFrame.pack(side=self.getKw("side", "left"), padx=self.getKw(
                "padx", 10), pady=self.getKw("pady", 5), expand=self.getKw("expand", True), fill=self.getKw("fill", tk.NONE), **self.kwargs)

    
    def getValue(self):
        """
        Return the form value. Required for a form.

        Returns:
            Return the entry value as string.
        """
        return self.mdFrame.text_area.get('1.0', 'end-1c')

    def setValue(self, newval):
        """
        Set the text value.
        Args:
            newval: the new value to be set inside the text
        """
        state = self.mdFrame.text_area.cget("state")
        self.mdFrame.text_area.configure(state="normal")
        self.mdFrame.text_area.delete("1.0", "end")
        self.mdFrame.text_area.insert("1.0", self.sanitize(newval))
        self.mdFrame.text_area.configure(state=state)

    def checkForm(self):
        """
        Check if this form is correctly filled.
        Check with the validation given in constructor.

        Returns:
            {
                "correct": True if the form is correctly filled, False otherwise.
                "msg": A message indicating what is not correctly filled.
            }
        """
        if isinstance(self.validation, str):
            import re
            if re.match(self.validation, self.getValue(), re.MULTILINE) is None:
                return False, self.name+" value is incorrect."
            return True, ""
        elif callable(self.validation):
            return self.validation(self.getValue()), self.name+" value is incorrect."


    def setFocus(self):
        """Set the focus to the ttk entry widget.
        """
        self.mdFrame.text_area.focus_set()
