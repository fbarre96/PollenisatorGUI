"""This class pop a defect view form in a subdialog"""

import tkinter as tk
import tkinter.ttk as ttk
from pollenisatorgui.core.Views.DefectView import DefectView
from pollenisatorgui.core.Controllers.DefectController import DefectController
from pollenisatorgui.core.Models.Defect import Defect

class DummyMainApp:
    def __init__(self, settings):
        self.settings = settings

class ChildDialogDefectView:
    """
    Open a child dialog of a tkinter application to answer a question.
    """
    def __init__(self, parent, settings, defectModel=None, multi=False):
        """
        Open a child dialog of a tkinter application to choose autoscan settings.

        Args:
            parent: the tkinter parent view to use for this window construction.
            defectModel : A Defect Model object to load default values. None to have empty fields, default is None.
        """
        self.app = tk.Toplevel(parent)
        self.app.title("Add a security defect")
        self.app.resizable(False, False)
        self.rvalue = None
        appFrame = ttk.Frame(self.app)
        self.isInsert = defectModel is None
        self.multi = multi
        if self.isInsert:
            defectModel = Defect()

        self.defect_vw = DefectView(None, appFrame, DummyMainApp(settings),
                                    DefectController(defectModel))
        if self.isInsert:
            if multi:
                self.defect_vw.openMultiInsertWindow(addButtons=False)
            else:
                self.defect_vw.openInsertWindow(addButtons=False)
        else:
            self.defect_vw.openModifyWindow(addButtons=False)

        ok_button = ttk.Button(appFrame, text="OK")
        ok_button.pack(side="right", padx=5, pady=10)
        ok_button.bind('<Button-1>', self.okCallback)
        cancel_button = ttk.Button(appFrame, text="Cancel")
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
            self.app.destroy()
