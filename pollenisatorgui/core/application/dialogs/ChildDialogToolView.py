"""This class pop a tool view form in a subdialog"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.application.dialogs.ChildDialogView import ChildDialogView

class DummyMainApp:
    def __init__(self, settings):
        self.settings = settings

class ChildDialogToolView(ChildDialogView):
    """
    Open a child dialog of a tkinter application to answer a question.
    """
    def __init__(self, parent, title, toolView):
        """
        Open a child dialog of a tkinter application to choose autoscan settings.

        Args:
            parent: the tkinter parent view to use for this window construction.
            toolView : A Tool view object to display
        """
        super().__init__(parent, title)
        self.tool_vw = toolView
        self.tool_vw.appliViewFrame = self.appFrame
        self.tool_vw.openModifyWindow()
        self.completeDialogView(addButtons=False)

   

  