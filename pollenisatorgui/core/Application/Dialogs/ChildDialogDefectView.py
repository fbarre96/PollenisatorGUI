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
        if defectModel is not None:
            if defectModel.isTemplate:
                self.app.title("Edit a security defect template")
            else:
                self.app.title("Edit a security defect")
        else:
            self.app.title("Add a security defect")
        self.app.resizable(True, True)
        self.app.geometry("800x600")
        container = ttk.Frame(self.app)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        self.rvalue = None
        self.canvas = tk.Canvas(container, bg="white")
        self.appFrame = ttk.Frame(self.canvas)
        self.myscrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.bind('<Enter>', self.boundToMousewheel)
        self.canvas.bind('<Leave>', self.unboundToMousewheel)
        self.canvas.bind('<Configure>',  lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        ))
        self.canvas_main_frame = self.canvas.create_window((0, 0), window=self.appFrame, anchor='nw')
        self.canvas.configure(yscrollcommand=self.myscrollbar.set)  
        
        
        self.isInsert = defectModel is None
        self.multi = multi
        if self.isInsert:
            defectModel = Defect()

        self.defect_vw = DefectView(None, self.appFrame, parent,
                                    DefectController(defectModel))
        if self.isInsert:
            if multi:
                self.defect_vw.openMultiInsertWindow(addButtons=False)
            else:
                self.defect_vw.openInsertWindow(addButtons=False)
        else:
            self.defect_vw.openModifyWindow(addButtons=False)

        ok_button = ttk.Button(self.appFrame, text="OK")
        ok_button.pack(side="right", padx=5, pady=10)
        ok_button.bind('<Button-1>', self.okCallback)
        cancel_button = ttk.Button(self.appFrame, text="Cancel")
        cancel_button.pack(side="right", padx=5, pady=10, ipadx=10)
        cancel_button.bind('<Button-1>', self.cancel)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.bind("<Configure>", self.resizeAppFrame)
        self.canvas.grid(column=0, row=0, sticky="nsew")
        self.myscrollbar.grid(column=1, row=0, sticky="ns")
        container.pack(fill=tk.BOTH, ipady=10, ipadx=10, expand=True)

        # self.appFrame.pack(fill=tk.X, ipady=10, ipadx=10, expand=True) this break the canvas drawing with scrollbar
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.grab_set()
            self.app.focus_force()
            self.app.lift()
        except tk.TclError:
            pass

    def resizeAppFrame(self, event):
        self.canvas.itemconfig(self.canvas_main_frame, height=self.appFrame.winfo_height(), width=event.width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def boundToMousewheel(self, _event=None):
        """Called when the **command canvas** is on focus.
        Bind the command scrollbar button on linux to the command canvas
        Args:
            _event: not used but mandatory
        """
        if self.canvas is None:
            return
        self.canvas.bind_all("<Button-4>", self._onMousewheel)
        self.canvas.bind_all("<Button-5>", self._onMousewheel)

    def unboundToMousewheel(self, _event=None):
        """Called when the **command canvas** is unfocused.
        Unbind the command scrollbar button on linux to the command canvas
        Args:
            _event: not used but mandatory"""
        if self.canvas is None:
            return
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def cancel(self, _event=None):
        """called when canceling the window.
        Close the window and set rvalue to False
        Args:
            _event: Not used but mandatory"""
        self.rvalue = False
        self.unboundToMousewheel()
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
            self.unboundToMousewheel()
            self.app.destroy()

    def _onMousewheel(self, event):
        """Scroll the settings canvas
        Args:
            event: scroll info filled when scroll event is triggered"""
        if event.num == 5 or event.delta == -120:
            count = 1
        if event.num == 4 or event.delta == 120:
            count = -1
        self.canvas.yview_scroll(count, "units")