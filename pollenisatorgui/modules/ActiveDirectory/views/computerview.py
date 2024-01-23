"""View for computer object. Handle node in treeview and present forms to user when interacted with."""

from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.views.viewelement import ViewElement
from tkinter import TclError
import tkinter as tk

class ComputerView(ViewElement):
    """View for computer object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory.
    """

    icon = 'computer.png'
    def openModifyWindow(self, **kwargs):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing Computer
        """
        self.form.clear()
        computer_data = self.controller.getData()
        panel = self.form
        panel_info = panel.addFormPanel(grid=True)
        panel_info.addFormLabel("IP")
        panel_info.addFormStr("IP", "", computer_data.get("ip", ""), status="readonly", row=0, column=1)
        panel_info.addFormLabel("Name", column=2)
        panel_info.addFormStr("Name", "", computer_data.get("name", ""), status="readonly", column=3)
        row = 1
        for info_name, val in computer_data.get("infos", {}).items():
            panel_info.addFormLabel(info_name, row=row)
            panel_info.addFormStr(info_name, "", val, status="readonly", row=row, column=1)
            row += 1
        apiclient = APIClient.getInstance()
        res = apiclient.getComputerUsers(str(computer_data["_id"]))
        if res is  None:
            res = {}
        users_data = [(d["domain"], d["username"], d["password"]) for d in res.get("users", [])]
        admins_data = [(d["domain"], d["username"], d["password"]) for d in res.get("admins",[])]
        panel.addFormLabel("Users", side="top")
        panel.addFormTreevw("Users", ("Domain", "Username", "Password"), users_data, fill=tk.X, height=2, max_height=10, side="top")
        
        panel.addFormLabel("Admins", side="top")
        panel.addFormTreevw("Admins", ("Domain", "Username", "Password"), admins_data,  fill=tk.X, height=2, max_height=10, side="top")
        if computer_data.get("secrets", []):
            panel.addFormLabel("Secrets", side="top")
            panel.addFormTreevw("Secrets", ("Secret", ""), [(s, "") for s in computer_data.get("infos", {}).get("secrets", [])], side="top")
        ntds = computer_data.get("ntds", [])
        if ntds:
            panel.addFormLabel("NTDS", side="top")
            panel.addFormText("NTDS", "", "\n".join(ntds), side="top")
        self.completeModifyWindow(editable=False)
        
    def openInsertWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to insert a new Computer
        """
        # modelData = self.controller.getData()
        # top_panel = self.form.addFormPanel(grid=True)
        # top_panel.addFormLabel("Start date")
        # top_panel.addFormDate("Start date", self.mainApp, "01/01/2000 00:00:00", column=1)
        # top_panel.addFormLabel("End date", row=1)
        # top_panel.addFormDate(
        #     "End date", self.mainApp, "31/12/2099 00:00:00", row=1, column=1)
        # top_panel.addFormHelper(
        #     "Auto scan will only launch if current time fits this computer", row=1, column=2)
        # # added in getEmptyModel
        # self.form.addFormHidden("waveName", modelData["wave"])

        # self.completeInsertWindow()
        raise NotImplementedError("ComputerView.openInsertWindow not implemented")

    def getAdditionalContextualCommands(self):
        return {}

    def addInTreeview(self, parentNode=None, **kwargs):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
            _addChildren: not used here
        """

        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}
        tags = self.controller.getTags()
        if parentNode is None:
            parentNode = self.getParentNode()
        try:
            self.appliTw.insert(parentNode, "end", str(
                self.controller.getDbId()), text=str(self.controller.getModelRepr()), tags=tags, image=self.getClassIcon())
        except:
            pass
        if "hidden" in tags:
            self.hide("tags")
        if self.mainApp.settings.is_checklist_view():
            self.hide("checklist_view")

   