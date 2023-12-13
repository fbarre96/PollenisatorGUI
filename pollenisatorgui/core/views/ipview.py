"""View for ip object. Handle node in treeview and present forms to user when interacted with."""

from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.controllers.checkinstancecontroller import CheckInstanceController
from pollenisatorgui.core.controllers.scopecontroller import ScopeController
from pollenisatorgui.core.models.port import Port
from pollenisatorgui.core.models.defect import Defect
from pollenisatorgui.core.models.ip import Ip
from pollenisatorgui.core.models.scope import Scope
from pollenisatorgui.core.views.checkinstanceview import CheckInstanceView
from pollenisatorgui.core.views.multipleipview import MultipleIpView
from pollenisatorgui.core.views.multiplescopeview import MultipleScopeView
from pollenisatorgui.core.views.portview import PortView
from pollenisatorgui.core.views.defectview import DefectView
from pollenisatorgui.core.controllers.portcontroller import PortController
from pollenisatorgui.core.controllers.defectcontroller import DefectController
from pollenisatorgui.core.controllers.ipcontroller import IpController
from pollenisatorgui.core.views.viewelement import ViewElement
import pollenisatorgui.core.components.utils as utils
from tkinter import TclError
from bson.objectid import ObjectId
import json


class IpView(ViewElement):
    """View for ip object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory."""
    icon = 'ip.png'
    icon_out_of_scope = "ip_oos.png"
    cachedClassOOSIcon  = None

    def getIcon(self):
        if not self.controller.is_in_scope():
            from PIL import Image, ImageTk
            if self.__class__.cachedClassOOSIcon == None:
                path = utils.getIcon(self.__class__.icon_out_of_scope)
                self.__class__.cachedClassOOSIcon = ImageTk.PhotoImage(Image.open(path))
            return self.__class__.cachedClassOOSIcon
        return super().getIcon()

    def openModifyWindow(self, **kwargs):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing Ip
        """
        self.form.clear()
        modelData = self.controller.getData()
        top_panel = self.form.addFormPanel(grid=True)
        top_panel.addFormLabel("Ip")
        top_panel.addFormStr(
            "Ip", '', modelData["ip"], None, column=1, state="readonly")
        notes = modelData.get("notes", "")
        top_panel = self.form.addFormPanel()
        top_panel.addFormLabel("Notes", side="top")
        top_panel.addFormText("Notes", r"", notes, None, side="top")
        top_panel.addFormLabel("Infos", side="left")
        top_panel.addFormText("Infos", utils.is_json, json.dumps(modelData["infos"], indent=4, cls=utils.JSONEncoder), height=100, side="left", fill="both")
        buttons_panel = self.form.addFormPanel(grid=True)
        buttons_panel.addFormButton("Add a port", self.addPortCallback)
        buttons_panel.addFormButton(
            "Add a security defect", self.addDefectCallback, column=1)
        self.completeModifyWindow()

    def openInsertWindow(self):
        view = MultipleIpView(self.appliTw, self.appliViewFrame, self.mainApp, self.controller)
        view.openInsertWindow()

    def addPortCallback(self, _event=None):
        """
        Create an empty port model and its attached view. Open this view insert window.

        Args:
            _event: Automatically generated with a button Callback, not used.
        """
        for widget in self.appliViewFrame.winfo_children():
            widget.destroy()
        modelData = self.controller.getData()
        pv = PortView(self.appliTw, self.appliViewFrame,
                      self.mainApp, PortController(Port(modelData)))
        pv.openInsertWindow()

    def getAdditionalContextualCommands(self):
        if self.controller.is_in_scope():
            return {"Add IPs/Hosts": self.addAHostCallback,  "Add a port":self.addPortCallback, "Add a defect":self.addDefectCallback}
        else:
            return {"Add in scope": self.addToScopeCallback}
    
    def addAHostCallback(self, _event=None):
        objView = MultipleIpView(self.appliTw, self.appliViewFrame, self.mainApp, IpController(Ip()))
        objView.openInsertWindow()

    def addToScopeCallback(self, _event=None):
        objView = MultipleScopeView(self.appliTw, self.appliViewFrame, self.mainApp, ScopeController(Scope({"wave":"Main","scope":self.controller.model.ip})))
        objView.openInsertWindow(check_scope=False)

    def addDefectCallback(self, _event=None):
        """
        Create an empty defect model and its attached view. Open this view insert window.

        Args:
            _event: Automatically generated with a button Callback, not used.
        """
        for widget in self.appliViewFrame.winfo_children():
            widget.destroy()
        modelData = self.controller.getData()
        modelData["target_type"] = self.controller.model.__class__.__name__.lower()
        modelData["target_id"] = self.controller.model.getId()
        dv = DefectView(self.appliTw, self.appliViewFrame, self.mainApp,
                        DefectController(Defect(modelData)))
        dv.openInsertWindow(modelData.get("notes", ""))
        

    def _insertChildrenDefects(self):
        """Insert every children defect in database as DefectView under this node"""
        defects = self.controller.getDefects()
        for defect in defects:
            defect_o = DefectController(Defect(defect))
            defect_vw = DefectView(
                self.appliTw, self.appliViewFrame, self.mainApp, defect_o)
            defect_vw.addInTreeview(str(self.controller.getDbId()), addChildren=False)
        return defects
    
    def _insertChildrenChecks(self):
        """Create a tools list node and insert every children tools in database as ToolView under this node"""
        checks = self.controller.getChecks()
        for check in checks:
            check_o = CheckInstanceController(check)
            check_vw = CheckInstanceView(
                self.appliTw, self.appliViewFrame, self.mainApp, check_o)
            check_vw.addInTreeview(str(self.controller.getDbId()), addChildren=False)
        return checks
    
    def _insertChildrenPorts(self, ip_node):
        """Insert every children port in database as DefectView under this node directly"""
        ports = self.controller.getPorts()
        PortView.multiAddInTreeview(self.appliTw, self.appliViewFrame, self.mainApp, ports, ip_node)
    
    def _insertChildren(self):
        self._insertChildrenPorts(str(self.controller.getDbId()))
        self._insertChildrenDefects()
        self._insertChildrenChecks()

    def addInTreeview(self, parentNode=None, **kwargs):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
            _addChildren: not used here
        """
        addChildren = kwargs.get("addChildren", True)
        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}

        if parentNode is None:
            parentNode = self.getParentNode()
        ip_node = None
        tags = self.controller.getTags()
        try:
            if isinstance(parentNode, ObjectId):
                ip_parent_o = Ip.fetchObject({"_id": parentNode})
                if ip_parent_o is not None:
                    parent_view = IpView(self.appliTw, self.appliViewFrame,
                                         self.mainApp, IpController(ip_parent_o))
                    parent_view.addInTreeview(None, addChildren=False)
            #CALLING TK CALL IS FASTER than
            #ip_node = self.appliTw.insert(parentNode, "end", str(
            #   self.controller.getDbId()), text=str(self.controller.getModelRepr()), tags=tags, image=self.getIcon())
            ip_node = self.appliTw.tk.call(self.appliTw._w, "insert", parentNode, "end", "-id", str(self.controller.getDbId()), 
                                 "-text", str(self.controller.getModelRepr()), "-tags", tags, "-image", self.getIcon())
        except TclError as e:
            pass
        if addChildren and ip_node is not None:
            self._insertChildren()
        elif not addChildren and self.appliTw.lazyload and not self.mainApp.searchMode:
            try:
                self.appliTw.tk.call(self.appliTw._w, "insert", ip_node, "end", "-id", str(self.controller.getDbId())+"|<Empty>", 
                                 "-text", "<Empty>")
            except TclError as e:
                pass
        # self.appliTw.sort(parentNode)
        if "hidden" in tags:
            self.hide("tags")
        if self.mainApp.settings.is_checklist_view():
            self.hide("checklist_view")
        modelData = self.controller.getData()
        if self.mainApp.settings.is_hide_oos() and not modelData["in_scopes"]:
            self.hide("filter_oos")
        if not modelData["in_scopes"]:
            # calling tk.call faster than 
            #self.appliTw.item(ip_node, tags=tags+["OOS"], image=self.getIcon())
            self.appliTw.tk.call(
                self.appliTw._w, "item", ip_node, "-tags", tags+["OOS"], "-image", self.getIcon())
            

    def split_ip(self):
        """Split a IP address given as string into a 4-tuple of integers.
        Returns:
            Tuple of 4 integers values representing the 4 parts of an ipv4 string"""
        modelData = self.controller.getData()
        try:
            ret = tuple(int(part) for part in modelData["ip"].split('.'))
        except ValueError:
            ret = tuple([0])+tuple(ord(chrDomain)
                                   for chrDomain in modelData["ip"])
        return ret

    def key(self):
        """Returns a key for sorting this node
        Returns:
            Tuple of 4 integers values representing the 4 parts of an ipv4 string, key to sort ips properly
        """
        return self.split_ip()

    def insertReceived(self):
        """Called when a IP insertion is received by notification.
        Insert the node in summary.
        Can also insert in treeview with OOS tags.
        """
        modelData = self.controller.getData()
        if modelData.get("in_scopes", []): # in_scopes is not empty
            for module in self.mainApp.modules:
                if callable(getattr(module["object"], "insertIP", None)):
                    module["object"].insertIp(modelData["ip"])
        else:
            self.appliTw.item(str(self.controller.getDbId()), text=str(
                self.controller.getModelRepr()), image=self.getIcon(), tags=["OOS"])

    def updateReceived(self, obj=None, old_obj=None):
        """Called when a IP update is received by notification.
        Update the ip node OOS status tags and add/remove it from summary.
        """
        if self.controller.model is not None:
            modelData = self.controller.getData()
            if not modelData["in_scopes"]:
                self.controller.addTag("OOS")
                self.appliTw.item(str(self.controller.getDbId()), image=self.getIcon(), tags=self.controller.getTags()+["OOS"])
                for module in self.mainApp.modules:
                    if callable(getattr(module["object"], "deleteIp", None)):
                        module["object"].deleteIp(modelData["ip"])
            else:
                tags = list(self.controller.getTags())
                if "OOS" in tags:
                    tags.remove("OOS")
                self.appliTw.item(str(self.controller.getDbId()), tags=tags, image=self.getIcon())
                for module in self.mainApp.modules:
                    if callable(getattr(module["object"], "insertIp", None)):
                        module["object"].insertIp(modelData["ip"])
            super().updateReceived()

    def getParentNode(self):
        """
        Return the id of the parent node in treeview.

        Returns:
            return the parent ips_node of application treeview
        """
        #parent = self.controller.getParent()
        #if parent is None:
        parent = self.appliTw.ips_node
        return parent
