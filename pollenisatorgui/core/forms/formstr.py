"""Describe tkinter Entry with default common args"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.forms.form import Form
import pyperclip
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.pollenisatorentry import PopoEntry

class FormStr(Form):
    """
    Form field representing a string input.
    Default setted values:
        width=20
        if pack : padx = pady = 5, side = left
        if grid: row = column = 0 sticky = "East"
    """

    def __init__(self, name, regexValidation="", default="", contextualMenu=None, **kwargs):
        """
        Constructor for a form entry

        Args:
            name: the entry name (id).
            regexValidation: a regex used to check the input in the checkForm function., default is ""
            default: a default value for the Entry, defauult is ""
            contextualMenu: (Opt.) a contextualMenu to open when right clicked. default is None
            kwargs: same keyword args as you would give to PopoEntry
                    + binds:  a dictionnary of tkinter binding with shortcut as key and callback as value
        """
        super().__init__(name)
        self.regexValidation = regexValidation
        self.default = default
        self.contextualMenu = contextualMenu
        self.kwargs = kwargs
        self.widgetMenuOpen = None
        self.entry = None

    def _initContextualMenu(self, parent):
        """Initialize the contextual menu for paperclip.
        Args:
            parent: the tkinter parent widget for the contextual menu
        """
        # FIXME Add to given menu instead of Overriding given contextual menu
        self.contextualMenu = utils.craftMenuWithStyle(parent)
        self.contextualMenu.add_command(
            label="Copy", command=self.copy)
        self.contextualMenu.add_command(
            label="Cut", command=self.cut)
        self.contextualMenu.add_command(
            label="Paste", command=self.paste)
        self.contextualMenu.add_command(
            label="Close", command=self.close)

    def close(self):
        """Option of the contextual menu : Close the contextual menu by doing nothing
        """
        pass

    def copy(self):
        """Option of the contextual menu : Copy entry text to clipboard
        """
        pyperclip.copy(self.entry.selection_get())

    def cut(self):
        """Option of the contextual menu : Cut entry text to clipboard
        """
        sel = self.entry.selection_get()
        if sel:
            pyperclip.copy(sel)
            self.entry.delete(tk.SEL_FIRST, tk.SEL_LAST)

    def paste(self, event=None):
        """Option of the contextual menu : Paste clipboard content to entry
        """
        if event is None:
            buff = pyperclip.paste()
        else:
            buff = event.widget.clipboard_get()
        if buff:
            try:
                self.entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
            insert_index = self.entry.index(tk.INSERT)
            self.entry.insert(insert_index, buff)
        return "break"

    def popup(self, event):
        """
        Fill the self.widgetMenuOpen and reraise the event in the editing window contextual menu

        Args:
            event: a ttk Treeview event autofilled. Contains information on what treeview node was clicked.
        """
        self.widgetMenuOpen = event.widget
        self.contextualMenu.tk_popup(event.x_root, event.y_root)
        self.contextualMenu.focus_set()
        self.contextualMenu.bind('<FocusOut>', self.popupFocusOut)

    def popupFocusOut(self, _event=None):
        """Callback for focus out event. Destroy contextual menu
        Args:
            _event: not used but mandatory
        """
        self.contextualMenu.unpost()

    def constructView(self, parent):
        """
        Create the string view inside the parent view given

        Args:
            parent: parent FormPanel.
        """
        self.entry = PopoEntry(parent.panel, placeholder_text=self.getKw("placeholder", self.getKw("placeholder_text", None)), width=self.getKw(
            "width", 200), state=self.getKw("state", "normal"), show=self.getKw("show", None))
        self._initContextualMenu(self.entry)
        self.entry.bind("<<Paste>>", self.paste)
        for bind, bind_call in self.getKw("binds", {}).items():
            self.entry.bind(bind, bind_call)
        if self.default != "" and self.default is not None:
            self.setValue(self.default)
            

        if parent.gridLayout:
            self.entry.grid(row=self.getKw("row", 0), column=self.getKw(
                "column", 0), sticky=self.getKw("sticky", tk.W))
        else:
            self.entry.pack(side=self.getKw("side", "left"), padx=self.getKw(
                "padx", 10), pady=self.getKw("pady", 5), expand=self.getKw("expand", True), fill=self.getKw("fill", "x"))

 

    def getValue(self):
        """
        Return the form value. Required for a form.

        Returns:
            Return the entry value as string.
        """
        return self.entry.get()
    
    def setValue(self, newval):
        """
        Set the text value.
        Args:
            newval: the new value to be set inside the text
        """
        state = self.entry.cget("state")
        self.entry.configure(state="normal")
        self.entry.delete("0", "end")
        self.entry.insert("0", newval)
        self.entry.configure(state=state)

    def checkForm(self):
        """
        Check if this form is correctly filled. Check with the regex validation given in constructor.

        Returns:
            {
                "correct": True if the form is correctly filled, False otherwise.
                "msg": A message indicating what is not correctly filled.
            }
        """
        import re
        if re.match(self.regexValidation, self.getValue()) is not None:
            return True, ""
        return False, self.kwargs.get("error_msg", self.name+" value is incorrect. \n "+self.getValue()+"does not match regex "+str(self.regexValidation))

    def setFocus(self):
        """Set the focus to the ttk entry widget.
        """
        self.entry.focus_set()
