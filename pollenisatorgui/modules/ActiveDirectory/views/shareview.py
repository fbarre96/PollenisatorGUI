"""View for share object. Handle node in treeview and present forms to user when interacted with."""

from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.views.viewelement import ViewElement
from tkinter import TclError
import tkinter as tk

class ShareView(ViewElement):
    """View for share object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory.
    """

    icon = 'share.png'
    def openModifyWindow(self, **kwargs):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing Share
        """
        self.form.clear()
        share_data = self.controller.getData()
        panel = self.form
        panel_info = panel.addFormPanel(grid=True)
        panel_info.addFormLabel("IP")
        panel_info.addFormStr("IP", "", share_data.get("ip", ""), status="readonly", row=0, column=1)
        panel_info.addFormLabel("Share", row=1)
        panel_info.addFormStr("Share", "", share_data.get("share", ""), status="readonly", row=1, column=1)
        files = share_data.get('files', []) 
        if files is None:
            files = []
        defaults = []
        for file in files:
            defaults.append([file["path"],file["flagged"], file["size"]])
        self.tree = panel.addFormTreevw("Files", ("Path","Flagged","Size"), default_values=defaults, side="top")
        contextual_menus = {}
        for module in self.mainApp.modules:
            if module.get("name", "") == "Active Directory":
                contextual_menus |= module["object"].getAdditionalContextualCommands("share", self.tree, self)
        
        self.completeModifyWindow(editable=False)
        for cmdname, cmd in contextual_menus.items():
            self.tree.addContextMenuCommand(cmdname, cmd)
        
    def openInsertWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to insert a new Share
        """
        # modelData = self.controller.getData()
        # top_panel = self.form.addFormPanel(grid=True)
        # top_panel.addFormLabel("Start date")
        # top_panel.addFormDate("Start date", self.mainApp, "01/01/2000 00:00:00", column=1)
        # top_panel.addFormLabel("End date", row=1)
        # top_panel.addFormDate(
        #     "End date", self.mainApp, "31/12/2099 00:00:00", row=1, column=1)
        # top_panel.addFormHelper(
        #     "Auto scan will only launch if current time fits this share", row=1, column=2)
        # # added in getEmptyModel
        # self.form.addFormHidden("waveName", modelData["wave"])

        # self.completeInsertWindow()
        raise NotImplementedError("ShareView.openInsertWindow not implemented")

    def getAdditionalContextualCommands(self):
        return {}
       
    
    @classmethod
    def DbToTreeviewListId(cls, parent_db_id):
        """Converts a mongo Id to a unique string identifying a list of shares given its parent
        Args:
            parent_db_id: the parent node mongo ID
        Returns:
            A string that should be unique to describe the parent list of defect node
        """
        return str(parent_db_id)+"|Shares"
    
    @classmethod
    def treeviewListIdToDb(cls, treeviewId):
        """Extract from the unique string identifying a list of defects the parent db ID
        Args:
            treeviewId: the treeview node id of a list of defects node
        Returns:
            the parent object mongo id as string
        """
        return str(treeviewId).split("|")[0]

    def addInTreeview(self, parentNode=None, **kwargs):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
            _addChildren: not used here
        """

        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}
        tags = self.controller.getTags()
        parentDbId = parentNode
        if parentNode is None:
            parentNode = self.getParentNode()
        elif "shares" not in parentNode:
            parentNode = self.__class__.DbToTreeviewListId(parentDbId)
        try:
            self.appliTw.insert(
                self.controller.getParentId(), 0, parentNode, text="Shares", image=self.getClassIcon())
        except TclError as e:  #  trigger if tools list node already exist
            pass
        try:
            self.appliTw.insert(parentNode, "end", str(
                self.controller.getDbId()), text=str(self.controller.getModelRepr()), tags=tags, image=self.getClassIcon())
        except:
            pass
        if "hidden" in tags:
            self.hide("tags")
        if self.mainApp.settings.is_checklist_view():
            self.hide("checklist_view")

   