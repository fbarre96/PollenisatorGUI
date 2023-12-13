"""View for scope object. Handle node in treeview and present forms to user when interacted with."""

from pollenisatorgui.core.controllers.checkinstancecontroller import CheckInstanceController
from pollenisatorgui.core.views.checkinstanceview import CheckInstanceView
from pollenisatorgui.core.views.ipview import IpView
from pollenisatorgui.core.views.multiplescopeview import MultipleScopeView
from pollenisatorgui.core.controllers.scopecontroller import ScopeController
from pollenisatorgui.core.models.scope import Scope
from pollenisatorgui.core.views.viewelement import ViewElement
from tkinter import TclError

class ScopeView(ViewElement):
    """View for port object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory"""

    icon = 'scope.png'

    def openModifyWindow(self, **kwargs):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing Scope
        """
        self.form.clear()
        modelData = self.controller.getData()
        top_panel = self.form.addFormPanel(grid=True)
        top_panel.addFormLabel("Scope", column=0)
        top_panel.addFormStr("Scope", '', modelData["scope"], None, column=1, state="readonly")
        notes = modelData.get("notes", "")
        top_panel = self.form.addFormPanel(grid=True)
        top_panel.addFormLabel("Notes")
        self.form.addFormText("Notes", r"", notes, None, side="top")
        self.completeModifyWindow()

    
    def addChildrenBaseNodes(self, newNode):
        """
        Add to the given node from a treeview the mandatory childrens.
        For a Scope it is the tools parent node and the ips parent node

        Args:
            newNode: the newly created node we want to add children to.
        """

        return self.appliTw.insert(newNode, "end", IpView.DbToTreeviewListId(newNode), text="IPs", image=IpView.getClassIcon())
    
    def openInsertWindow(self):
        view = MultipleScopeView(self.appliTw, self.appliViewFrame, self.mainApp, self.controller)
        view.openInsertWindow()
    
    def getAdditionalContextualCommands(self):
        return {"Insert Scopes":self.openInsertWindow}

    def addInTreeview(self, parentNode=None, **kwargs):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
            addChildren: If False, skip the tool insert. Useful when displaying search results
        """
        addChildren = kwargs.get("addChildren", True)
        self.appliTw.views[str(self.controller.getDbId())] = {"view":self}

        parentDbId = parentNode
        if parentNode is None:
            parentNode = self.getParentNode()
        elif parentNode == "":
            parentNode = ""
        elif 'scopes' not in parentNode:
            parentNode = ScopeView.DbToTreeviewListId(parentDbId)
        if parentNode != "" and parentNode is not None and kwargs.get("insert_parents", True):
            try:
                parentNode = self.appliTw.insert(
                    self.controller.getParentId(), 0, parentNode, text="Scopes", image=self.getClassIcon())
            except TclError as e:  #  trigger if tools list node already exist
                pass
        try:
            node = self.appliTw.insert(parentNode, "end", str(self.controller.getDbId()), text=str(self.controller.getModelRepr()), tags=self.controller.getTags(), image=self.getClassIcon())
        except TclError as e:
            pass
        if addChildren:
            self._insertChildren()
        elif self.appliTw.lazyload and not self.mainApp.searchMode:
            try:
                self.appliTw.insert(self.controller.getDbId(), "end", str(self.controller.getDbId()+"|<Empty>"), text="<Empty>")
            except TclError as e:
                pass
        if self.mainApp.settings.is_checklist_view():
            self.hide("checklist_view")
        if "hidden" in self.controller.getTags():
            self.hide("tags")

    def _insertChildren(self):
        checks = self.controller.getChecks()
        for check in checks:
            check_o = CheckInstanceController(check)
            check_vw = CheckInstanceView(self.appliTw, self.appliViewFrame, self.mainApp, check_o)
            check_vw.addInTreeview(str(self.controller.getDbId()))

    @classmethod
    def treeviewListIdToDb(cls, treeview_id):
        """Extract from the unique string identifying a list of scopes the parent db ID
        Args:
            treeview_id: the treeview node id of a list of scopes node
        Returns:
            the parent object mongo id as string
        """
        return str(treeview_id).split("|")[1]

    @classmethod
    def DbToTreeviewListId(cls, parent_db_id):
        """Converts a mongo Id to a unique string identifying a list of scopes given its parent
        Args:
            parent_db_id: the parent node mongo ID
        Returns:
            A string that should be unique to describe the parent list of scope node
        """
        return "scopes|"+str(parent_db_id)

    def split_ip(self):
        """Split a IP address given as string into a 5-tuple of integers.
        Returns:
            If network IP Tuple of 5 integers values representing the 4 parts of an ipv4 string + the /mask integer
            Otherwise returns self"""
        modelData = self.controller.getData()
        try:
            ret = tuple(int(part) for part in modelData["scope"].split('.'))
            ret = ret + tuple(int(modelData["scope"].split('/')[1]))
        except ValueError:
            ret = tuple(str(part) for part in modelData["scope"].split('.'))
        return ret

    def insertReceived(self):
        """Called when a scope insertion is received by notification.
        Tells the parent wave to update itself
        """
        if self.controller.model is None:
            return
        parentId = self.controller.getParentId()
        parentView = self.appliTw.views[str(parentId)]["view"]
        parentView.updateReceived(None, None)
        super().insertReceived()

    def key(self):
        """Returns a key for sorting this node
        Returns:
            Tuple of 5 integer valus representing the scope perimeter if network ip or self directly
        """
        return self.split_ip()
