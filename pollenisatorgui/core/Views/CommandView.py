"""View for command object. Handle node in treeview and present forms to user when interacted with."""

from pollenisatorgui.core.Components.apiclient import APIClient
from pollenisatorgui.core.Views.ViewElement import ViewElement
from pollenisatorgui.core.Components.Settings import Settings
import tkinter as tk

class CommandView(ViewElement):
    """
    View for command object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory.
    """
    icon = 'command.png'

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

    def _commonWindowForms(self, default={}):
        """Construct form parts identical between Modify and Insert forms
        Args:
            default: a dict of default values for inputs (sleep_between, priority, max_thread). Default to empty respectively "0", "0", "1"
        """
        self.form.addFormHidden("owner", default.get("owner", ""))
        panel_bottom = self.form.addFormPanel(grid=True)
        row = 0
        panel_bottom.addFormLabel("Binary path", row=row)
        panel_bottom.addFormStr("Bin path", r"", default.get("bin_path", ""), width=30, column=1, row=row)
        panel_bottom.addFormHelper(
            "The local binary path to use for this command.", column=2, row=row)
        row += 1
        panel_bottom.addFormLabel("Plugin", row=row)
        panel_bottom.addFormCombo("Plugin", APIClient.getInstance().getPlugins(), default.get("plugin", "Default") ,width=30, column=1, row=row)
        panel_bottom.addFormHelper(
            "The plugin handling this command.", column=2, row=row)
        row += 1
        panel_bottom.addFormLabel("Timeout (in secondes)", row=row)
        panel_bottom.addFormStr("Timeout", r"\d+", default.get("timeout", "300"), width=10, column=1, row=row)
        panel_bottom.addFormHelper(
            "The tool will cancel itself when this duration in second is reached to be run again later.", column=2, row=row)
        row += 1
        panel_bottom.addFormLabel("Delay", row=row)
        panel_bottom.addFormStr("Delay", r"\d+", default.get("sleep_between", "0"), width=5, column=1, row=row)
        panel_bottom.addFormHelper(
            "Delay in-between two launch of this command (in seconds)", column=2, row=row)
        row += 1
        panel_bottom.addFormLabel("Priority", row=row)
        panel_bottom.addFormStr("Priority", r"\d+", default.get("priority", "0"),
                                width=2, row=row, column=1)
        panel_bottom.addFormHelper(
            "Priority in queue (0 is HIGHEST)", row=row, column=2)
        row += 1
        panel_bottom.addFormLabel("Threads", row=row)
        panel_bottom.addFormStr("Threads", r"\d+", default.get("max_thread", "1"),
                                width=2, row=row, column=1)
        panel_bottom.addFormHelper(
            "Number of authorized parallel running of this command on one worker.", row=row, column=2)

    def openModifyWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing Command
        """
        modelData = self.controller.getData()
        self._initContextualMenu()
        settings = self.mainApp.settings
        settings.reloadSettings()
        self.form.addFormHidden("indb", self.controller.getData()["indb"])
        panel_top = self.form.addFormPanel(grid=True)
        panel_top.addFormLabel("Name", modelData["name"], sticky=tk.NW)
        panel_top.addFormLabel("Level", modelData["lvl"], row=1, sticky=tk.NW)
        panel_top_bis = self.form.addFormPanel(grid=True)
        panel_top_bis.addFormChecklist(
            "Types", Settings.getPentestTypes().keys(), modelData["types"], column=1)
        panel_safe = self.form.addFormPanel(grid=True)
        panel_safe.addFormLabel("Safe")
        panel_safe.addFormCheckbox(
            "Safe", "Safe", modelData["safe"], column=1)
        panel_safe.addFormHelper(
            "If checked, this command can be run by an auto scan.", column=2)
        panel_text = self.form.addFormPanel()
        panel_text.addFormLabel("Command line options", side="top")
        panel_text.addFormHelper(
            """Do not include binary name/path\nDo not include Output file option\nUse variables |wave|, |scope|, |ip|, |port|, |parent_domain|, |outputDir|, |port.service|, |port.product|, |ip.infos.*| |port.infos.*|""", side="right")
        panel_text.addFormText("Command line options", r"",
                               modelData["text"], self.menuContextuel, side="left", height=5)
        panel_bottom = self.form.addFormPanel(grid=True)
        panel_bottom.addFormLabel("Ports/Services", column=0)
        panel_bottom.addFormStr(
            "Ports/Services", r"^(\d{1,5}|[^\,]+)?(?:,(\d{1,5}|[^\,]+))*$", modelData["ports"], self.popup, width=50, column=1)
        panel_bottom.addFormHelper(
            "Services, ports or port ranges.\nthis list must be separated by a comma, if no protocol is specified, tcp/ will be used.\n Example: ssl/http,https,http/ssl,0-65535,443...",column=2)
        panel_bottom = self.form.addFormPanel()

        if not self.controller.isMyCommand():
            panel_bottom.addFormButton("Duplicate to my commands", self.controller.addToMyCommands)
        self._commonWindowForms(modelData)
        self.completeModifyWindow(self.controller.isMyCommand() or self.controller.isWorkerCommand())

    def openInsertWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to insert a new Command
        """
        data = self.controller.getData()
        self._initContextualMenu()
        self.form.addFormHidden("indb", data.get("indb", "pollenisator"))
        panel_top = self.form.addFormPanel(grid=True)
        panel_top.addFormLabel("Name")
        panel_top.addFormStr("Name", r"\S+", data.get("name", ""), None, column=1)
        panel_top.addFormLabel("Level", row=1)
        lvl = ["network", "domain", "ip", "port", "wave"]
        for module in self.mainApp.modules:
            if getattr(module["object"], "registerLvls", False):
                lvl += module["object"].registerLvls
        panel_top.addFormCombo(
            "Level", lvl, data.get("lvl", "network"), row=1, column=1)
        panel_top.addFormHelper(
            "lvl wave: will run on each wave once\nlvl network: will run on each NetworkIP once\nlvl domain: will run on each scope domain once\nlvl ip: will run on each ip/hostname once\nlvl port: will run on each port once", row=1, column=2)
        panel_types = self.form.addFormPanel(grid=True)
        panel_types.addFormChecklist(
            "Types", Settings.getPentestTypes(), data.get("types", []), row=2, column=1)
        panel_types.addFormHelper(
            "This command will be added by default on pentest having a type checked in this list.\nThis list can be modified on settings.", column=2)
        panel_safe = self.form.addFormPanel(grid=True)
        panel_safe.addFormLabel("Safe")
        panel_safe.addFormCheckbox(
            "Safe", "Safe", data.get("safe", False), column=1)
        panel_safe.addFormHelper(
            "If checked, this command can be run by an auto scan.", column=2)
        panel_text = self.form.addFormPanel()
        panel_text.addFormLabel("Command line options", side="top")
        panel_text.addFormHelper(
            """Do not include binary name/path\nDo not include Output file option\nUse variables |wave|, |scope|, |ip|, |port|, |parent_domain|, |outputDir|, |port.service|, |port.product|, |ip.infos.*| |port.infos.*|""", side="right")
        panel_text.addFormText("Command line options",
                               r"", data.get("text", ""), self.menuContextuel, side="top", height=5)
        panel_bottom = self.form.addFormPanel(grid=True)
        panel_bottom.addFormLabel("Ports/Services")
        panel_bottom.addFormStr(
            "Ports/Services", r"^(\d{1,5}|[^\,]+)?(?:,(\d{1,5}|[^\,]+))*$", data.get("ports", ""), width=50, column=1)
        panel_bottom.addFormHelper(
            "Services, ports or port ranges.\nthis list must be separated by a comma, if no protocol is specified, tcp/ will be used.\n Example: ssl/http,https,http/ssl,0-65535,443...", column=2)

        self._commonWindowForms(self.controller.getData())
        self.completeInsertWindow()

    def addInTreeview(self, parentNode=None):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
        """
        if parentNode is None:
            parentNode = self.getParentNode()
        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}
        self.appliTw.insert(parentNode, "end", str(
            self.controller.getDbId()), text=str(self.controller.getModelRepr()), tags=self.controller.getTags(), image=self.getClassIcon())
        if "hidden" in self.controller.getTags():
            self.hide()

    def getParentNode(self):
        """
        Return the id of the parent node in treeview.

        Returns:
            return the saved command_node node inside the Appli class.
        """
        apiclient = APIClient.getInstance()
        if self.controller.isMyCommand():
            return self.appliTw.my_commands_node
        elif self.controller.isWorkerCommand():
            return self.appliTw.worker_commands_node
        return self.appliTw.others_commands_node

    def _initContextualMenu(self):
        """Initiate contextual menu with variables"""
        self.menuContextuel = tk.Menu(self.appliViewFrame, tearoff=0, background='#A8CF4D',
                                      foreground='white', activebackground='#A8CF4D', activeforeground='white')
        self.menuContextuel.add_command(
            label="Wave id", command=self.addWaveVariable)
        self.menuContextuel.add_command(
            label="Network address without slash nor dots", command=self.addIpReseauDirVariable)
        self.menuContextuel.add_command(
            label="Network address", command=self.addIpReseauVariable)
        self.menuContextuel.add_command(
            label="Parent domain", command=self.addParentDomainVariable)
        self.menuContextuel.add_command(label="Ip", command=self.addIpVariable)
        self.menuContextuel.add_command(
            label="Ip without dots", command=self.addIpDirVariable)
        self.menuContextuel.add_command(
            label="Port", command=self.addPortVariable)

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

    def addWaveVariable(self):
        """
        insert the wave variable inside the a tkinter widget stored in appli widgetMenuOpen attribute.
        """
        self.widgetMenuOpen.insert(tk.INSERT, "|wave|")

    def addIpReseauDirVariable(self):
        """
        insert the scope_dir variable inside the a tkinter widget stored in appli widgetMenuOpen attribute.
        """
        self.widgetMenuOpen.insert(tk.INSERT, "|scope_dir|")

    def addIpReseauVariable(self):
        """
        insert the scope variable inside the a tkinter widget stored in appli widgetMenuOpen attribute.
        """
        self.widgetMenuOpen.insert(tk.INSERT, "|scope|")

    def addParentDomainVariable(self):
        """
        insert the scope variable inside the a tkinter widget stored in appli widgetMenuOpen attribute.
        """
        self.widgetMenuOpen.insert(tk.INSERT, "|parent_domain|")

    def addIpVariable(self):
        """
        insert the ip variable inside the a tkinter widget stored in appli widgetMenuOpen attribute.
        """
        self.widgetMenuOpen.insert(tk.INSERT, "|ip|")

    def addIpDirVariable(self):
        """
        insert the ip_dir variable inside the a tkinter widget stored in appli widgetMenuOpen attribute.
        """
        self.widgetMenuOpen.insert(tk.INSERT, "|ip_dir|")

    def addPortVariable(self):
        """
        insert the port variable inside the a tkinter widget stored in appli widgetMenuOpen attribute.
        """
        self.widgetMenuOpen.insert(tk.INSERT, "|port|")


    def updateReceived(self):
        """Called when a command update is received by notification.
        Update the command treeview item (resulting in icon reloading)
        """
        # if self.controller.isMyCommand():
        #     try:
        #         self.appliTw.move(str(self.controller.model.getId()), self.appliTw.my_commands_node, "end")
        #     except tk.TclError:
        #         print("WARNING: Update received for a non existing command "+str(self.controller.getModelRepr()))
        # else:
        #     try:
        #         self.appliTw.move(str(self.controller.model.getId()), self.appliTw.commands_node, "end")
        #     except tk.TclError:
        #         print("WARNING: Update received for a non existing command "+str(self.controller.getModelRepr()))
        
        super().updateReceived()

    def key(self):
        """Returns a key for sorting this node
        Returns:
            string, key to sort
        """
        return str(self.controller.getModelRepr()).lower()
