"""View for tool object. Handle node in treeview and present forms to user when interacted with."""

from pollenisatorgui.core.application.dialogs.ChildDialogGenericView import ChildDialogGenericView
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.views.viewelement import ViewElement
from pollenisatorgui.core.components.apiclient import APIClient
import tkinter.messagebox
import tkinter as tk
from tkinter import TclError
from pollenisatorgui.core.views.defectview import DefectView
from pollenisatorgui.core.models.defect import Defect
from pollenisatorgui.core.controllers.defectcontroller import DefectController
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.application.dialogs.ChildDialogInfo import ChildDialogInfo
from pollenisatorgui.core.application.dialogs.ChildDialogRemoteInteraction import ChildDialogRemoteInteraction
import pollenisatorgui.core.components.utils as utils
from bson import ObjectId, errors
from customtkinter import *
import os
import json


class ToolView(ViewElement):
    """View for tool object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory
        done_icon: icon filename for done tools
        ready_icon: icon filename for ready tools
        running_icon: icon filename for running tools
        not_ready_icon: icon filename for not ready tools
        cached_icon: a cached loaded PIL image icon of ToolView.icon. Starts as None.
        cached_done_icon: a cached loaded PIL image icon of ToolView.done_icon. Starts as None.
        cached_ready_icon: a cached loaded PIL image icon of ToolView.ready_icon. Starts as None.
        cached_running_icon: a cached loaded PIL image icon of ToolView.running_icon. Starts as None.
        cached_not_ready_icon: a cached loaded PIL image icon of ToolView.not_ready_icon. Starts as None.
        """

    done_icon = 'done_tool.png'
    error_icon = 'error_tool.png'
    ready_icon = 'waiting.png'
    running_icon = 'running.png'
    not_ready_icon = 'cross.png'
    icon = 'tool.png'


    cached_icon = None
    cached_done_icon = None
    cached_ready_icon = None
    cached_running_icon = None
    cached_not_ready_icon = None
    cached_error_icon = None

    def getIcon(self):
        """
        Load the object icon in cache if it is not yet done, and returns it

        Return:
            Returns the icon representing this object.
        """
        status = self.controller.getStatus()
        iconStatus = "ready"
        if "done" in status:
            cache = self.__class__.cached_done_icon
            ui = self.__class__.done_icon
            iconStatus = "done"
        elif "running" in status:
            ui = self.__class__.running_icon
            cache = self.__class__.cached_running_icon
            iconStatus = "running"
        elif "error" in status or "timedout" in status:
            cache = self.__class__.cached_error_icon
            ui = self.__class__.error_icon
            iconStatus = "error"
        elif "OOS" not in status and "OOT" not in status:
            ui = self.__class__.ready_icon
            cache = self.__class__.cached_ready_icon
            iconStatus = "ready"
        else:
            ui = self.__class__.not_ready_icon
            cache = self.__class__.cached_not_ready_icon
        # FIXME, always get triggered
        # if status == [] or iconStatus not in status :
        #     print("status is "+str(status)+ " or "+str(iconStatus)+" not in "+str(status))
        #     self.controller.setStatus([iconStatus])

        if cache is None:
            from PIL import Image, ImageTk
            path = utils.getIcon(ui)
            if iconStatus == "done":
                self.__class__.cached_done_icon = ImageTk.PhotoImage(
                    Image.open(path))
                return self.__class__.cached_done_icon
            elif iconStatus == "error":
                self.__class__.cached_error_icon = ImageTk.PhotoImage(
                    Image.open(path))
                return self.__class__.cached_error_icon
            elif iconStatus == "running":
                self.__class__.cached_running_icon = ImageTk.PhotoImage(
                    Image.open(path))
                return self.__class__.cached_running_icon
            elif iconStatus == "ready":
                self.__class__.cached_ready_icon = ImageTk.PhotoImage(
                    Image.open(path))
                return self.__class__.cached_ready_icon
            else:
                self.__class__.cached_not_ready_icon = ImageTk.PhotoImage(
                    Image.open(path))
                return self.__class__.cached_not_ready_icon
        return cache

    

    def openModifyWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing Tool
        """
        modelData = self.controller.getData()
        top_panel = self.form.addFormPanel(grid=True)
        top_panel.addFormLabel("Name", modelData["name"])
        dates_panel = self.form.addFormPanel(grid=True)
        dates_panel.addFormLabel("Start date")
        dates_panel.addFormDate(
            "Start date", self.mainApp, modelData["dated"], column=1)
        dates_panel.addFormLabel("End date", row=1)
        dates_panel.addFormDate(
            "End date", self.mainApp, modelData["datef"], row=1, column=1)
        dates_panel.addFormLabel("Scanner", row=2)
        dates_panel.addFormStr(
            "Scanner", r"", modelData["scanner_ip"], row=2, column=1)
        dates_panel.addFormLabel("Command executed", row=3)
        dates_panel.addFormStr("Command executed", "", modelData.get("infos", {}).get("cmdline",""), row=3, column=1)
        notes = modelData.get("notes", "")
        top_panel = self.form.addFormPanel()
        top_panel.addFormLabel("Notes", side="top")
        top_panel.addFormText("Notes", r"", notes, None, side="top")
        top_panel.addFormLabel("Infos", side="left")
        top_panel.addFormText("Infos", utils.is_json, json.dumps(modelData["infos"], indent=4), height=100,  side="left", fill="both")
        actions_panel = self.form.addFormPanel()
        apiclient = APIClient.getInstance()
        datamanager = DataManager.getInstance()
        try:
            command_d = datamanager.get("commands", modelData["command_iid"])
            if command_d is not None: # command not registered, I.E import
                workers = apiclient.getWorkers({"pentest":apiclient.getCurrentPentest(), "known_commands":command_d.bin_path})
                workers = [x["name"] for x in workers]
                hasWorkers = len(workers)
            #Ready is legacy, OOS and/or OOT should be used
            if ("ready" in self.controller.getStatus() or "error" in self.controller.getStatus() or "timedout" in self.controller.getStatus()) or len(self.controller.getStatus()) == 0:
                if apiclient.getUser() in command_d.owners:
                    actions_panel.addFormButton(
                        "Local launch", self.localLaunchCallback, side="right")
                if any(x in command_d.owners for x in workers):
                    actions_panel.addFormButton(
                        "Run on worker", self.launchCallback, side="right")
                elif apiclient.getUser() not in command_d.owners:
                    actions_panel.addFormLabel(
                        "Info", "Tool is ready", side="right")
            elif "OOS" in self.controller.getStatus() or "OOT" in self.controller.getStatus():
                actions_panel.addFormButton(
                    "Local launch", self.localLaunchCallback, side="right")
                if hasWorkers:
                    actions_panel.addFormButton(
                        "Run on worker", self.launchCallback, side="right")
                else:
                    actions_panel.addFormLabel(
                        "Info", "Tool is ready but no worker found", side="right")
            elif "running" in self.controller.getStatus():
                actions_panel.addFormButton(
                    "Stop", self.stopCallback, side="right")
                actions_panel.addFormButton(
                    "Remote Interaction", self.remoteInteraction, side="right")
            elif "done" in self.controller.getStatus():
                actions_panel.addFormButton(
                    "Download result file", self.downloadResultFile, side="right")
                try:
                    mod = utils.loadPlugin(self.controller.model.getCommand()["plugin"])
                    pluginActions = mod.getActions(self.controller.model)
                except KeyError:  # Happens when parsed an existing file.:
                    pluginActions = None
                except Exception:
                    pluginActions = None
                if pluginActions is not None:
                    for pluginAction in pluginActions:
                        actions_panel.addFormButton(
                            pluginAction, pluginActions[pluginAction], side="right")
                    if command_d is not None:
                        actions_panel.addFormButton(
                            "Reset", self.resetCallback, side="right")
        except errors.InvalidId:
            pass

        defect_panel = self.form.addFormPanel(grid=True)
        defect_panel.addFormButton("Create defect", self.createDefectCallback)
        defect_panel.addFormButton("Show associated command", self.showAssociatedCommand, column=1)

        self.completeModifyWindow()

    def addInTreeview(self, parentNode=None, _addChildren=True):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
            _addChildren: not used for tools
        """
        mustHide = False
        if parentNode is None:
            mustHide = True 
            parentNode = self.controller.getParentId()

        nodeText = str(self.controller.getModelRepr())
        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}
        try:
            self.appliTw.insert(parentNode, "end", str(
                self.controller.getDbId()), text=nodeText, tags=self.controller.getTags(), image=self.getIcon())
        except tk.TclError:
            pass
        self.appliTw.sort(parentNode)
        if self.mainApp.settings.is_checklist_view():
            self.hide("checklist_view")
        if "hidden" in self.controller.getTags() or mustHide:
            self.hide("tags")

    def downloadResultFile(self, _event=None):
        """Callback for tool click 
        Download the tool result file and asks the user if he or she wants to open it. 
        If OK, tries to open it
        Args:
            _event: not used 
        """
        apiclient = APIClient.getInstance()
        dialog = ChildDialogInfo(
            self.appliViewFrame, "Download Started", "Downloading...")
        dialog.show()
        abs_path = os.path.dirname(os.path.abspath(__file__))
        outputDir = os.path.join(abs_path, "../../results")
        path = self.controller.getOutputDir(apiclient.getCurrentPentest())
        path = apiclient.getResult(self.controller.getDbId(), os.path.join(outputDir,path))
        dialog.destroy()
        if path is not None:
            if os.path.isfile(path):
                dialog = ChildDialogQuestion(self.appliViewFrame, "Download completed",
                                            "The file has been downloaded.\n Would you like to open it?", answers=["Open", "Cancel"])
                self.appliViewFrame.wait_window(dialog.app)
                if dialog.rvalue == "Open":
                    utils.openPathForUser(path)
                    return
                else:
                    return
            path = None
        if path is None:
            tkinter.messagebox.showerror(
                "Download failed", "the file does not exist on sftp server")

    def createDefectCallback(self, _event=None):
        """Callback for tool click 
        Creates an empty defect view and open it's insert window with notes = tools notes.
        """
        modelData = self.controller.getData()
        toExport = modelData["notes"]
        for widget in self.appliViewFrame.winfo_children():
            widget.destroy()
        dv = DefectView(self.appliTw, self.appliViewFrame,
                        self.mainApp, DefectController(Defect(modelData)))
        dv.openInsertWindow(toExport)

    def showAssociatedCommand(self, _event=None):
        if self.appliTw is not None:
            self.appliTw.showItem(self.controller.getData()["command_iid"])
            

    def localLaunchCallback(self, _event=None):
        """
        Callback for the launch tool button. Will launch it on localhost pseudo 'worker'. 

        Args:
            event: Automatically generated with a button Callback, not used.
        """
        self.mainApp.scanManager.launchTask(self.controller.model,)
       
        self.form.clear()
        for widget in self.appliViewFrame.winfo_children():
            widget.destroy()
        self.openModifyWindow()

    def safeLaunchCallback(self, _event=None):
        """
        Callback for the launch tool button. Will queue this tool to a worker. 
        Args:
            event: Automatically generated with a button Callback, not used.
        Returns:
            None if failed. 
        """
        apiclient = APIClient.getInstance()
        return apiclient.sendLaunchTask(self.controller.model.getId()) is not None

    def launchCallback(self, _event=None):
        """
        Callback for the launch tool button. Will queue this tool to a worker. 
        Will try to launch respecting limits first. If it does not work, it will asks the user to force launch.

        Args:
            _event: Automatically generated with a button Callback, not used.
        """
        res = self.safeLaunchCallback()
        if not res:
            dialog = ChildDialogQuestion(self.appliViewFrame,
                                         "Safe queue failed", "This tool cannot be launched because no worker add space for its thread.\nDo you want to launch it anyway?")
            self.appliViewFrame.wait_window(dialog.app)
            answer = dialog.rvalue
            if answer == "Yes":
                apiclient = APIClient.getInstance()
                apiclient.sendLaunchTask(self.controller.model.getId(),  False)
        if res:
            self.form.clear()
            for widget in self.appliViewFrame.winfo_children():
                widget.destroy()
            self.openModifyWindow()

    def remoteInteraction(self, _event=None):
        dialog = ChildDialogRemoteInteraction(self.mainApp, self.controller, self.mainApp.scanManager)
        dialog.app.wait_window(dialog.app)
        
    def stopCallback(self, _event=None):
        """
        Callback for the launch tool stop button. Will stop this task. 

        Args:
            _event: Automatically generated with a button Callback, not used.
        """
        apiclient = APIClient.getInstance()
        success = False
        success_local = self.mainApp.scanManager.stopTask(self.controller.model.getId())
        if success_local:
            apiclient.sendStopTask(self.controller.model.getId(), True) # send reset tool 
            success = True
        else:
            success_distant = apiclient.sendStopTask(self.controller.model.getId())
            delete_anyway = False
            if success_distant != True: # it can be a tuple so this check is invalid if False and Tuple
                delete_anyway = tkinter.messagebox.askyesno(
                    "Stop failed", """This tool cannot be stopped because its trace has been lost (The application has been restarted and the tool is still not finished).\n
                        Reset tool anyway?""")
            if delete_anyway:
                success = apiclient.sendStopTask(self.controller.model.getId(), True)
        if success:
            self.form.clear()
            for widget in self.appliViewFrame.winfo_children():
                widget.destroy()
            self.openModifyWindow()

    def resetCallback(self, _event=None):
        """
        Callback for the reset tool stop button. Will reset the tool to a ready state. 

        Args:
            event: Automatically generated with a button Callback, not used.
        """
        self.controller.markAsNotDone()
        self.form.clear()
        for widget in self.appliViewFrame.winfo_children():
            widget.destroy()
        self.openModifyWindow()

    @classmethod
    def DbToTreeviewListId(cls, parent_db_id):
        """Converts a mongo Id to a unique string identifying a list of tools given its parent
        Args:
            parent_db_id: the parent node mongo ID
        Returns:
            A string that should be unique to describe the parent list of tool node
        """
        return str(parent_db_id)

    @classmethod
    def treeviewListIdToDb(cls, treeview_id):
        """Extract from the unique string identifying a list of tools the parent db ID
        Args:
            treeview_id: the treeview node id of a list of tools node
        Returns:
            the parent object mongo id as string
        """
        return str(treeview_id)

    def updateReceived(self):
        """Called when a tool update is received by notification.
        Update the tool treeview item (resulting in icon reloading)
        """
        try:
            self.appliTw.item(str(self.controller.getDbId()), text=str(
                self.controller.getModelRepr()), image=self.getIcon())
        except tk.TclError:
            print("WARNING: Update received for a non existing tool "+str(self.controller.getModelRepr()))
        super().updateReceived()
