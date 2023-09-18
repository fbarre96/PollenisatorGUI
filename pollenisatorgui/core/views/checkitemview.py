"""View for checkitem object. Handle node in treeview and present forms to user when interacted with."""

from pollenisatorgui.core.application.dialogs import ChildDialogView
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.controllers.commandcontroller import CommandController
from pollenisatorgui.core.views.commandview import CommandView
from pollenisatorgui.core.views.viewelement import ViewElement
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.models.tool import Tool
from pollenisatorgui.core.models.command import Command
from pollenisatorgui.core.controllers.checkitemcontroller import CheckItemController
from pollenisatorgui.core.models.checkitem import CheckItem
from pollenisatorgui.core.components.scriptmanager import ScriptManager
import pollenisatorgui.core.components.utils as utils
from customtkinter import *
from bson import ObjectId
import tkinter as tk

class CheckItemView(ViewElement):
    """
    View for CheckItemView object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory.
    """
    default_icon = 'checklist.png'
    cached_default_icon = None
    icon = "checklist.png"
    icon_auto = 'auto.png'
    cached_icon_auto = None

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

    def getIcon(self):
        """
        Load the object icon in cache if it is not yet done, and returns it

        Return:
            Returns the icon representing this object.
        """
        isAuto = self.controller.isAuto()
        if isAuto: # order is important as "done" is not_done but not the other way
            ui = self.__class__.icon_auto
            cache = self.__class__.cached_icon_auto
            iconStatus = "auto"
        else:
            cache = self.__class__.cached_default_icon
            ui = self.__class__.default_icon
            iconStatus = "default"
        if cache is None:
            from PIL import Image, ImageTk

            path = utils.getIcon(ui)
            if iconStatus == "auto":
                self.__class__.cached_icon_auto = ImageTk.PhotoImage(
                    Image.open(path))
                return self.__class__.cached_icon_auto
            else:
                self.__class__.cached_default_icon = ImageTk.PhotoImage(
                    Image.open(path))
                return self.__class__.cached_default_icon
        return cache

    def _commonWindowForms(self, default={}, action="modify"):
        """Construct form parts identical between Modify and Insert forms
        Args:
            default: a dict of default values for inputs (priority, priority, max_thread). Default to empty respectively "0", "0", "1"
        """
        self.form.addFormHidden("Step", default.get("step", 0))
        self.form.addFormHidden("Parent", default.get("parent", ""))
        panel_bottom = self.form.addFormPanel(grid=True)
        panel_bottom.addFormLabel("Check type", row=0, column=0)
        self.checktypeForm = panel_bottom.addFormCombo("Check type", ("manual_commands", "auto_commands", "script", "manual"), 
                                                        default=default.get("check_type","manual"),  
                                                        command=lambda ev: self.updateCheckType(action),
                                                        row=0, column=1)
        panel_bottom.addFormLabel("Trigger", row=0, column=0)
        panel_bottom.addFormChecklist("Pentest types", list(Settings.getPentestTypes().keys()), default.get("pentest_types", []), row=1, column=1)
        panel_bottom = self.form.addFormPanel(grid=True)
        apiclient = APIClient.getInstance()
        lvls = apiclient.getTriggerLevels()
        panel_bottom.addFormLabel("Trigger", row=0, column=0)
        true_lvl = default.get("lvl", "port:onServiceUpdate")
        if true_lvl.startswith("tag:"):
            true_lvl = ":".join(true_lvl.split(":")[:2])+":str"
        self.triggerLevelForm = panel_bottom.addFormCombo(
            "Level", lvls, true_lvl,  command=lambda ev: self.triggerLevelUpdate(true_lvl), width=200, row=0, column=1)
        panel_bottom.addFormHelper(
            "When the event is triggered, \na instance for this check will be created on the triggering object", row=0, column=2)
        self.panel_trigger_options = self.form.addFormPanel(grid=True)
        if default.get("lvl","port:onServiceUpdate").startswith("port"):
            self.panel_trigger_options.clear()
            self.panel_trigger_options.addFormLabel("Ports/Services (if level is port only)")
            self.panel_trigger_options.addFormStr(
                "Ports/Services", r"^(\d{1,5}|[^\,]+)?(?:,(\d{1,5}|[^\,]+))*$", default.get("ports", ""), column=1)
            self.panel_trigger_options.addFormHelper(
                "Services, ports or port ranges.\nthis list must be separated by a comma, if no protocol is specified, tcp/ will be used.\n Example: ssl/http,https,http/ssl,0-65535,443...", column=2)
        if default.get("lvl", "").startswith("tag:"):
            lvl_split = default.get("lvl", "").split(":")
            if len(lvl_split) == 3:
                tag_name = lvl_split[2] 
            else:
                tag_name = ""
            self.panel_trigger_options.clear()
            self.panel_trigger_options.addFormLabel("Tag name")
            self.panel_trigger_options.addFormStr(
                "Tag Name", r".+", tag_name, column=1)
            self.panel_trigger_options.addFormHelper(
                "Tag filter to trigger this check", column=2)
        panel_bottom = self.form.addFormPanel(grid=True)
        panel_bottom.addFormLabel("Category", row=1, column=0)
        panel_bottom.addFormStr("Category", r"", default.get("category", ""), row=1, column=1)
        panel = self.form.addFormPanel(grid=True)
        panel.addFormLabel("Priority")
        panel.addFormStr(
            "Priority", r"\d+", default["priority"], width=40, column=1)
        panel.addFormHelper(
            "Defines the priority of this group of command when an auto scan is running.\nAutoscan will try to launch the highest priority (0 is max) and the highest+1.", column=2)
        
        panel_bottom = self.form.addFormPanel()
        panel_bottom.addFormLabel("Description")
        panel_bottom.addFormText("Description", r"", default.get("description", ""), side="right")
        if "commands" in default.get("check_type", "manual"):
            formCommands = self.form.addFormPanel(grid=True)
            formCommands.addFormLabel("Shared threads")
            formCommands.addFormStr("Shared threads", r"\d+",
                            default["max_thread"], width=40, column=1)
            panel.addFormHelper(
                "Number of parallel execution allowed for every command in this group at any given moment.", column=2)
            formTv = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5)
            formSearchCommand = formTv.addFormPanel(side=tk.LEFT, fill=tk.Y, pady=5, padx=5)
            formSearchCommand.addFormSearchBar("Commands search", self.searchCallback, self.form, side=tk.TOP)
            formSearchCommand.addFormSeparator()
            formSearchCommand.addFormButton("Create new command", self.create_command_callback, side=tk.TOP)
            commands = default.get("commands")
            if commands is None:
                tv_commands = ["", ""]
            else:
                tv_commands = []
                for command in commands:
                    comm = Command.fetchObject({"_id":ObjectId(command)})
                    if comm is not None:
                        tv_commands.append((comm.name, str(command)))
            self.treeview_commands = formTv.addFormTreevw(
                "Commands", ("Command names",), tv_commands, doubleClickBinds=[self.onCommandDoubleClick],height=5, width=30, pady=5, fill=tk.X, side=tk.RIGHT)
        elif "script" in default.get("check_type", "manual"):
            formTv = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5)
            formTv.addFormLabel("Script", side=tk.LEFT)
            self.textForm = formTv.addFormStr("Script", ".+", default.get("script", ""))
            btn = formTv.addFormButton("Browse", lambda _event : self.browseScriptCallback(self.textForm))

    def triggerLevelUpdate(self, old_value):
        if self.triggerLevelForm.getValue() != old_value:
            self.controller.model.lvl = self.triggerLevelForm.getValue()
            self.reopen()

    def onCommandDoubleClick(self, oldval):
        command_o = Command.fetchObject({"name":oldval})
        if command_o is None:
            return
        view = CommandView(self.appliTw, self.appliViewFrame, self.mainApp, CommandController(command_o))
        view.openInDialog()
        
    def reopen(self):
        if self.is_insert_view:
            self.openInsertWindow()
            return
        self.openModifyWindow()

    def updateCheckType(self, action):
        form_values = self.form.getValue()
        form_values_as_dicts = ViewElement.list_tuple_to_dict(form_values)
        self.controller.doUpdate(form_values_as_dicts, updateInDb=False)
        self.form.clear()
        if action == "modify":
            self.openModifyWindow()
        else:
            self.openInsertWindow()

    def browseScriptCallback(self, textForm):
        scriptManagerInst = ScriptManager()
        scriptManagerInst.initUI(self.mainApp, whatfor="select")
        self.mainApp.wait_window(scriptManagerInst.app)
        liste = scriptManagerInst.rvalue
        textForm.setValue(", ".join(liste))
        
    def openModifyWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing Command
        """
        self.is_insert_view = False
        self.form.clear()
        modelData = self.controller.getData()
        self._initContextualMenu()
        panel_top = self.form.addFormPanel(grid=True)
        panel_top.addFormLabel("Title", column=0)
        panel_top.addFormStr("Title", r".+", default=modelData.get("title", ""), column=1)

        self._commonWindowForms(modelData, action="modify")
        #if modelData.get("parent") is None:
            #self.form.addFormButton("Add a step", self.addStep)
        self.completeModifyWindow(editable=True, addTags=False)



    def addStep(self, event=None):
        newCheckItem = CheckItem({"parent":str(self.controller.getDbId())})
        view = CheckItemView(self.appliTw, self.appliViewFrame, self.mainApp, CheckItemController(newCheckItem))
        view.openInsertWindow()

    def openInsertWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to insert a new Command
        """
        self.is_insert_view = True
        self.form.clear()
        data = self.controller.getData()
        self._initContextualMenu()
        panel_top = self.form.addFormPanel(grid=True)
        panel_top.addFormLabel("Title", column=0)
        panel_top.addFormStr("Title", r".+", default=data.get("title", ""), column=1)
        
       
        self._commonWindowForms(data, action="insert")
        self.completeInsertWindow()


    def addInTreeview(self, parentNode=None, with_category=False):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
        """
        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}

        if parentNode is None:
            parentNode = self.getParentNode(with_category)
        try:
            self.appliTw.insert(parentNode, "end", str(
                self.controller.getDbId()), text=str(self.controller.getModelRepr()), tags=self.controller.getTags(), image=self.getIcon())
        except tk.TclError:
            pass
        if hasattr(self.appliTw, "hide"):
            if not self.mainApp.settings.is_checklist_view():
                self.hide("checklist_view")
            if "hidden" in self.controller.getTags():
                self.hide("tags")
            if self.mainApp.settings.is_show_only_manual() and self.controller.isAuto():
                self.hide("filter_manual")
            

    def getParentNode(self, with_category=False):
        """
        Return the id of the parent node in treeview.

        Returns:
            return the saved command_node node inside the Appli class.
        """
        if with_category:
            category = self.controller.getCategory()
            try:
                self.appliTw.insert("", "end", category, text=self.controller.getCategory(), tags=self.controller.getTags(), image=self.__class__.getClassIcon())
            except tk.TclError:
                pass
            if hasattr(self.appliTw, "hide") and not self.mainApp.settings.is_checklist_view():
                self.appliTw.hide(category, "checklist_view")
            return category
        parent = self.controller.getParent()
        if parent is not None and parent != "":
            return parent
        
        return "" # category

    def _initContextualMenu(self):
        """Initiate contextual menu with variables"""
        self.menuContextuel = utils.craftMenuWithStyle(self.appliViewFrame)

    def popup(self, event):
        """
        Fill the self.widgetMenuOpen and reraise the event in the editing window contextual menu

        Args:
            event: a ttk Treeview event autofilled. Contains information on what treeview node was clicked.
        """
        self.widgetMenuOpen = event.widget
        self.menuContextuel.tk_popup(event.x_root, event.y_root)
        self.menuContextuel.focus_set()
        self.menuContextuel.bind('<FocusOut>', self.popupFocusOut)

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
    
    def create_command_callback(self, _event=None):
        view = CommandView(self.appliTw, self.appliViewFrame, self.mainApp, CommandController(Command()))
        result, msg = view.openInDialog(is_insert=True)
        if result:
            comm = Command.fetchObject({"_id":ObjectId(msg)})
            if comm is not None:
                self.treeview_commands.addItem("", "end", str(msg), text=comm.name, values=(0, str(comm.getId()),))
            else:
                tk.messagebox.showerror("Error inserting command", msg)

    def updateReceived(self, obj=None, old_obj=None):
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
            tuple, key to sort
        """
        return tuple([ord(c) for c in str(self.controller.getModelRepr()).lower()])

    # function that converts a string into a lsit of ascii values
    def convert(self, string):  
        li = list(string.split(" ")) 
        return li   
