"""Describe tkinter button with default common args"""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.forms.form import Form


class FormButton(Form):
    """
    Form field representing a button.
    Default setted values: 
        if pack : padx = pady = 5, side = right
        if grid: row = column = 0 sticky = "west
    """

    def __init__(self, name, callback, **kwargs):
        """
        Constructor for a form button

        Args:
            name: the button text.
            callback: a function that will be called when the button is clicked.
            kwargs: same keyword args as you would give to CTkButton
        """
        super().__init__(name)
        self.callback = callback
        self.kwargs = kwargs
        self.btn = None
        self.wid_kwargs = None
        self.infos = {}

    def callback_infos(self, event):
        self.callback(event, self.infos)

    def constructView(self, parent):
        """
        Create the button view inside the parent view given

        Args:
            parent: parent form panel.
        """
        s = self.getKw("style", None)
        text = self.getKw("text", self.name)
        tooltip = self.getKw("tooltip", None)
        if s is None and tooltip is None:
            self.btn = CTkButton(parent.panel, text=text, width=int(self.getKw("width", 150)), height=int(self.getKw("height", 28)), image=self.getKw("image", None),
                                  border_color=self.getKw("border_color", None),
                                  border_width=self.getKw("border_width", None),
                                  text_color=self.getKw("text_color", None),
                                  hover_color=self.getKw("hover_color", None),
                                  fg_color=self.getKw("fg_color", None), font=self.getKw("font", None),
                                  state=self.getKw("state", "normal"))
        else:
            self.btn = ttk.Button(parent.panel, text=text, image=self.getKw("image", None), style=s)
            if tooltip is not None:
                self.btn.configure(tooltip=tooltip)
        self.infos = self.getKw("infos", {})
        if len(self.infos) > 0:
            self.btn.bind('<Button-1>', self.callback_infos)
        else:
            self.btn.bind('<Button-1>', self.callback)
        for bind, bind_call in self.getKw("binds", {}).items():
            self.btn.bind(bind, bind_call)
        
        if parent.gridLayout:
            self.btn.grid(row=self.getKw("row", 0), column=self.getKw("column", 0), sticky=self.getKw("sticky", tk.W), **self.kwargs)
        else:
            self.btn.pack(side=self.getKw("side", "right"), padx=self.getKw("padx", 5), pady=self.getKw("pady", 5), **self.kwargs)
        if self.wid_kwargs is not None:
            self.btn.configure(**self.wid_kwargs)

    def configure(self, **kwargs):
        """Change kwargs to given one. Must be called before constructView
        Args:
            **kwargs: any ttk Button keyword arguments."""
        if self.btn is None:
            self.wid_kwargs = kwargs
        else:
            self.btn.configure(**kwargs)
  

    def setFocus(self):
        """Set the focus to the ttk button.
        """
        self.btn.focus_set()