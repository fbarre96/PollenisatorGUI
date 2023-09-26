"""Describe tkinter combobox with default common args"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.forms.form import Form


class FormCombo(Form):
    """
    Form field representing a combobox.
    Default setted values: 
        state="readonly"
        if pack : padx = pady = 5, side = "right"
        if grid: row = column = 0 sticky = "west"
    Additional values to kwargs:
        binds:  a dictionnary of tkinter binding with shortcut as key and callback as value
    """

    def __init__(self, name, choicesList, default, **kwargs):
        """
        Constructor for a form checkbox

        Args:
            name: the checklist name (id).
            choicesList: a list of string forming all the possible choices.
            default: a list of string that should be prechecked if in the choice list.
            kwargs: same keyword args as you would give to CTkComboBox
        """
        super().__init__(name)
        self.choicesList = choicesList
        self.default = default
        self.kwargs = kwargs
        self.box = None
        self.wid_kwargs = None

    

    def constructView(self, parent):
        """
        Create the combobox view inside the parent view given

        Args:
            parent: parent FormPanel.
        """
        kw = {}
        width = self.getKw("width", None)
        if width is not None:
            kw["width"] = int(width)
        self.box = CTkComboBox(parent.panel, values=tuple(
            self.choicesList), state=self.getKw("state", "normal"), command=self.getKw("command",None), **kw)
        if self.default is not None:
            self.box.set(self.default)
        binds = self.getKw("binds", {})
        self.box.bind('<KeyRelease>', self.check_input)
        for bind in binds:
            self.box.bind(bind, binds[bind])
        if parent.gridLayout:
            self.box.grid(row=self.getKw("row", 0), column=self.getKw(
                "column", 0), sticky=self.getKw("sticky", tk.W))
        else:
            self.box.pack(side=self.getKw("side", "right"), padx=self.getKw(
                "padx", 10), pady=self.getKw("pady", 5), anchor=self.getKw("anchor", None))
        if self.wid_kwargs is not None:
            self.box.configure(**self.wid_kwargs)

    def getValue(self):
        """
        Return the form value. Required for a form.

        Returns:
            Return the selected text inside the comboxbox.
        """
        v = self.box.get()
        if v == "<Empty>":
            return ""
        return v

    def get(self):
        """alias of getValue"""
        return self.getValue()
    
    def setValue(self, newval):
        """
        Set the combo value.
        Args:
            newval: the new value to be set inside the combobox
        """
        if isinstance(newval, list):
            #self.choicesList = newval
            if newval:
                self.box.set(newval[0])
        elif newval not in self.choicesList:
            self.choicesList.append(newval)
        self.box.set(newval)
        command = self.box.cget("command")
        if command is not None:
            command()

    def set(self, newval):
        # alias for setValue
        return self.setValue(newval)

    def checkForm(self):
        """
        Check if this form is correctly filled. Formal verification if the selected value is still on the choice list.

        Returns:
            {
                "correct": True if the form is correctly filled, False otherwise.
                "msg": A message indicating what is not correctly filled.
            }
        """
        if "<Empty>" in self.choicesList and self.getValue() == "":
            return True, ""
        if self.getValue() not in self.choicesList:
            return False, self.name+" values ("+str(self.getValue())+") not in the accepted list."
        return True, ""

    def setFocus(self):
        """Set the focus to the ttk combobox.
        """
        self.box.focus_set()

    def configure(self, **kwargs):
        if "values" in kwargs:
            self.box.configure(values=kwargs["values"])
            self.choicesList = kwargs["values"]
            del kwargs["values"]
        self.wid_kwargs = kwargs

    def winfo_reqwidth(self):
        return self.box.winfo_reqwidth()
    
    def winfo_reqheight(self):
        return self.box.winfo_reqheight()
    
    def winfo_rootx(self):
        return self.box.winfo_rootx()
    
    def winfo_rooty(self):
        return self.box.winfo_rooty()
    
    def check_input(self, event):
        if event is not None:
            if event.keysym != "BackSpace" and event.keysym != "Delete" and (len(event.keysym) > 1 or not event.keysym.isalnum()):
                return
        value = event.widget.get()
        if value == '':
            self.box['values'] = self.choicesList
        else:
            data = []
            for item in self.choicesList:
                if isinstance(value, str):
                    if value.lower() in item.lower():
                        data.append(item)

            self.box['values'] = data
            if len(data) == 1:
                self.setValue(data)
                self.box.event_generate("<Down>")
