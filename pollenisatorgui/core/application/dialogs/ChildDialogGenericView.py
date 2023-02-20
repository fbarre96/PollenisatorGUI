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
    def __init__(self, parent, title, view):
        """
        Open a child dialog of a tkinter application to choose autoscan settings.

        Args:
            parent: the tkinter parent view to use for this window construction.
            toolView : A Tool view object to display
        """
        super().__init__(parent, title)
        self.view = view
        self.view.appliViewFrame = self.appFrame
        self.view.openModifyWindow()
        self.completeDialogView(False)

   

  