"""View for command object. Handle node in treeview and present forms to user when interacted with."""

from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.views.viewelement import ViewElement
from pollenisatorgui.core.components.settings import Settings
import tkinter as tk
import pollenisatorgui.core.components.utils as utils


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
            default: a dict of default values for inputs (priority, priority, max_thread). Default to empty respectively "0", "0", "1"
        """
        self.form.addFormHidden("owners", default.get("owners", []))
        panel_bottom = self.form.addFormPanel(grid=True)
        row = 0
        panel_bottom.addFormLabel("Common binary name", row=row)
        panel_bottom.addFormStr("Bin path", r"", default.get("bin_path", ""), column=1, row=row)
        panel_bottom.addFormHelper(
            "The binary name (nmap for Nmap, dirsearch for Diresearch even if it's dir.py for exemple).\nHelps user not to configure this for common name", column=2, row=row)
        row += 1
        
        panel_bottom.addFormLabel("Plugin", row=row)
        panel_bottom.addFormCombo("Plugin", [x["plugin"] for x in APIClient.getInstance().getPlugins()], default.get("plugin", "Default") , column=1, row=row)
        panel_bottom.addFormHelper(
            "The plugin handling this command.", column=2, row=row)
        row += 1
        panel_bottom.addFormLabel("Timeout (in secondes)", row=row)
        panel_bottom.addFormStr("Timeout", r"\d+", default.get("timeout", "300"), width=50, column=1, row=row)
        panel_bottom.addFormHelper(
            "The tool will cancel itself when this duration in second is reached to be run again later.", column=2, row=row)
        row += 1

    def openModifyWindow(self, **kwargs):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing Command
        """
        self.form.clear()
        modelData = self.controller.getData()
        self._initContextualMenu()
        settings = self.mainApp.settings
        settings.reloadSettings()
        self.form.addFormHidden("indb", self.controller.getData()["indb"])
        panel_top = self.form.addFormPanel(grid=True)
        panel_top.addFormLabel("Name", modelData["name"], sticky=tk.NW)
        
        self.panel_text = self.form.addFormPanel()
        self.panel_text.addFormLabel("Command line options", side="top")
        self.panel_text.addFormLabel(
            """Do not include binary name/path\nDo not include Output file option\nRight click to insert variables like ip, scope, port....""", side="right")
        self.panel_text.addFormText("Command line options", r"",
                               modelData["text"], self.menuContextuel, binds={"<Button-3>": self.popup}, side="left", height=100)
        self._commonWindowForms(modelData)
        panel_bottom = self.form.addFormPanel(fill=tk.X, grid=True)
        
        if not self.controller.isMine():
            panel_bottom.addFormButton("Add to my commands", self.controller.addToMyCommands)
        else:
            settings = Settings()
            settings.reloadLocalSettings()
            my_commands = settings.local_settings.get("my_commands", {})
            default = my_commands.get(modelData["name"], modelData["bin_path"])
            panel_bottom.addFormLabel("My binary path")
            panel_bottom.addFormStr("My binary path", r"", default, column=1)
            panel_bottom.addFormHelper("""This is local to your computer. It will not be shared with other users.\nIt is useful to launch commands on your own computer""",column=2)
        
        self.completeModifyWindow(addTags=False)

    def getAdditionalContextualCommands(self):
        return {"Insert command": self.openInsertWindow}

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
        
        panel_text = self.form.addFormPanel()
        panel_text.addFormLabel("Command line options", side="top")
        panel_text.addFormLabel(
            """Do not include binary name/path\nDo not include Output file option\nRight click to insert variables like ip, scope, port....""", side="right")
        panel_text.addFormText("Command line options",
                               r"", data.get("text", ""), self.menuContextuel, binds={"<Button-3>": self.popup}, side="top", height=100)

        self._commonWindowForms(self.controller.getData())
        self.completeInsertWindow()

    def addInTreeview(self, parentNode=None, **kwargs):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
        """
        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}
        if parentNode is None:
            parentNode = self.getParentNode()
        tags = self.controller.getTags()
        #if self.controller.isMine():
        #    tags.append("known_command")
        try:
            self.appliTw.insert(parentNode, "end", str(
            self.controller.getDbId()), text=str(self.controller.getModelRepr()), tags=tags, image=self.getClassIcon())
        except tk.TclError:
            pass
        if hasattr(self.appliTw, "hide" ) and self.mainApp.settings.is_checklist_view():
            self.hide("checklist_view")
        if "hidden" in tags:
            self.hide("tags")

    def getParentNode(self):
        """
        Return the id of the parent node in treeview.

        Returns:
            return the saved command_node node inside the Appli class.
        """
        return self.appliTw.commands_node

    def _initContextualMenu(self):
        """Initiate contextual menu with variables"""
        self.menuContextuel = utils.craftMenuWithStyle(self.mainApp)
        apiclient = APIClient.getInstance()
        command_variables = apiclient.getCommandVariables()
        for variable_name in command_variables:
           self.menuContextuel.add_command(label=variable_name, command=lambda variable_name=variable_name: self.addVariable(variable_name))
        # self.menuContextuel.add_command(
        #     label="Wave id", command=self.addWaveVariable)
        # self.menuContextuel.add_command(
        #     label="Network address without slash nor dots", command=self.addIpReseauDirVariable)
        # self.menuContextuel.add_command(
        #     label="Network address", command=self.addIpReseauVariable)
        # self.menuContextuel.add_command(
        #     label="Parent domain", command=self.addParentDomainVariable)
        # self.menuContextuel.add_command(label="Ip", command=self.addIpVariable)
        # self.menuContextuel.add_command(
        #     label="Ip without dots", command=self.addIpDirVariable)
        # self.menuContextuel.add_command(
        #     label="Port", command=self.addPortVariable)

    def addVariable(self, variable):
        """
        insert the variable inside the a tkinter widget stored in appli widgetMenuOpen attribute.

        Args:
            variable: the variable to insert
        """
        self.widgetMenuOpen.insert(tk.INSERT, "|"+variable+"|")

    def popup(self, event):
        """
        Fill the self.widgetMenuOpen and reraise the event in the editing window contextual menu

        Args:
            event: a ttk Treeview event autofilled. Contains information on what treeview node was clicked.
        """
        print("command view popup")
        self.widgetMenuOpen = event.widget
        self.menuContextuel.tk_popup(event.x_root, event.y_root)
        self.menuContextuel.focus_set()
        self.menuContextuel.bind('<FocusOut>', self.popupFocusOut)

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


    def updateReceived(self, obj=None, old_obj=None):
        """Called when a command update is received by notification.
        Update the command treeview item (resulting in icon reloading)
        """
        # if self.controller.isMine():
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
            tuple, key to sort
        """
        return tuple([ord(c) for c in str(self.controller.getModelRepr()).lower()])
