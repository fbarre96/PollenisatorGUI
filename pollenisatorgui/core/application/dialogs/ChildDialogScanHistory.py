"""This class pop a dialog to view scan history"""

from datetime import datetime
import tkinter as tk
from customtkinter import *
from pollenisatorgui.core.application.scrollableframexplateform import ScrollableFrameXPlateform
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.application.scrollabletreeview import ScrollableTreeview
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.forms.formpanel import FormPanel
from pollenisatorgui.core.models.checkinstance import CheckInstance
from pollenisatorgui.core.models.tool import Tool
from pollenisatorgui.core.controllers.toolcontroller import ToolController 
from pollenisatorgui.core.views.toolview import ToolView
from pollenisatorgui.core.application.dialogs.ChildDialogToolView import ChildDialogToolView
from bson.objectid import ObjectId

class ChildDialogScanHistory:
    """
    Open a child dialog of a tkinter application
    """
    def __init__(self, parent):
        """
        Open a child dialog of a tkinter application to choose autoscan checks.

        Args:
            parent: the tkinter parent view to use for this window construction.
        """
        self.app = CTkToplevel(parent)
        self.app.attributes("-type", "dialog")
        #self.app.geometry("800x650")
        self.app.title("Scan history")
        self.app.resizable(True, True)
        self.app.bind("<Escape>", self.cancel)
        self.rvalue = None
        appFrame = CTkFrame(self.app)
        self.parent = parent
        self.initUI(appFrame)
        frame_buttons = CTkFrame(self.app)
        ok_button = CTkButton(frame_buttons, text="OK")
        ok_button.pack(side=tk.RIGHT, padx=5)
        ok_button.bind('<Button-1>', self.okCallback)
        cancel_button = CTkButton(frame_buttons, text="Cancel", 
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
        cancel_button.pack(side=tk.RIGHT, padx=5)
        cancel_button.bind('<Button-1>', self.cancel)
        frame_buttons.pack(side=tk.BOTTOM, anchor=tk.SE , padx=5 , pady=5)
        appFrame.pack(fill=tk.BOTH, pady=10, padx=10, expand="yes")

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
        self.rvalue = None
        self.app.destroy()

    def okCallback(self, _event=None):
        """called when pressing the validating button
        Close the window if the form is valid.
        Set rvalue to True and perform the defect update/insert if validated.
        Args:
            _event: Not used but mandatory"""
        
        self.rvalue = []
        self.app.destroy()

    def OnDoubleClick(self, event):
        """
        Callback for double click on treeview.
        Opens a window to update the double clicked tool view.
        Args:
            event: automatically created with the event catch. stores data about line in treeview that was double clicked.
        """
        item = self.histoScanTv.identify("item", event.x, event.y)
        if item is None or item == '':
            return
        datamanager = DataManager.getInstance()
        tool = datamanager.get("tool", str(item))
        if tool is None:
            return
        
        dialog = ChildDialogToolView(self.app, "Tool view", ToolView(None, None, None, ToolController(tool)))
            
        
    def filter(self, event=None):
        category = self.str_filter_category.getValue()
        name = self.str_filter_name.getValue()
        startd = self.date_filter_startd.getValue()
        endd = self.date_filter_endd.getValue()
        self.histoScanTv.filter(category, name, (ScrollableTreeview.date_compare, startd, endd))

    def initUI(self, frame):
        form = FormPanel(side=tk.TOP, fill=tk.X, pady=5, grid=True)
        form.addFormLabel("Category")
        self.str_filter_category = form.addFormStr("Category", placeholder_text="category", column=1, binds={"<Key-Return>":  self.filter})
        form.addFormLabel("Name", column=2)
        self.str_filter_name = form.addFormStr("Name", placeholder_text="name", column=3, binds={"<Key-Return>":  self.filter})
        form.addFormLabel("Start date", column=4)
        start = datetime.today()
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        self.date_filter_startd = form.addFormDate("Start Date", self.app, default=utils.dateToString(start), column=5, binds={"<Key-Return>":  self.filter})
        form.addFormLabel("End date", column=6)
        self.date_filter_endd = form.addFormDate("End Date", self.app, default=utils.dateToString(datetime.now()), column=7, binds={"<Key-Return>":  self.filter})
        form.constructView(frame)

        self.histoScanTv = ScrollableTreeview(frame, ('History category', 'Name', 'Ended at'), height=25, sort_keys=(None, None, utils.stringToDate))
        self.histoScanTv.pack(fill=tk.BOTH, expand="yes", padx=10, pady=10)
        self.histoScanTv.bind("<Double-Button-1>", self.OnDoubleClick)
        self.refreshUI()

    
    def refreshUI(self):
        done_scans = list(Tool.fetchObjects({"status":"done"}))
        checks = CheckInstance.fetchObjects([ObjectId(done_scan.check_iid) for done_scan in done_scans if done_scan.check_iid != ""])
        self.mapping = {}
        for check in checks:
            self.mapping[str(check._id)] = check
        self.histoScanTv.reset()
        for done_scan in done_scans:
            check = self.mapping.get(str(done_scan.check_iid), None)
            group_name = "" if check is None else check.check_m.title
            try:
                self.histoScanTv.insert('',"end", str(done_scan.getId()), text=group_name, values=(done_scan.name, done_scan.datef))
            except tk.TclError as e:
                print(e)
        
