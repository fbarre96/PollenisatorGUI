"""Ttk treeview class with added functions.
"""
import tkinter as tk
from bson.objectid import ObjectId
from pollenisatorgui.core.Application.Treeviews.PollenisatorTreeview import PollenisatorTreeview
from pollenisatorgui.core.Components.apiclient import APIClient
from pollenisatorgui.core.Application.Dialogs.ChildDialogQuestion import ChildDialogQuestion

from pollenisatorgui.core.Models.CheckItem import CheckItem
from pollenisatorgui.core.Views.CheckItemView import CheckItemView
from pollenisatorgui.core.Views.MultiCheckItemView import MultiCheckItemView
from pollenisatorgui.core.Controllers.CheckItemController import CheckItemController

from pollenisatorgui.core.Models.CheckInstance import CheckInstance
from pollenisatorgui.core.Views.CheckInstanceView import CheckInstanceView
from pollenisatorgui.core.Controllers.CheckInstanceController import CheckInstanceController

class CheatsheetTreeview(PollenisatorTreeview):
    """CheatsheetTreeview class
    Inherit PollenisatorTreeview.
    Ttk treeview class with added functions to handle the command objects.
    """

    def __init__(self, appli, parentFrame, viewFrame):
        """
        Args:
            appli: a reference to the main Application object.
            parentFrame: the parent tkinter window object.
        """
        super().__init__(appli, parentFrame)
        self.viewFrame = viewFrame
        self.openedViewFrameId = None  # if of the currently opened object in the view frame

    def attachViewFrame(self, viewFrame):
        self.viewFrame = viewFrame


    def initUI(self, _event=None):
        """Initialize the user interface widgets and binds them.
        Args:
            _event: not used but mandatory
        """
        self._initContextualsMenus()
        self.title = "Cheatsheet"
        self.heading('#0', text='Checks', anchor=tk.W)
        self.column('#0', stretch=tk.YES, minwidth=300, width=300)
        self.bind("<Button-3>", self.doPopup)
        self.bind("<<TreeviewSelect>>", self.onTreeviewSelect)
        #self.bind("<Return>", self.onTreeviewSelect)
        #self.bind("<Button-1>", self.onTreeviewSelect)
        self.bind('<Delete>', self.deleteSelected)
    
    def onTreeviewSelect(self, event=None):
        """Called when a line is selected on the treeview
        Open the selected object view on the view frame.
        IF it's a parent commands or command_groups node, opens Insert
        ELSE open a modify window
        Args:
            event: filled with the callback, contains data about line clicked
        """
        selection = self.selection()
        if len(selection) == 1:
            item = super().onTreeviewSelect(event)
            if isinstance(item, str):
                if "pentest|" not in str(item):
                    objView = CheckItemView(
                        self, self.viewFrame, self.appli, CheckItemController(CheckItem({"category":str(item)})))
                    objView.openInsertWindow()
            else:
                self.openModifyWindowOf(item)
        elif len(selection) > 1:
            # Multi select:
            multiView = MultiCheckItemView(self, self.viewFrame, self.appli)
            for widget in self.viewFrame.winfo_children():
                widget.destroy()
            multiView.form.clear()
            multiView.openModifyWindow()


    def doPopup(self, event):
        """Open the popup 
        Args:
            event: filled with the callback, contains data about line clicked
        """
        self.contextualMenu.selection = self.identify(
            "item", event.x, event.y)
        super().doPopup(event)

    def openModifyWindowOf(self, dbId):
        """
        Retrieve the View of the database id given and open the modifying form for its model and open it.

        Args:
            dbId: the database Mongo Id to modify.
        """
        objView = self.getViewFromId(str(dbId))
        if objView is not None:
            for widget in self.viewFrame.winfo_children():
                widget.destroy()
            objView.form.clear()
            self.openedViewFrameId = str(dbId)
            objView.openModifyWindow()

    def load(self, _searchModel=None):
        """
        Load the treeview with database information

        Args:
            _searchModel: (Deprecated) inherited not used. 
        """
        for widget in self.viewFrame.winfo_children():
            widget.destroy()
        self.delete(*self.get_children())

        self._load()

    def _load(self):
        """
        Load the treeview with database information
        """
       
        checkitems = CheckItem.fetchObjects({})
        checkitems = sorted(checkitems, key=lambda x:x.step)
        for checkitem in checkitems:
            checkitem_vw = CheckItemView(
                self, self.viewFrame, self.appli, CheckItemController(checkitem))
            checkitem_vw.addInTreeview()

        checkinstances = CheckInstance.fetchObjects({})
        for checkinstance in checkinstances:
            if checkinstance.check_m is not None:
                checkinstance_vw = CheckInstanceView(
                    self, self.viewFrame, self.appli, CheckInstanceController(checkinstance))
                checkinstance_vw.addInTreeview()
            
    def deleteSelected(self, _event):
        """
        Interface to delete a database object from an event.
        Prompt the user a confirmation window.
        Args:
            _event: not used, a ttk Treeview event autofilled. Contains information on what treeview node was clicked.
        """
        n = len(self.selection())
        dialog = ChildDialogQuestion(self.parentFrame,
                                     "DELETE WARNING", "Becareful for you are about to delete "+str(n) + " entries and there is no turning back.", ["Delete", "Cancel"])
        self.wait_window(dialog.app)
        if dialog.rvalue != "Delete":
            return
        if n == 1:
            view = self.getViewFromId(self.selection()[0])
            if view is None:
                return
            view.delete(None, False)
        else:
            toDelete = {}
            for selected in self.selection():
                view = self.getViewFromId(selected)
                if view is not None:
                    viewtype = view.controller.model.coll_name
                    if viewtype not in toDelete:
                        toDelete[viewtype] = []
                    toDelete[viewtype].append(view.controller.getDbId())
            apiclient = APIClient.getInstance()
            apiclient.bulkDelete(toDelete)

    def refresh(self):
        """Alias to self.load method"""
        self.load()

    def _initContextualsMenus(self):
        """
        Create the contextual menu
        """
        self.contextualMenu = tk.Menu(self.parentFrame, tearoff=0, background='#A8CF4D',
                                      foreground='black', activebackground='#A8CF4D', activeforeground='white')
        self.contextualMenu.add_command(
            label="Sort children", command=self.sort)
        self.contextualMenu.add_command(
            label="Expand", command=self.expand)
        self.contextualMenu.add_command(
            label="Collapse", command=self.collapse)
        self.contextualMenu.add_separator()
        self.contextualMenu.add_command(
            label="Close", command=self.closeMenu)
        super()._initContextualsMenus
        return self.contextualMenu

    def notify(self, db, collection, iid, action, parent):
        """
        Callback for the observer pattern implemented in mongo.py.

        Args:
            collection: the collection that has been modified
            iid: the mongo ObjectId _id that was modified/inserted/deleted
            action: update/insert/delete. It was the action performed on the iid
            parent: the mongo ObjectId of the parent. Only if action in an insert.
        """
        if collection != "cheatsheet":
            return
        # Delete
        apiclient = APIClient.getInstance()
        if action == "delete":
            try:
                self.delete(ObjectId(iid))
            except tk.TclError:
                pass  # item was not inserted in the treeview

        # Insert
        if action == "insert":
            if collection == "cheatsheet":
                checkitem = CheckItem.fetchObject({"_id":ObjectId(iid)})
                view = CheckItemView(self, self.viewFrame,
                                   self.appli, CheckItemController(checkitem))
                parent = None
            try:
                view.addInTreeview(parent)
                if view is not None:
                    view.insertReceived()
            except tk.TclError:
                pass

        if action == "update":
            try:
                view = self.getViewFromId(str(iid))
                if view is not None:
                    self.item(str(iid), text=str(
                        view.controller.getModelRepr()), image=view.getIcon())
            except tk.TclError:
                if view is not None:
                    view.addInTreeview()
            if str(self.openedViewFrameId) == str(iid):
                view.clearWindow()
                view.openModifyWindow()
            if view is not None:
                view.controller.actualize()
                view.updateReceived()
