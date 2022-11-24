"""User auth infos module to store and use user login informations """
import tkinter as tk
import tkinter.messagebox
import tkinter.ttk as ttk
from bson.objectid import ObjectId
from pollenisatorgui.core.Components.apiclient import APIClient
from pollenisatorgui.Modules.Module import Module
from pollenisatorgui.core.Application.Treeviews.CheatsheetTreeview import CheatsheetTreeview

class Cheatsheet(Module):
    iconName = "tab_cheatsheet.png"
    tabName = "Cheatsheet"
    collName = "cheatsheet"
    pentest_types = ["all"]

    def __init__(self, parent, settings):
        """
        Constructor
        """
        
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
        self.moduleFrame = ttk.Frame(parent)
        #PANED PART
        self.paned = tk.PanedWindow(self.moduleFrame, height=800)
        #RIGHT PANE : Canvas + frame
        self.canvasMain = tk.Canvas(self.paned, bg="white")
        self.viewframe = ttk.Frame(self.canvasMain)
        #LEFT PANE : Treeview
        self.frameTw = ttk.Frame(self.paned)
        self.treevw = CheatsheetTreeview(
            self.tkApp, self.frameTw, self.viewframe)
        self.treevw.heading("#0", text="Cheatsheets")
        self.treevw.initUI()
        scbVSel = ttk.Scrollbar(self.frameTw,
                                orient=tk.VERTICAL,
                                command=self.treevw.yview)
        self.treevw.configure(yscrollcommand=scbVSel.set)
        self.treevw.grid(row=0, column=0, sticky=tk.NSEW)
        scbVSel.grid(row=0, column=1, sticky=tk.NS)
        self.paned.add(self.frameTw)
        self.myscrollbarMain = tk.Scrollbar(self.paned, orient="vertical", command=self.canvasMain.yview)
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


    def handleNotif(self, db, collection, iid, action):
        self.treevw.notify(db, collection, iid, action, None)

