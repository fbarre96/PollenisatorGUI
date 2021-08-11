"""ChildDialogEditLocalTools class
Settings for local tools (path and plugin associated)"""
import tkinter as tk
import tkinter.ttk as ttk
from pollenisatorgui.core.Forms.FormPanel import FormPanel
from pollenisatorgui.core.Views.ViewElement import ViewElement
import pollenisatorgui.core.Models.Command as Command
import pollenisatorgui.core.Components.Utils as Utils
from pollenisatorgui.core.Components.apiclient import APIClient


class ChildDialogEditLocalTools:
    """
    Open a child dialog of a tkinter application to ask a user to reset its password.
    """

    def __init__(self, parent):
        """
        Open a child dialog of a tkinter application to display and edit local tools settings

        Args:
            parent: the tkinter parent view to use for this window construction.
        """
        self.parent = parent
        self.app = tk.Toplevel(parent)
        self.app.title("Edit local tools config")
        appFrame = ttk.Frame(self.app)
        self.form = FormPanel()
        toolsConfig = Utils.loadToolsConfig()
        values = {}
        apiclient = APIClient.getInstance()
        commands = Command.Command.fetchObjects({}, apiclient.getCurrentPentest())
        for command in commands:
            values[command.name] = (command.name, toolsConfig.get(command.name, {"bin":"","plugin":""}).get("bin",""),  toolsConfig.get(command.name, {"bin":"","plugin":""}).get("plugin",""))
        self.form.addFormTreevw("tools", ["Command name", "Launch command", "Plugin"], values, side="top", doubleClickBinds=[None, "askstring", apiclient.getPlugins()])
        self.form.addFormButton("OK", self.onOk)
        self.rvalue = None
        self.form.constructView(appFrame)
        appFrame.pack(ipadx=10, ipady=10)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.focus_force()
            self.app.grab_set()
            self.app.lift()
        except tk.TclError:
            pass

    def onOk(self, _event=None):
        """Called the ok button is pressed.
        
        Args:
            _event: not used but mandatory"""
        res, msg = self.form.checkForm()
        apiclient = APIClient.getInstance()
        success = False
        if res:
            form_values = self.form.getValue()
            form_values_as_dicts = ViewElement.list_tuple_to_dict(form_values)
            tools = form_values_as_dicts["tools"]
            new_config = {}
            for tool, values in tools.items():
                if tool.strip() != "":
                    new_config[tool] = {"bin":values[0], "plugin":values[1]}
            Utils.saveToolsConfig(new_config)
        else:
            tk.messagebox.showwarning(
                "Form not validated", msg, parent=self.app)
        
        self.app.destroy()
        

