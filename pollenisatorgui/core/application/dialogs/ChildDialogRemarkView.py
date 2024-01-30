"""This class pop a remark view form in a subdialog"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.views.remarkview import RemarkView
from pollenisatorgui.core.controllers.remarkcontroller import RemarkController
from pollenisatorgui.core.models.remark import Remark
import pollenisatorgui.core.components.utils as utils

class ChildDialogRemarkView:
    """
    Open a child dialog of a tkinter application to answer a question.
    """
    def __init__(self, parent, remarkModel=None):
        """

        Args:
            parent: the tkinter parent view to use for this window construction.
            remarkModel : A Remark Model object to load default values. None to have empty fields, default is None.
        """
        self.app = CTkToplevel(parent)
        self.app.attributes("-type", "dialog")
        self.isInsert = remarkModel is None
        if self.isInsert:
            remarkModel = Remark()
        title = "Add a remark" if self.isInsert else "Edit remark"
        self.app.title(title)
        self.app.resizable(False, False)
        self.rvalue = None
        appFrame = CTkFrame(self.app)
        self.app.bind("<Escape>", self.cancel)
        
        self.remark_vw = RemarkView(appFrame, RemarkController(remarkModel))
        if self.isInsert:
            self.remark_vw.openInsertWindow(addButtons=False)
        else:
            self.remark_vw.openModifyWindow(addButtons=False)
        ok_button = CTkButton(appFrame, text="OK")
        ok_button.pack(side="right", padx=5, pady=10)
        ok_button.bind('<Button-1>', self.okCallback)
        cancel_button = CTkButton(appFrame, text="Cancel", 
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
        cancel_button.pack(side="right", padx=5, pady=10)
        cancel_button.bind('<Button-1>', self.cancel)
        appFrame.pack(fill=tk.BOTH, ipady=10, ipadx=10)
        self.app.transient(parent)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
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
        Set rvalue to True and perform the remark update/insert if validated.
        Args:
            _event: Not used but mandatory"""
        
        if self.isInsert:
            res, _ = self.remark_vw.insert()
        else:
            res, _ = self.remark_vw.update()
        if res:
            self.rvalue = True
            self.app.destroy()
