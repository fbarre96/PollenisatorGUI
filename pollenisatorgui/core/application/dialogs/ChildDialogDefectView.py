"""This class pop a defect view form in a subdialog"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.application.dialogs.ChildDialogView import ChildDialogView
from pollenisatorgui.core.views.defectview import DefectView
from pollenisatorgui.core.controllers.defectcontroller import DefectController
from pollenisatorgui.core.models.defect import Defect

class DummyMainApp:
    def __init__(self, settings):
        self.settings = settings

class ChildDialogDefectView(ChildDialogView):
    """
    Open a child dialog of a tkinter application to answer a question.
    """
    def __init__(self, parent, title, settings, defectModel=None, multi=False):
        """
        Open a child dialog of a tkinter application to choose autoscan settings.

        Args:
            parent: the tkinter parent view to use for this window construction.
            defectModel : A Defect Model object to load default values. None to have empty fields, default is None.
        """
        super().__init__(parent, title)
        self.isInsert = defectModel is None
        self.multi = multi
        if self.isInsert:
            defectModel = Defect()

        self.defect_vw = DefectView(None, self.appFrame, parent,
                                    DefectController(defectModel))
        if self.isInsert:
            if multi:
                self.defect_vw.openMultiInsertWindow(addButtons=False)
                self.completeDialogView(True)
            else:
                self.defect_vw.openInsertWindow(addButtons=True)
                self.completeDialogView(False)
        else:
            self.defect_vw.openModifyWindow(addButtons=True)
            self.completeDialogView(False)

    
    def okCallback(self, _event=None):
        """called when pressing the validating button
        Close the window if the form is valid.
        Set rvalue to True and perform the defect update/insert if validated.
        Args:
            _event: Not used but mandatory"""
        
        if self.isInsert:
            if self.multi:
                res = self.defect_vw.multi_insert()
            else:
                res, _ = self.defect_vw.insert()
        else:
            res, _ = self.defect_vw.update()
        if res:
            self.rvalue = True
            self.unboundToMousewheel()
            self.app.destroy()

