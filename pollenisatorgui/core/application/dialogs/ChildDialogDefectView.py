"""This class pop a defect view form in a subdialog"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.application.dialogs.ChildDialogView import ChildDialogView
from pollenisatorgui.core.components.apiclient import APIClient
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
    def __init__(self, parent, title, settings, defectModel=None, multi=False, as_template=False, force_insert=False):
        """
        Open a child dialog of a tkinter application to choose autoscan settings.

        Args:
            parent: the tkinter parent view to use for this window construction.
            defectModel : A Defect Model object to load default values. None to have empty fields, default is None.
        """
        super().__init__(parent, title, scrollable=True)
        
        self.isInsert = defectModel is None or force_insert
        self.multi = multi
        self.as_template = as_template
        if self.isInsert:
            defectModel = Defect() if defectModel is None else defectModel
            if self.as_template:
                defectModel.isTemplate = True

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
            if multi:
                self.defect_vw.openMultiModifyWindow(addButtons=False)
                self.completeDialogView(True)
            else:
                self.defect_vw.openModifyWindow(addButtons=True)
                self.completeDialogView(False)
        
    
    def okCallback(self, _event=None):
        """called when pressing the validating button
        Close the window if the form is valid.
        Set rvalue to True and perform the defect update/insert if validated.
        Args:
            _event: Not used but mandatory"""
        msg = None
        if self.isInsert:
            if self.multi:
                res = self.defect_vw.multi_insert()
            else:
                res, msg = self.defect_vw.insert()
        else:
            res, msg = self.defect_vw.update()
        if res:
            self.rvalue = res, msg
            self.app.destroy()

