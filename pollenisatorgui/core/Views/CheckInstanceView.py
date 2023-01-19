"""View for checkitem object. Handle node in treeview and present forms to user when interacted with."""

from venv import create
from pollenisatorgui.core.Components.apiclient import APIClient
from pollenisatorgui.core.Components.ScriptManager import ScriptManager
from pollenisatorgui.core.Controllers.ToolController import ToolController
from pollenisatorgui.core.Views.ToolView import ToolView
from pollenisatorgui.core.Views.ViewElement import ViewElement
from pollenisatorgui.core.Components.Settings import Settings
from pollenisatorgui.core.Models.Tool import Tool
from pollenisatorgui.core.Models.Command import Command
import pollenisatorgui.core.Components.Utils as Utils

from bson import ObjectId
import os
import tkinter as tk

class CheckInstanceView(ViewElement):
    """
    View for CheckInstanceView object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory.
    """
    done_icon = 'done_tool.png'
    running_icon = 'running.png'
    not_done_icon = 'cross.png'
    icon = 'checklist.png'

    cached_icon = None
    cached_done_icon = None
    cached_running_icon = None
    cached_not_ready_icon = None

    def getIcon(self):
        """
        Load the object icon in cache if it is not yet done, and returns it

        Return:
            Returns the icon representing this object.
        """
        infos = self.controller.getCheckInstanceInfos()
        modelData = self.controller.getData()
        status = infos.get("status", "")
        if status == "":
            status = modelData.get("status", "")
        if status == "":
            status = "not done"
        iconStatus = "not_done"
        if "not done" in status: # order is important as "done" is not_done but not the other way
            ui = self.__class__.not_done_icon
            cache = self.__class__.cached_not_ready_icon
            iconStatus = "not_done"
        elif "running" in status:
            ui = self.__class__.running_icon
            cache = self.__class__.cached_running_icon
            iconStatus = "running"
        else:
            cache = self.__class__.cached_done_icon
            ui = self.__class__.done_icon
            iconStatus = "done"
        # FIXME, always get triggered
        # if status == [] or iconStatus not in status :
        #     print("status is "+str(status)+ " or "+str(iconStatus)+" not in "+str(status))
        #     self.controller.setStatus([iconStatus])

        if cache is None:
            from PIL import Image, ImageTk
            abs_path = os.path.dirname(os.path.abspath(__file__))

            path = os.path.join(abs_path, "../../icon/"+ui)
            if iconStatus == "done":
                self.__class__.cached_done_icon = ImageTk.PhotoImage(
                    Image.open(path))
                return self.__class__.cached_done_icon
            elif iconStatus == "running":
                self.__class__.cached_running_icon = ImageTk.PhotoImage(
                    Image.open(path))
                return self.__class__.cached_running_icon
            else:
                self.__class__.cached_not_ready_icon = ImageTk.PhotoImage(
                    Image.open(path))
                return self.__class__.cached_not_ready_icon
        return cache

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
        
        super().__init__(appTw, appViewFrame, mainApp, controller)

    def clearWindow(self):
        self.form.clear()
        for widget in self.appliViewFrame.winfo_children():
            widget.destroy()
            
    def openModifyWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing Command
        """
        infos = self.controller.getCheckInstanceInfos()
        modelData = self.controller.getData()
        check_m = self.controller.getCheckItem()
        self._initContextualMenu()
        self.form.addFormHidden("parent", modelData.get("parent"))
        panel_top = self.form.addFormPanel(grid=True)
        panel_top.addFormLabel("Status", row=0, column=0)
        default_status = infos.get("status", "")
        if default_status == "":
            default_status = modelData.get("status", "")
        if default_status == "":
            default_status = "not done"
        panel_top.addFormCombo("Status", ["not done", "running","done"], default=default_status, row=0, column=1, pady=5)
        panel_top.addFormLabel("Description", row=1, column=0)
        panel_top.addFormText("Description", r"", default=check_m.description, width=60, height=5, state="disabled", row=1, column=1, pady=5)
        panel_top.addFormLabel("Notes", row=2, column=0)
        panel_top.addFormText("Notes", r"", default=modelData.get("notes", ""), width=60, height=5, row=2, column=1, pady=5)
        if "commands" in check_m.check_type:
            formTv = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5)
            formTv.addFormLabel("Commands associated", side=tk.LEFT)
            from PIL import ImageTk, Image

            self.buttonRunImage = ImageTk.PhotoImage(Image.open(Utils.getIconDir()+'execute.png'))

            tv_commands = []
            for command_name, status in infos.get("tools_status", {}).items():
                tv_commands.append([command_name, f'{status["done"]}/{status["total"]}'])
            if True==True:#if check_m.check_type == "manual_commands": #
                formCommands = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5, grid=True)
                dict_of_tools = infos.get("tools_not_done")
                lambdas = [self.launchToolCallbackLambda(iid) for iid in dict_of_tools.keys()]
                row=0
                for tool_iid, tool_string in dict_of_tools.items():
                    formCommands.addFormLabel(tool_string, row=row, column=0)
                    formCommands.addFormButton("Run", lambdas[row], row=row, column=1, image=self.buttonRunImage, style="icon.TButton")
                    row+=1
                    print(tool_string+":"+tool_iid)
            formTv.addFormTreevw(
                "Commands", ("Command names", "ratio completed"), tv_commands, height=5, width=40, pady=5, fill=tk.X, side=tk.RIGHT, doubleClickBinds=[None, None])

            #for command, status in infos.get("tools_status", {}).items():
        elif "script" in check_m.check_type:
            formTv = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5)
            formTv.addFormLabel("Script", side=tk.LEFT)
            self.textForm = formTv.addFormStr("Script", ".+", check_m.script)
            self.execute_icon = tk.PhotoImage(file = Utils.getIcon("execute.png"))
            self.edit_icon = tk.PhotoImage(file = Utils.getIcon("view_doc.png"))
            formTv.addFormButton("View", lambda _event: self.viewScript(check_m.script), image=self.edit_icon, style="icon.TButton")
            formTv.addFormButton("Exec", lambda _event: self.execScript(check_m.script), image=self.execute_icon, style="icon.TButton")
        self.completeModifyWindow(addTags=False)

    
    def launchToolCallbackLambda(self, tool_iid):
        return lambda event: self.launchToolCallback(tool_iid)
    
    def launchToolCallback(self, tool_iid):
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})
        self.mainApp.scanManager.launchTask(tool_m)

    def viewScript(self, script):
        ScriptManager.openScriptForUser(script)

    def execScript(self, script):
        ScriptManager.executeScript(script)
    

    def addInTreeview(self, parentNode=None, addChildren=True):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
        """
        if parentNode is None:
            parentNode = self.getParentNode()
        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}
        try:
            self.appliTw.insert(parentNode, "end", str(
                self.controller.getDbId()), text=str(self.controller.getModelRepr()), tags=self.controller.getTags(), image=self.getIcon())
        except tk.TclError:
            pass
        if addChildren:
            tools = self.controller.getTools()
            for tool in tools:
                tool_o = ToolController(Tool(tool))
                tool_vw = ToolView(
                    self.appliTw, self.appliViewFrame, self.mainApp, tool_o)
                tool_vw.addInTreeview(str(self.controller.getDbId()))
        if "hidden" in self.controller.getTags():
            self.hide()

    def getParentNode(self):
        """
        Return the id of the parent node in treeview.

        Returns:
            return the saved command_node node inside the Appli class.
        """
        parent = self.controller.getTarget()
        if parent is not None and parent != "":
            return parent
        return None

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


    def updateReceived(self):
        """Called when a command update is received by notification.
        Update the command treeview item (resulting in icon reloading)
        """
        try:
            self.appliTw.item(str(self.controller.getDbId()), text=str(
                self.controller.getModelRepr()), image=self.getIcon())
        except tk.TclError:
            print("WARNING: Update received for a non existing tool "+str(self.controller.getModelRepr()))
        super().updateReceived()

    def key(self):
        """Returns a key for sorting this node
        Returns:
            tuple, key to sort
        """
        return tuple([ord(c) for c in str(self.controller.getModelRepr()).lower()])
