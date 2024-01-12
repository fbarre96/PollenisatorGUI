"""This class pop a tool view form in a subdialog"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.application.dialogs.ChildDialogView import ChildDialogView

class DummyMainApp:
    def __init__(self, settings):
        self.settings = settings

class ChildDialogGenericView(ChildDialogView):
    """
    Open a child dialog of a tkinter application to answer a question.
    """
    def __init__(self, parent, title, view, is_insert=False):
        """
        Open a child dialog of a tkinter application to choose autoscan settings.

        Args:
            parent: the tkinter parent view to use for this window construction.
            title: title of the window
            view : A view object to display
            is_insert(False) : open in insert mode
        """
        super().__init__(parent, title)
        self.view = view
        self.view.appliViewFrame = self.appFrame
        self.viewdelete = self.view.delete
        self.viewinsert = self.view.insert
        self.view.delete = self.deleteProxy
        self.view.insert = self.insertProxy
        if is_insert:
            self.view.openInsertWindow()
        else:
            self.view.openModifyWindow()
        self.completeDialogView(addButtons=False)

    def deleteProxy(self, *args, **kwargs):
        self.viewdelete(*args, **kwargs)
        self.app.destroy()
   
    def insertProxy(self, *args, **kwargs):
        res = self.viewinsert(*args, **kwargs)
        self.rvalue = res
        self.app.destroy()

  