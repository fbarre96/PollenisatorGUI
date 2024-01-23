"""View for user object. Handle node in treeview and present forms to user when interacted with."""

from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.views.viewelement import ViewElement
from tkinter import TclError
import tkinter as tk

class UserView(ViewElement):
    """View for user object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory.
    """

    icon = 'user.png'
    def openModifyWindow(self, **kwargs):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing User
        """
        self.form.clear()
        user_data = self.controller.getData()
        panel = self.form
        panel_info = panel.addFormPanel(grid=True)
        panel_info.addFormLabel("Domain")
        panel_info.addFormStr("Domain", "", user_data.get("domain", ""), status="readonly", row=0, column=1)
        panel_info.addFormLabel("Username", row=1)
        panel_info.addFormStr("Username", "", user_data.get("username", ""), status="readonly", row=1, column=1)
        panel_info.addFormLabel("Password", row=2)
        panel_info.addFormStr("Password", "", user_data.get("password", ""), status="readonly", row=2, column=1)
        panel.addFormLabel("Desc", text=f"Desc : {user_data.get('desc', '')}" , side="top")
        if user_data.get("infos", {}).get("secrets", []):
            panel.addFormLabel("Secrets", side="top")
            panel.addFormTreevw("Secrets", ("Secret", ""), [(s, "") for s in user_data.get("infos", {}).get("secrets", [])], side="top")
        groups = user_data.get('groups', []) 
        if groups is None:
            groups = []
        panel.addFormTreevw("Groups", ("Group",), [ [x] for x in groups], side="top")
        self.completeModifyWindow(editable=False)
        
    def openInsertWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to insert a new User
        """
        # modelData = self.controller.getData()
        # top_panel = self.form.addFormPanel(grid=True)
        # top_panel.addFormLabel("Start date")
        # top_panel.addFormDate("Start date", self.mainApp, "01/01/2000 00:00:00", column=1)
        # top_panel.addFormLabel("End date", row=1)
        # top_panel.addFormDate(
        #     "End date", self.mainApp, "31/12/2099 00:00:00", row=1, column=1)
        # top_panel.addFormHelper(
        #     "Auto scan will only launch if current time fits this user", row=1, column=2)
        # # added in getEmptyModel
        # self.form.addFormHidden("waveName", modelData["wave"])

        # self.completeInsertWindow()
        raise NotImplementedError("UserView.openInsertWindow not implemented")

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
        data = self.controller.getData()
        if parentNode is None:
            parentNode = data.get("domain")+" Users"
        try:
            self.appliTw.insert(
                "", 0, parentNode, text=data.get("domain")+" Users", image=self.getClassIcon())
        except TclError as e:  #  trigger if tools list node already exist
            pass
        try:
            self.appliTw.insert(parentNode, "end", str(
                self.controller.getDbId()), text=str(self.controller.getModelRepr()), tags=tags, image=self.getClassIcon())
        except TclError as e:
            pass
        if "hidden" in tags:
            self.hide("tags")
        if self.mainApp.settings.is_checklist_view():
            self.hide("checklist_view")

   