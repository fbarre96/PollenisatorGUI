"""Ask the user to select a file or directory and then parse it with the selected parser"""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
import os
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.forms.formpanel import FormPanel
from pollenisatorgui.core.views.viewelement import ViewElement
from pollenisatorgui.core.application.dialogs.ChildDialogProgress import ChildDialogProgress
import pollenisatorgui.core.components.utils as utils


class ChildDialogFileParser:
    """
    Open a child dialog of a tkinter application to ask details about
    existing files parsing.
    """

    def __init__(self, parent, default_path=""):
        """
        Open a child dialog of a tkinter application to ask details about
        existing files parsing.

        Args:
            default_path: a default path to be added
        """
        self.app = CTkToplevel(parent)
        self.app.attributes("-type", "dialog")
        self.app.title("Upload result file")
        self.rvalue = None
        self.default = default_path
        appFrame = CTkFrame(self.app)
        self.app.bind("<Escape>", self.onError)
        apiclient = APIClient.getInstance()
        self.form = FormPanel()
        self.form.addFormLabel(
            "Import one file or choose a directory", "", side=tk.TOP)
        self.form.addFormFile("File", ".+", self.default, width=50,
                              side=tk.TOP, mode="file|directory")
        self.form.addFormLabel("Plugins", side=tk.TOP)
        self.form.addFormCombo(
            "Plugin", ["auto-detect"]+[x["plugin"] for x in apiclient.getPlugins()], "auto-detect", side=tk.TOP)
        self.form.addFormButton("Parse", self.onOk, side=tk.RIGHT)

        self.form.constructView(appFrame)
        appFrame.pack(pady=10,padx=10)

        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.focus_force()
            self.app.grab_set()
            self.app.lift()
        except tk.TclError:
            pass

    def onError(self, event=None):
        self.app.destroy()
        self.rvalue = None
        return None

    def onOk(self, _event=None):
        """
        Called when the user clicked the validation button.
        launch parsing with selected parser on selected file/directory.
        Close the window.

        Args:
            _event: not used but mandatory
        """
        res, msg = self.form.checkForm()
        if not res:
            tk.messagebox.showwarning(
                "Form not validated", msg, parent=self.app)
            return
        notes = None
        tags = None
        form_values = self.form.getValue()
        form_values_as_dicts = ViewElement.list_tuple_to_dict(form_values)
        files_paths = form_values_as_dicts["File"]
        plugin = form_values_as_dicts["Plugin"]
        files = set()
        for filepath in files_paths:
            if os.path.isdir(filepath):
                # r=root, d=directories, f = files
                for r, _d, f in os.walk(filepath):
                    for fil in f:
                        files.add(os.path.join(r, fil))
            else:
                files.add(filepath)
        if not files:
            return
        dialog = ChildDialogProgress(self.app, "Importing files", "Importing "+str(
            len(files)) + " files. Please wait for a few seconds.", 100.0/len(files), "determinate")
        dialog.show(len(files))
        # LOOP ON FOLDER FILES
        results = {}
        apiclient = APIClient.getInstance()
        for f_i, file_path in enumerate(files):
            additional_results = apiclient.importExistingResultFile(file_path, plugin)
            for key, val in additional_results.items():
                results[key] = results.get(key, 0) + val
            dialog.update()
        dialog.destroy()
        # DISPLAY RESULTS
        presResults = ""
        filesIgnored = 0
        for key, value in results.items():
            presResults += str(value) + " " + str(key)+".\n"
            if key == "Ignored":
                filesIgnored += 1
        if plugin == "auto-detect":
            if filesIgnored > 0:
                tk.messagebox.showwarning(
                    "Auto-detect ended", presResults, parent=self.app)
            else:
                tk.messagebox.showinfo("Auto-detect ended", presResults, parent=self.app)
        else:
            if filesIgnored > 0:
                tk.messagebox.showwarning(
                    "Parsing ended", presResults, parent=self.app)
            else:
                tk.messagebox.showinfo("Parsing ended", presResults, parent=self.app)

        self.rvalue = None
        self.app.quit()
