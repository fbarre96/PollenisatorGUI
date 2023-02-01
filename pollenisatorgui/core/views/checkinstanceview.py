"""View for checkitem object. Handle node in treeview and present forms to user when interacted with."""

import tkinter.ttk as ttk
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.scriptmanager import ScriptManager
from pollenisatorgui.core.application.dialogs.ChildDialogRemoteInteraction import ChildDialogRemoteInteraction
from pollenisatorgui.core.controllers.toolcontroller import ToolController
from pollenisatorgui.core.views.toolview import ToolView
from pollenisatorgui.core.views.viewelement import ViewElement
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.models.tool import Tool
import pollenisatorgui.core.components.utils as utils


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

    def getIcon(self, check_infos=None):
        """
        Load the object icon in cache if it is not yet done, and returns it

        Return:
            Returns the icon representing this object.
        """
        if check_infos is None:
            check_infos = self.controller.getCheckInstanceInfos()
        modelData = self.controller.getData()
        status = check_infos.get("status", "")
        if status == "":
            status = modelData.get("status", "")
        if status == "":
            status = "todo"
        iconStatus = "todo"
        if "todo" in status: # order is important as "done" is not_done but not the other way
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
        self.clearWindow()
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
            default_status = "todo"
        panel_top.addFormCombo("Status", ["todo", "running","done"], default=default_status, row=0, column=1, pady=5)
        panel_top.addFormLabel("Description", row=1, column=0)
        panel_top.addFormText("Description", r"", default=check_m.description, width=60, height=5, state="disabled", row=1, column=1, pady=5)
        panel_top.addFormLabel("Notes", row=2, column=0)
        panel_top.addFormText("Notes", r"", default=modelData.get("notes", ""), width=60, height=5, row=2, column=1, pady=5)
        if "commands" in check_m.check_type:
            formTv = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5)
            from PIL import ImageTk, Image

            self.buttonExecuteImage = ImageTk.PhotoImage(Image.open(utils.getIconDir()+'execute.png'))
            self.buttonRunImage = ImageTk.PhotoImage(Image.open(utils.getIconDir()+'tab_terminal.png'))
            self.buttonDownloadImage = ImageTk.PhotoImage(Image.open(utils.getIconDir()+'download.png'))
            
            dict_of_tools_not_done = infos.get("tools_not_done")
            dict_of_tools_running = infos.get("tools_running")
            dict_of_tools_done = infos.get("tools_done")
            lambdas_not_done = [self.launchToolCallbackLambda(iid) for iid in dict_of_tools_not_done.keys()]
            lambdas_running = [self.peekToolCallbackLambda(iid) for iid in dict_of_tools_running.keys()]
            lambdas_done = [self.downloadToolCallbackLambda(iid) for iid in dict_of_tools_done.keys()]
            formCommands = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5, grid=True)
            row=0
            for tool_iid, tool_string in dict_of_tools_not_done.items():
                formCommands.addFormButton(tool_string, self.openToolDialog, row=row, column=0, style="link.TButton", infos={"iid":tool_iid})
                formCommands.addFormButton("Execute", lambdas_not_done[row], row=row, column=1, image=self.buttonExecuteImage, style="icon.TButton")
                row+=1
            formCommands = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5, grid=True)
            row=0
            for tool_iid, tool_string in dict_of_tools_running.items():
                formCommands.addFormButton(tool_string, self.openToolDialog, row=row, column=0, style="link.TButton", infos={"iid":tool_iid})
                formCommands.addFormButton("Peek", lambdas_running[row], row=row, column=1, image=self.buttonRunImage, style="icon.TButton")
                row+=1
            formCommands = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5)
            row=0
            for tool_iid, tool_data in dict_of_tools_done.items():
                tool_m = Tool(tool_data)
                tool_panel = formCommands.addFormPanel(side=tk.TOP, fill=tk.X, pady=0)
                tool_panel.addFormButton(tool_m.getDetailedString(), self.openToolDialog, side=tk.TOP, anchor=tk.W, style="link.TButton", infos={"iid":tool_iid})
                if tool_m.tags:
                    for tag in tool_m.tags:
                        registeredTags = Settings.getTags()
                        keys = list(registeredTags.keys())
                        column = 0
                        item_no = 0
                        
                        s = ttk.Style(self.mainApp)
                        color = registeredTags.get(tag, "white")
                        try: # CHECK IF COLOR IS VALID
                            ttk.Label(self.mainApp, background=color)
                        except tk.TclError as e:
                            #color incorrect
                            color = "white"
                        s.configure(""+color+".Default.TLabel", background=color, foreground="black", borderwidth=1, bordercolor="black")
                        tool_panel.addFormLabel(tag, text=tag, side="top", padx=1, pady=0, style=""+color+".Default.TLabel")
                        column += 1
                        item_no += 1
                        if column == 4:
                            column = 0
                        if column == 0:
                            tool_panel = tool_panel.addFormPanel(pady=0,side=tk.TOP, anchor=tk.W)
                tool_panel.addFormText(str(tool_iid)+"_notes", "", default=tool_m.notes, width=60, height=5, side=tk.LEFT)
                tool_panel.addFormButton("Download", lambdas_done[row], image=self.buttonDownloadImage, style="icon_white.TButton", side=tk.LEFT, anchor=tk.E)
                row+=1

            #for command, status in infos.get("tools_status", {}).items():
        elif "script" in check_m.check_type:
            formTv = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5)
            formTv.addFormLabel("Script", side=tk.LEFT)
            self.textForm = formTv.addFormStr("Script", ".+", check_m.script)
            self.execute_icon = tk.PhotoImage(file = utils.getIcon("execute.png"))
            self.edit_icon = tk.PhotoImage(file = utils.getIcon("view_doc.png"))
            formTv.addFormButton("View", lambda _event: self.viewScript(check_m.script), image=self.edit_icon, style="icon.TButton")
            formTv.addFormButton("Exec", lambda _event: self.execScript(check_m.script), image=self.execute_icon, style="icon.TButton")
        self.completeModifyWindow(addTags=False)

    
    def launchToolCallbackLambda(self, tool_iid):
        return lambda event: self.launchToolCallback(tool_iid)

    def peekToolCallbackLambda(self, tool_iid):
        return lambda event: self.peekToolCallback(tool_iid)

    def downloadToolCallbackLambda(self, tool_iid):
        return lambda event: self.downloadToolCallback(tool_iid)

    def openToolDialog(self, event, infos):
        tool_iid = infos.get("iid")
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})
        tool_vw = ToolView(self.appliTw, None, self.mainApp, ToolController(tool_m))
        tool_vw.openInDialog()
        self.openModifyWindow()

    
    def launchToolCallback(self, tool_iid):
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})
        self.mainApp.scanManager.launchTask(tool_m)
        self.openModifyWindow()

    def peekToolCallback(self, tool_iid):
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})
        dialog = ChildDialogRemoteInteraction(ToolController(tool_m))
        dialog.app.wait_window(dialog.app)
        

    def downloadToolCallback(self, tool_iid):
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})
        tool_vw = ToolView(self.appliTw, self.appliViewFrame, self.mainApp, ToolController(tool_m))
        tool_vw.downloadResultFile()
        

    def viewScript(self, script):
        ScriptManager.openScriptForUser(script)

    def execScript(self, script):
        data = self.controller.getData()
        ScriptManager.executeScript(script, data)
    

    def addInTreeview(self, parentNode=None, addChildren=True, detailed=False):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
        """
        if parentNode is None:
            parentNode = self.getParentNode()
        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}
        check_infos = self.controller.getCheckInstanceInfos()
        text = check_infos.get("repr", "unknown") if self.mainApp.settings.is_checklist_view() else str(self)
            
        try:
            self.appliTw.insert(parentNode, "end", str(
                self.controller.getDbId()), text=text, tags=self.controller.getTags(), image=self.getIcon(check_infos))
        except tk.TclError as e:
            pass
        # if addChildren:
        #     tools = self.controller.getTools()
        #     for tool in tools:
        #         tool_o = ToolController(Tool(tool))
        #         tool_vw = ToolView(
        #             self.appliTw, self.appliViewFrame, self.mainApp, tool_o)
        #         tool_vw.addInTreeview(str(self.controller.getDbId()))
    
        status = check_infos.get("status", "")
        if status == "":
            status = check_infos.get("status", "")
        if status == "":
            status = "todo"
    
        if "hidden" in self.controller.getTags() or (status != "todo" and self.mainApp.settings.is_show_only_todo()):
            self.hide()
        if self.mainApp.settings.is_show_only_manual() and self.controller.isAuto():
            self.hide()

    def getParentNode(self):
        """
        Return the id of the parent node in treeview.

        Returns:
            return the saved command_node node inside the Appli class.
        """
        if self.mainApp.settings.is_checklist_view():
            return str(self.controller.model.check_iid)
            
        else:
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
