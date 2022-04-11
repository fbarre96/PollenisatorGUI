"""View for command group object. Handle node in treeview and present forms to user when interacted with."""

from bson import ObjectId
from pollenisatorgui.core.Views.ViewElement import ViewElement
import pollenisatorgui.core.Models.Command as Command
import tkinter as tk
from pollenisatorgui.core.Components.apiclient import APIClient


class CommandGroupView(ViewElement):
    """
    View for command group object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory.
    """
    icon = 'group_command.png'

    def openModifyWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing CommandGroup
        """
        modelData = self.controller.getData()
        self.form.addFormHidden("indb", modelData["indb"])
        panel = self.form.addFormPanel(grid=True)
        panel.addFormLabel("Name")
        panel.addFormStr("Name", r".*\S.*", modelData["name"], column=1)
        panel = self.form.addFormPanel()
        apiclient = APIClient.getInstance()
        if modelData["indb"] == "pollenisator":
            commands = apiclient.findCommand({"owner":modelData["owner"]})
        else:
            commands = apiclient.find("commands", {"owner":modelData["owner"]}, True)
        commands_names = []
        defaults = []
        comms_values = []
        comms_as_oid = [ObjectId(x) for x in modelData["commands"]]
        for command_dict in commands:
            c = Command.Command(command_dict)
            commands_names.append(str(c))
            comms_values.append(str(c.getId()))
            if ObjectId(c.getId()) in comms_as_oid:
                defaults.append(str(c))
        panel.addFormChecklist(
            "Commands", commands_names, defaults, values=comms_values, side=tk.LEFT)
        panel = self.form.addFormPanel(grid=True)
        panel.addFormLabel("Delay")
        panel.addFormStr(
            "Delay", r"\d+", modelData["sleep_between"], width=5, column=1)
        panel.addFormHelper(
            "Delay in-between two launch of each command of ths group (in seconds).\nIf a command is in two groups, the highest delay will be used", column=2)
        panel.addFormLabel("Shared threads", row=1)
        panel.addFormStr("Shared threads", r"\d+",
                         modelData["max_thread"], width=2, row=1, column=1)
        panel.addFormHelper(
            "Number of parallel execution allowed for every command in this group at any given moment.", row=1, column=2)
        self.completeModifyWindow()

    def openInsertWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to insert a new CommandGroup
        """
        modelData = self.controller.getData()
        self.form.addFormHidden("indb", modelData["indb"])
        self.form.addFormHidden("owner", modelData.get("owner", None))
        panel = self.form.addFormPanel(grid=True)
        panel.addFormLabel("Name")
        panel.addFormStr("Name", r".*\S.*", "", column=1)
        panel = self.form.addFormPanel()
        apiclient = APIClient.getInstance()
        if modelData["indb"] == "pollenisator":
            commands = apiclient.findCommand({"owner":modelData["owner"]})
        else:
            commands = apiclient.find("commands", {"owner":modelData["owner"]}, True)
        commands_names = []
        comms_values = []
        for command_dict in commands:
            c = Command.Command(command_dict)
            commands_names.append(str(c))
            comms_values.append(str(c.getId()))
        panel.addFormChecklist("Commands", commands_names, [], values=comms_values,side=tk.LEFT)
        panel = self.form.addFormPanel(grid=True)
        panel.addFormLabel("Delay")
        panel.addFormStr("Delay", r"\d+", "0", width=5, column=1)
        panel.addFormHelper(
            "Delay in-between two launch of each command of ths group (in seconds).\nIf a command is in two groups, the highest delay will be used", column=2)
        panel.addFormLabel("Shared threads", row=1)
        panel.addFormStr("Shared threads", r"\d+",
                         "1", width=2, row=1, column=1)
        panel.addFormHelper(
            "Number of parallel execution allowed for every command in this group at any given moment.", row=1, column=2)
        self.completeInsertWindow()

    def addInTreeview(self, parentNode=None):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: not used
        """
        parentNode = self.getParentNode()
        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}
        self.appliTw.insert(parentNode, "end", str(self.controller.getDbId()), text=str(
            self.controller.getModelRepr()), tags=self.controller.getTags(), image=self.getClassIcon())
        if "hidden" in self.controller.getTags():
            self.hide()

    def getParentNode(self):
        """
        Return the id of the parent node in treeview.

        Returns:
            return the saved group_command_node node inside the Appli class.
        """
        apiclient = APIClient.getInstance()
        if self.controller.model.indb == "pollenisator":
            if self.controller.isMyCommandGroup():
                return self.appliTw.my_group_command_node
            elif self.controller.isWorkerCommandGroup():
                return self.appliTw.worker_group_command_node
        else:
            if self.controller.isMyCommandGroup():
                return self.appliTw.my_group_command_node
            elif self.controller.isWorkerCommandGroup():
                return self.appliTw.worker_group_command_node
        return self.appliTw.group_command_node
