"""User auth infos module to store and use user login informations """
import tkinter as tk
import tkinter.messagebox
import tkinter.ttk as ttk
from customtkinter import *
from bson.objectid import ObjectId
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.modules.module import Module
from pollenisatorgui.core.models.checkitem import CheckItem
from pollenisatorgui.core.application.treeviews.CheatsheetTreeview import CheatsheetTreeview
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.scrollableframexplateform import ScrollableFrameXPlateform

class Cheatsheet(Module):
    iconName = "tab_cheatsheet.png"
    tabName = "Cheatsheet"
    coll_name = "cheatsheet"
    order_priority = Module.LOW_PRIORITY
    pentest_types = ["all"]

    def __init__(self, parent, settings, tkApp):
        """
        Constructor
        """
        super().__init__()
        self.dashboardFrame = None
        self.parent = None
        self.infos = {}
        self.treevw = None
        self.tkApp = tkApp
        self.style = None
        self.icons = {}
        self.inited = False
    
    def open(self,view, nbk, treevw):
        apiclient = APIClient.getInstance()
        if self.inited is False:
            self.treevw = treevw
            self.initUI(view)
        if apiclient.getCurrentPentest() is not None:
            self.refreshUI()
        return True

    def refreshUI(self):
        """
        Reload data and display them
        """
        self.loadData()
        self.displayData()

    def loadData(self):
        """
        Fetch data from database
        """
        apiclient = APIClient.getInstance()
        

    def displayData(self):
        """
        Display loaded data in treeviews
        """
        self.treevw.load()

    def initUI(self, parent):
        """
        Initialize Dashboard widgets
        Args:
            parent: its parent widget
        """
        self.inited = True
        self.parent = parent
        self.moduleFrame = CTkFrame(parent)
        #PANED PART
        self.paned = tk.PanedWindow(self.moduleFrame, height=800)
        #RIGHT PANE : Canvas + frame
        
        self.container = CTkFrame(self.paned) # proxy for ScrollableFrame which can't be added to panedWindow
        self.viewframe = ScrollableFrameXPlateform(self.container)
        #LEFT PANE : Treeview
        self.frameTw = CTkFrame(self.paned)
        self.treevw = CheatsheetTreeview(
            self.tkApp, self.frameTw, self.viewframe)
        self.treevw.heading("#0", text="Cheatsheets")
        self.treevw.initUI()
        btn_add_check = CTkButton(self.frameTw, text="Add a check", command=self.createCheck)
        scbVSel = CTkScrollbar(self.frameTw,
                                orientation=tk.VERTICAL,
                                command=self.treevw.yview)
        self.treevw.configure(yscrollcommand=scbVSel.set)
        self.treevw.grid(row=0, column=0, sticky=tk.NSEW)
        scbVSel.grid(row=0, column=1, sticky=tk.NS)
        btn_add_check.grid(row=1, column=0, sticky=tk.S)
        self.paned.add(self.frameTw)
        self.viewframe.pack(fill=tk.BOTH, expand=1)
        self.paned.add(self.container)
        self.paned.pack(fill=tk.BOTH, expand=1)
        self.frameTw.rowconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        self.frameTw.columnconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        self.moduleFrame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def onCheatsheetDelete(self, event):
        """Callback for a delete key press on a worker.
        Force deletion of worker
        Args:
            event: Auto filled
        """
        apiclient = APIClient.getInstance()
        selected = self.treevw.selection()
        apiclient.bulkDelete({"checkitems":selected}) 

    def createCheck(self, event=None):
        self.treevw.openInsertWindow(CheckItem())

    def update_received(self, dataManager, notif, obj, old_obj):
        if notif["db"] == "pollenisator":
            if self.treevw is not None:
                self.treevw.update_received(dataManager, notif, obj, old_obj)

