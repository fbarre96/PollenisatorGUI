"""Help the user to create a setup an autoscan.
"""
import tkinter as tk
from tkinter import ttk
from customtkinter import *
from pollenisatorgui.core.application.checkboxscrollabletreeview import CheckboxScrollableTreeview
from pollenisatorgui.core.application.scrollabletreeview import ScrollableTreeview
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.settings import Settings
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.forms.formpanel import FormPanel
from pollenisatorgui.core.models.checkitem import CheckItem
from pollenisatorgui.core.models.command import Command
from pollenisatorgui.core.components.logger_config import logger


class ChildDialogAutoScanParams(CTkToplevel):
    """
    Open a child dialog of a tkinter application to ask details about
    a new pentest database to create.
    """

    def __init__(self, parent):
        """
        Open a child dialog of a tkinter application to choose autoscan checks.

        Args:
            parent: the tkinter parent view to use for this window construction.
        """
        super().__init__(parent)
        self.attributes("-type", "dialog")
        self.title("AutoScan configuration")
        self.resizable(True, True)
        self.bind("<Escape>", self.cancel)
        self.rvalue = None
        appFrame = CTkFrame(self)
        self.parent = parent
        self.initUI(appFrame)
        frame_buttons = CTkFrame(self)
        ok_button = CTkButton(frame_buttons, text="OK")
        ok_button.pack(side=tk.RIGHT, padx=5)
        ok_button.bind('<Button-1>', self.okCallback)
        cancel_button = CTkButton(frame_buttons, text="Cancel", 
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
        cancel_button.pack(side=tk.RIGHT, padx=5)
        cancel_button.bind('<Button-1>', self.cancel)
        frame_buttons.pack(side=tk.BOTTOM, anchor=tk.SE , padx=5 , pady=5)
        appFrame.pack(fill=tk.BOTH, ipady=10, ipadx=10, expand="yes")

        self.transient(parent)
        try:
            self.wait_visibility()
            self.transient(parent)
            self.grab_set()
            self.focus_force()
            self.lift()
        except tk.TclError:
            pass

    def cancel(self, _event=None):
        """called when canceling the window.
        Close the window and set rvalue to False
        Args:
            _event: Not used but mandatory"""
        self.rvalue = None
        self.destroy()

    def okCallback(self, _event=None):
        """called when pressing the validating button
        Close the window if the form is valid.
        Set rvalue to True and perform the defect update/insert if validated.
        Args:
            _event: Not used but mandatory"""
        
        self.rvalue = {}
        self.rvalue["commands"] = self.autoScanTv.get_checked_children()
        self.rvalue["autoqueue"] = self.switch_auto_queue.get()
        self.destroy()


    def filter(self, event=None):
        category = self.str_filter_category.getValue()
        title = self.str_filter_category_title.getValue()
        prio = self.str_filter_priority.getValue()
        command = self.str_filter_command.getValue()
        self.autoScanTv.filter(command, category, title, (lambda prio, toCompare: int(toCompare)<=int(prio) if prio != "" else True, prio), check_case=False)

    def initUI(self, frame):
        form = FormPanel(side=tk.TOP, fill=tk.X, pady=5, grid=True)
        column = 0
        form.addFormLabel("Command name", column=(column := column + 1))
        self.str_filter_command = form.addFormStr("Command", placeholder_text="Nmap", column=(column := column + 1), binds={"<Key-Return>":  self.filter})
        form.addFormLabel("Category", column=(column := column + 1))
        self.str_filter_category = form.addFormStr("Category", placeholder_text="recon", column=(column := column + 1), binds={"<Key-Return>":  self.filter})
        form.addFormLabel("Category title", column=(column := column + 1))
        self.str_filter_category_title = form.addFormStr("CategoryTitle", placeholder_text="title", column=(column := column + 1), binds={"<Key-Return>":  self.filter})
        form.addFormLabel("Priority", column=(column := column + 1))
        self.str_filter_priority = form.addFormStr("Priority", placeholder_text="0", column=(column := column + 1), binds={"<Key-Return>":  self.filter})
        form.constructView(frame)
        self.check_box_all = CTkCheckBox(frame, text="All", command=self.check_all)
        self.check_box_all.pack(padx=10,pady=10,side=tk.TOP)
        tvFrame = CTkFrame(frame)
        self.autoScanTv = CheckboxScrollableTreeview(tvFrame, ("Command", 'Category', 'Category title', 'Priority'), maxPerPage=25, height=25, sort_keys=(None, None, None, int), fill=tk.X, autoresize=False)
        self.autoScanTv.pack(fill=tk.BOTH, expand="yes", padx=10, side=tk.BOTTOM, anchor=tk.CENTER)
        tvFrame.pack(fill=tk.BOTH, expand="yes", padx=10, pady=10, side=tk.BOTTOM)
        self.switch_auto_queue = CTkSwitch(frame, text="Continously queue selected command(s)")
        self.switch_auto_queue.pack(padx=10,pady=15,side=tk.BOTTOM)
        self.refreshUI()

    def check_all(self):
        if self.check_box_all.get():
            self.autoScanTv.checkAll()
        else:
            self.autoScanTv.uncheckAll()
    
    def refreshUI(self):
        settings = Settings()
        settings._reloadDbSettings()
        apiclient = APIClient.getInstance()
        checks = list(CheckItem.fetchObjects({"pentest_types":settings.getPentestType(), "check_type":"auto_commands"}))
        commands_iids = set()
        lkuptable = {}
        for check in checks:
            commands_iids = commands_iids.union(set(check.commands))
            for command in check.commands:
                lkuptable[str(command)] = check
        commands = Command.fetchObjects({"original_iid":{"$in":list(commands_iids)}}, targetdb=apiclient.getCurrentPentest())
        self.autoScanTv.reset()
        for command in commands:
            check = lkuptable.get(str(command.original_iid), None)
            if check is None:
                logger.debug("ERROR : command without a check")
                continue
            try:
                self.autoScanTv.insert('',"end", str(command.getId()), text=command.name, values=(check.category, check.title, str(check.priority)))
            except tk.TclError as e:
                pass
        
