"""Ttk treeview class with added functions.
"""
import tkinter as tk
from bson.objectid import ObjectId
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.models.command import Command
from pollenisatorgui.core.views.commandview import CommandView
from pollenisatorgui.core.views.multicommandview import MultiCommandView
from pollenisatorgui.core.controllers.commandcontroller import CommandController
from pollenisatorgui.core.application.treeviews.PollenisatorTreeview import PollenisatorTreeview
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
import pollenisatorgui.core.components.utils as utils

class CommandsTreeview(PollenisatorTreeview):
    """CommandsTreeview class
    Inherit PollenisatorTreeview.
    Ttk treeview class with added functions to handle the command objects.
    """

    def __init__(self, appli, parentFrame):
        """
        Args:
            appli: a reference to the main Application object.
            parentFrame: the parent tkinter window object.
        """
        super().__init__(appli, parentFrame)
        self.commands_node = None  # parent of all commands nodes
        self.openedViewFrameId = None  # if of the currently opened object in the view frame
        
    

    def initUI(self, _event=None):
        """Initialize the user interface widgets and binds them.
        Args:
            _event: not used but mandatory
        """
        if self.commands_node is not None:
            return
        self._initContextualsMenus()
        self.heading('#0', text='Commands', anchor=tk.W)
        self.column('#0', stretch=tk.YES, minwidth=300, width=300)
        self.bind("<Button-3>", self.doPopup)
        self.bind("<<TreeviewSelect>>", self.onTreeviewSelect)
        #self.bind("<Return>", self.onTreeviewSelect)
        #self.bind("<Button-1>", self.onTreeviewSelect)
        self.bind('<Delete>', self.deleteSelected)
        self.load()
        self.switchExpandCollapse(True, self.commands_node)

    def onTreeviewSelect(self, event=None):
        """Called when a line is selected on the treeview
        Open the selected object view on the view frame.
        IF it's a parent commands or other node, opens Insert
        ELSE open a modify window
        Args:
            event: filled with the callback, contains data about line clicked
        """
        selection = self.selection()
        if len(selection) == 1:
            item = super().onTreeviewSelect(event)
            if isinstance(item, str):
                pass
                # apiclient = APIClient.getInstance()
                # if str(item) == "mycommands":
                #     user = apiclient.getUser()
                #     objView = CommandView(
                #         self, self.appli.commandsViewFrame, self.appli, CommandController(Command({"owners":[user]})))
                #     objView.openInsertWindow()
                # elif str(item) == "commands":
                #     objView = CommandView(
                #         self, self.appli.commandsViewFrame, self.appli, CommandController(Command({})))
                #     objView.openInsertWindow()
            else:
                self.openModifyWindowOf(item)
        elif len(selection) > 1:
            # Multi select:
            multiView = MultiCommandView(self, self.appli.commandsViewFrame, self.appli)
            for widget in self.appli.commandsViewFrame.winfo_children():
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
            for widget in self.appli.commandsViewFrame.winfo_children():
                widget.destroy()
            objView.form.clear()
            self.openedViewFrameId = str(dbId)
            objView.openModifyWindow(treevw="commands")

    def load(self, _searchModel=None):
        """
        Load the treeview with database information

        Args:
            _searchModel: (Deprecated) inherited not used. 
        """
        for widget in self.appli.commandsViewFrame.winfo_children():
            widget.destroy()
        self.delete(*self.get_children())

        self._load()

    def _load(self):
        """
        Load the treeview with database information
        """
        self.commands_node = self.insert(
            "", "end", "commands", text="Commands", image=CommandView.getClassIcon())
        commands = Command.fetchObjects({})
        for command in commands:
            command_vw = CommandView(
                self, self.appli.commandsViewFrame, self.appli, CommandController(command))
            command_vw.addInTreeview()
        
    def deleteSelected(self, _event=None):
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
            apiclient.bulkDeleteCommands(toDelete)

    def refresh(self, force=True):
        """Alias to self.load method"""
        self.load()

    def _initContextualsMenus(self):
        """
        Create the contextual menu
        """
        
        self.contextualMenu = utils.craftMenuWithStyle(self.parentFrame)
        self.contextualMenu.add_command(
            label="Add command", command=self.addCommand)
        self.contextualMenu.add_command(
            label="Duplicate command", command=self.duplicateCommand)
        self.contextualMenu.add_separator()
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
    
    def addCommand(self, _event=None):
        objView = CommandView(
                        self, self.appli.commandsViewFrame, self.appli, CommandController(Command({})))
        objView.openInsertWindow()

    def duplicateCommand(self, _event=None):
        for selected in self.selection():
            view_o = self.getViewFromId(selected)
            if view_o is not None:
                if isinstance(view_o, CommandView):
                    data = view_o.controller.getData()
                    del data["_id"]
                    data["name"] = data["name"] + "_dup"
                    objView = CommandView(
                        self, self.appli.commandsViewFrame, self.appli, CommandController(Command(data)))
                    objView.openInsertWindow()
                    
    
    def update_received(self, dataManager, notification, obj, oldObj):
        """
        Callback for the observer pattern implemented in mongo.py.

        Args:
            collection: the collection that has been modified
            iid: the mongo ObjectId _id that was modified/inserted/deleted
            action: update/insert/delete. It was the action performed on the iid
            parent: the mongo ObjectId of the parent. Only if action in an insert.
        """
        if notification["db"] != "pollenisator":
            return
        if notification["collection"] != "commands":
            return
        action = notification["action"]
        iid = notification["iid"]
        # Delete
        apiclient = APIClient.getInstance()
        if action == "delete":
            try:
                self.delete(ObjectId(iid))
            except tk.TclError:
                pass  # item was not inserted in the treeview
        # Insert
        if action == "insert":
            res = Command.fetchObject({"_id": ObjectId(iid)})
            view = CommandView(self, self.appli.commandsViewFrame,
                                self.appli, CommandController(res))
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
            if str(iid) == self.openedViewFrameId:
                self.event_generate("<F6>")
            if view is not None:
                view.controller.actualize()
                view.updateReceived()
