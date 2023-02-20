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

class Cheatsheet(Module):
    iconName = "tab_cheatsheet.png"
    tabName = "Cheatsheet"
    collName = "cheatsheet"
    pentest_types = ["all"]

    def __init__(self, parent, settings):
        """
        Constructor
        """
        super().__init__()
        self.dashboardFrame = None
        self.parent = None
        self.infos = {}
        self.treevw = None
        self.style = None
        self.icons = {}
    
    def open(self):
        apiclient = APIClient.getInstance()
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
    
    def resizeCanvasMainFrame(self, event):
        canvas_width = event.width
        self.canvasMain.itemconfig(self.canvas_main_frame, width=canvas_width)

    def scrollFrameMainFunc(self, _event):
        """make the main canvas scrollable"""
        self.canvasMain.configure(scrollregion=self.canvasMain.bbox("all"), width=20, height=200)

    def initUI(self, parent, nbk, treevw, tkApp):
        """
        Initialize Dashboard widgets
        Args:
            parent: its parent widget
        """
        if self.parent is not None:  # Already initialized
            return
        self.parent = parent
        self.tkApp = tkApp
        self.treevwApp = treevw
        self.moduleFrame = CTkFrame(parent)
        #PANED PART
        self.paned = tk.PanedWindow(self.moduleFrame, height=800)
        #RIGHT PANE : Canvas + frame
        self.canvasMain = tk.Canvas(self.paned, bg="white")
        self.viewframe = CTkFrame(self.canvasMain)
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
        self.myscrollbarMain = CTkScrollbar(self.paned, orientation="vertical", command=self.canvasMain.yview)
        self.myscrollbarMain.pack(side="right", fill=tk.BOTH)
        self.canvasMain.bind('<Enter>', self.boundToMousewheelMain)
        self.canvasMain.bind('<Leave>', self.unboundToMousewheelMain)
        self.canvasMain.pack(side="left")
        self.canvasMain.bind('<Configure>', self.resizeCanvasMainFrame)
        self.canvas_main_frame = self.canvasMain.create_window((0, 0), window=self.viewframe, anchor='nw')
        self.viewframe.bind("<Configure>", self.scrollFrameMainFunc)
        self.canvasMain.configure(yscrollcommand=self.myscrollbarMain.set)
        self.paned.add(self.canvasMain)
        self.paned.pack(fill=tk.BOTH, expand=1)
        self.frameTw.rowconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        self.frameTw.columnconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        
        self.moduleFrame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def boundToMousewheelMain(self, _event):
        """Called when the **main view canvas** is focused.
        Bind the main view scrollbar button on linux to the main view canvas
        Args:
            _event: not used but mandatory"""
        if self.canvasMain is None:
            return
        self.canvasMain.bind_all("<Button-4>", self._onMousewheelMain)
        self.canvasMain.bind_all("<Button-5>", self._onMousewheelMain)
        
    def _onMousewheelMain(self, event):
        """Called when a scroll occurs. boundToMousewheelMain must be called first.
        Performs the scroll on the main canvas.
        Args:
            event: Holds info on scroll within event.delta and event.num"""
        if event.num == 5 or event.delta == -120:
            count = 1
        if event.num == 4 or event.delta == 120:
            count = -1
        self.canvasMain.yview_scroll(count, "units")

    def unboundToMousewheelMain(self, _event):
        """Called when the **main view canvas** is unfocused.
        Unbind the main view scrollbar button on linux to the main view canvas
        Args:
            _event: not used but mandatory"""
        self.canvasMain.unbind_all("<Button-4>")
        self.canvasMain.unbind_all("<Button-5>")
     
    def onCheatsheetDelete(self, event):
        """Callback for a delete key press on a worker.
        Force deletion of worker
        Args:
            event: Auto filled
        """
        apiclient = APIClient.getInstance()
        selected = self.treevw.selection()
        apiclient.bulkDelete({"cheatsheet":selected}) 

    def createCheck(self, event=None):

        self.treevw.openInsertWindow(CheckItem())

    def update(self, dataManager, notif, obj, old_obj):
        if notif["db"] == "pollenisator":
            if self.treevw is not None:
                self.treevw.update(dataManager, notif, obj, old_obj)

