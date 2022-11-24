"""View for checkitem object. Handle node in treeview and present forms to user when interacted with."""

from pollenisatorgui.core.Components.apiclient import APIClient
from pollenisatorgui.core.Views.ViewElement import ViewElement
from pollenisatorgui.core.Components.Settings import Settings
from pollenisatorgui.core.Models.Tool import Tool
from pollenisatorgui.core.Models.Command import Command
from pollenisatorgui.core.Controllers.CheckItemController import CheckItemController
from pollenisatorgui.core.Models.CheckItem import CheckItem
from pollenisatorgui.core.Components.ScriptManager import ScriptManager

from bson import ObjectId
import tkinter as tk

class CheckItemView(ViewElement):
    """
    View for CheckItemView object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory.
    """
    icon = 'checklist.png'

    def __init__(self, appTw, appViewFrame, mainApp, controller):
        """Constructor
        Args:
            appTw: a PollenisatorTreeview instance to put this view in
            appViewFrame: an view frame to build the forms in.
            mainApp: the Application instance
            controller: a CommandController for this view.
        """
        self.menuContextuel = None
        self.widgetMenuOpen = None
        self.checktypeForm = None
        super().__init__(appTw, appViewFrame, mainApp, controller)

    def _commonWindowForms(self, default={}, action="modify"):
        """Construct form parts identical between Modify and Insert forms
        Args:
            default: a dict of default values for inputs (priority, priority, max_thread). Default to empty respectively "0", "0", "1"
        """
        self.form.addFormHidden("Step", default.get("step", 0))
        self.form.addFormHidden("Parent", default.get("parent", ""))
        panel_bottom = self.form.addFormPanel(grid=True)
        panel_bottom.addFormLabel("Check type", row=0, column=0)
        self.checktypeForm = panel_bottom.addFormCombo("Check type", ("manual_commands", "auto_commands", "script", "manual"), default=default.get("check_type","manual"),  binds={"<<ComboboxSelected>>": lambda ev: self.updateCheckType(action)}, row=0, column=1)
        panel_bottom = self.form.addFormPanel(grid=True)
        panel_bottom.addFormChecklist("Pentest types", list(Settings.getPentestTypes().keys()), default.get("pentest_types", []), row=1, column=1)
        if default.get("parent") is None:
            panel_bottom.addFormLabel("Category", row=2, column=0)
            panel_bottom.addFormStr("Category", r"", default.get("category", ""), width=50, row=2, column=1)
        panel_bottom = self.form.addFormPanel()
        panel_bottom.addFormLabel("Description")
        panel_bottom.addFormText("Description", r"", default.get("description", ""), height=10, side="right")
        if "commands" in default.get("check_type", "manual"):
            formTv = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5)
            formTv.addFormSearchBar("Commands search", self.searchCallback, self.form, side=tk.TOP)
            formTv.addFormLabel("Commands associated", side=tk.LEFT)
            commands = default.get("commands")
            if commands is None:
                tv_commands = ["", ""]
            else:
                tv_commands = []
                for command in commands:
                    comm = Command.fetchObject({"_id":ObjectId(command)})
                    if comm is not None:
                        tv_commands.append((comm.name, str(command)))
            formTv.addFormTreevw(
                "Commands", ("Command names",), tv_commands, height=5, width=30, pady=5, fill=tk.X, side=tk.RIGHT)
        elif "script" in default.get("check_type", "manual"):
            formTv = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5)
            formTv.addFormLabel("Script", side=tk.LEFT)
            self.textForm = formTv.addFormStr("Script", ".+", default.get("script", ""))
            btn = formTv.addFormButton("Browse", lambda _event : self.browseScriptCallback(self.textForm))

    def updateCheckType(self, action):
        newValue = self.checktypeForm.getValue()
        self.controller.model.check_type = newValue
        self.form.clear()
        if action == "modify":
            self.openModifyWindow()
        else:
            self.openInsertWindow()

    def browseScriptCallback(self, textForm):
        scriptManagerInst = ScriptManager(self.mainApp, whatfor="select")
        self.mainApp.wait_window(scriptManagerInst.app)
        liste = scriptManagerInst.rvalue
        textForm.setValue(", ".join(liste))
        
    def openModifyWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing Command
        """
        modelData = self.controller.getData()
        self._initContextualMenu()
        panel_top = self.form.addFormPanel(grid=True)
        panel_top.addFormLabel("Title", column=0)
        panel_top.addFormStr("Title", r".+", default=modelData.get("title", ""), column=1)
      
        self._commonWindowForms(modelData, action="modify")
        if modelData.get("parent") is None:
            self.form.addFormButton("Add a step", self.addStep)
        self.completeModifyWindow()

    def clearWindow(self):
        for widget in self.appliViewFrame.winfo_children():
            widget.destroy()

    def addStep(self, event=None):
        newCheckItem = CheckItem({"parent":str(self.controller.getDbId())})
        view = CheckItemView(self.appliTw, self.appliViewFrame, self.mainApp, CheckItemController(newCheckItem))
        view.openInsertWindow()

    def openInsertWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to insert a new Command
        """
        self._initContextualMenu()
        panel_top = self.form.addFormPanel(grid=True)
        panel_top.addFormLabel("Title", column=0)
        panel_top.addFormStr("Title", r".+", column=1, width=50)

        self._commonWindowForms(self.controller.getData(), action="insert")
        self.completeInsertWindow()

    def addInTreeview(self, parentNode=None):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
        """
        if parentNode is None:
            parentNode = self.getParentNode()
        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}
        self.appliTw.insert(parentNode, "end", str(
            self.controller.getDbId()), text=str(self.controller.getModelRepr()), tags=self.controller.getTags(), image=self.getClassIcon())
        if "hidden" in self.controller.getTags():
            self.hide()

    def getParentNode(self):
        """
        Return the id of the parent node in treeview.

        Returns:
            return the saved command_node node inside the Appli class.
        """
        apiclient = APIClient.getInstance()
        category = self.controller.getCategory()
        try:
            self.appliTw.insert("", "end", "global", text="Setup Cheatsheets")
        except tk.TclError:
            pass
        try:
            self.appliTw.insert("global", "end", category, text=self.controller.getCategory(), tags=self.controller.getTags(), image=self.getClassIcon())
        except tk.TclError:
            pass
        parent = self.controller.getParent()
        if parent is not None and parent != "":
            return parent
        return category

    def _initContextualMenu(self):
        """Initiate contextual menu with variables"""
        self.menuContextuel = tk.Menu(self.appliViewFrame, tearoff=0, background='#A8CF4D',
                                      foreground='white', activebackground='#A8CF4D', activeforeground='white')

    def popup(self, event):
        """
        Fill the self.widgetMenuOpen and reraise the event in the editing window contextual menu

        Args:
            event: a ttk Treeview event autofilled. Contains information on what treeview node was clicked.
        """
        self.widgetMenuOpen = event.widget
        self.menuContextuel.tk_popup(event.x_root, event.y_root)
        self.menuContextuel.focus_set()
        #self.menuContextuel.bind('<FocusOut>', self.popupFocusOut)

    def popupFocusOut(self, _event=None):
        """
        Called when the contextual menu is unfocused
        Args:
            _event: a ttk event autofilled. not used but mandatory.
        """
        self.menuContextuel.unpost()

    def searchCallback(self, searchreq):
        apiclient = APIClient.getInstance()
        commands = apiclient.findInDb("pollenisator", "commands", {"name":{'$regex':searchreq}})
        if commands is None:
            return [], "Invalid response from API"

        ret = [{"TITLE":command["name"], "commands":{"text":command["name"], "values":(0, str(command["_id"]))}} for command in commands]
        return ret, ""

    def updateReceived(self):
        """Called when a command update is received by notification.
        Update the command treeview item (resulting in icon reloading)
        """
        # if self.controller.isMine():
        #     try:
        #         self.appliTw.move(str(self.controller.model.getId()), self.appliTw.my_commands_node, "end")
        #     except tk.TclError:
        #         print("WARNING: Update received for a non existing command "+str(self.controller.getModelRepr()))
        # else:
        #     try:
        #         self.appliTw.move(str(self.controller.model.getId()), self.appliTw.commands_node, "end")
        #     except tk.TclError:
        #         print("WARNING: Update received for a non existing command "+str(self.controller.getModelRepr()))
        
        super().updateReceived()

    def key(self):
        """Returns a key for sorting this node
        Returns:
            string, key to sort
        """
        return str(self.controller.getModelRepr()).lower()

