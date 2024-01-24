"""View for wavr object. Handle node in treeview and present forms to user when interacted with."""
import tkinter as tk
from pollenisatorgui.core.controllers.checkinstancecontroller import CheckInstanceController
from pollenisatorgui.core.models.checkinstance import CheckInstance
from pollenisatorgui.core.views.checkinstanceview import CheckInstanceView

from pollenisatorgui.core.views.viewelement import ViewElement
from pollenisatorgui.core.models.command import Command
from pollenisatorgui.core.models.interval import Interval
from pollenisatorgui.core.views.intervalview import IntervalView
from pollenisatorgui.core.models.scope import Scope
from pollenisatorgui.core.views.scopeview import ScopeView
from pollenisatorgui.core.views.toolview import ToolView
from pollenisatorgui.core.controllers.intervalcontroller import IntervalController
from pollenisatorgui.core.controllers.scopecontroller import ScopeController
from pollenisatorgui.core.controllers.toolcontroller import ToolController
from pollenisatorgui.core.components.apiclient import APIClient

from bson import ObjectId

class WaveView(ViewElement):
    """View for wavr object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory"""

    icon = 'wave.png'

    def openModifyWindow(self, **kwargs):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing Wave
        """
        self.form.clear()
        modelData = self.controller.getData()
        top_panel = self.form.addFormPanel(grid=True)
        top_panel.addFormLabel("Scope options", modelData["wave"])
        # self.form.addFormHelper(
        #     "If you select a previously unselected command,\n it will be added to every object of its level.\nIf you unselect a previously selected command,\n it will remove only tools that are not already done.")
        # commands = Command.getList(None, APIClient.getInstance().getCurrentPentest())
        # commands_names = []
        # defaults = []
        # comms_values = []
        # for c in commands:
        #     commands_names.append(str(c))
        #     comms_values.append(c.getId())
        #     if str(c.getId()) in modelData["wave_commands"]:
        #         defaults.append(str(c))
        # self.form.addFormChecklist(
        #     "Commands", commands_names, defaults, values=comms_values)
        self.completeModifyWindow()

    def openInsertWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to insert a new Wave
        """
        top_panel = self.form.addFormPanel(grid=True)
        top_panel.addFormLabel("Scope options")
        top_panel.addFormStr("Wave", r".+", "", column=1)
        # self.form.addFormHelper("Only selected commands will be launchable.")
        # commands = Command.getList(None, APIClient.getInstance().getCurrentPentest())
        # commands_names = []
        # comms_values = []
        # for c in commands:
        #     commands_names.append(str(c))
        #     comms_values.append(c.getId())
        # self.form.addFormChecklist("Commands", commands_names, [], values=comms_values)
        self.completeInsertWindow()

    def getAdditionalContextualCommands(self):
        return {"Insert wave": self.openInsertWindow}

    def addChildrenBaseNodes(self, newNode):
        """
        Add to the given node from a treeview the mandatory childrens.
        For a wave it is the intervals parent node and the copes parent node.

        Args:
            newNode: the newly created node we want to add children to.
        Returns:
            * the created Intervals parent node
            * the created Scope parent node
        """
        d = self.appliTw.insert(newNode, "end", IntervalView.DbToTreeviewListId(
            self.controller.getDbId()), text="Intervals", image=IntervalView.getClassIcon())
        s = self.appliTw.insert(newNode, "end", ScopeView.DbToTreeviewListId(
            self.controller.getDbId()), text="Scopes", image=ScopeView.getClassIcon())
        return d, s

    def addInTreeview(self, parentNode=None, **kwargs):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
            addChildren: If False: skip interval, tools and scope insert. Useful when displaying search results.
        """
        addChildren = kwargs.get("addChildren", True)
        self.appliTw.views[str(self.controller.getDbId())] = {
            "view": self, 'parent': ''}
        if parentNode is None:
            parentNode = self.getParentNode()
        try:
            wave_node = self.appliTw.insert(parentNode, "end", str(self.controller.getDbId()), text=str(
                self.controller.getModelRepr()), tags=self.controller.getTags(), image=self.getClassIcon())
        except tk.TclError:
            wave_node = str(self.controller.getDbId())
        if addChildren:
            dates_node, scopes_node = self.addChildrenBaseNodes(wave_node)
            intervals = self.controller.getIntervals()
            for interval in intervals:
                interval_vw = IntervalView(
                    self.appliTw, self.appliViewFrame, self.mainApp, IntervalController(Interval(interval)))
                interval_vw.addInTreeview(dates_node)
            checks = self.controller.getChecks()
            for check in checks:
                check_o = CheckInstanceController(check)
                check_vw = CheckInstanceView(self.appliTw, self.appliViewFrame, self.mainApp, check_o)
                check_vw.addInTreeview(str(self.controller.getDbId()))
            scopes = self.controller.getScopes()
            for scope in scopes:
                scope_o = ScopeController(Scope(scope))
                scope_vw = ScopeView(
                    self.appliTw, self.appliViewFrame, self.mainApp, scope_o)
                scope_vw.addInTreeview(scopes_node)
        if self.mainApp.settings.is_checklist_view():
            self.hide("checklist_view")
        if "hidden" in self.controller.getTags():
            self.hide("tags")

    def getParentNode(self):
        """
        Return the id of the parent node in treeview.

        Returns:
            return the saved waves_node inside the Appli class.
        """
        return self.appliTw.waves_node

