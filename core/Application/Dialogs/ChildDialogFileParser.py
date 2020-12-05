"""Ask the user to select a file or directory and then parse it with the selected parser"""
import tkinter as tk
import tkinter.ttk as ttk
import io
import os
from core.Components.Utils import listPlugin
from core.Components.apiclient import APIClient
from core.Forms.FormPanel import FormPanel
from core.Views.ViewElement import ViewElement
from core.Models.Wave import Wave
from core.Application.Dialogs.ChildDialogProgress import ChildDialogProgress



class ChildDialogFileParser:
    """
    Open a child dialog of a tkinter application to ask details about
    existing files parsing.
    """

    def __init__(self, parent):
        """
        Open a child dialog of a tkinter application to ask details about
        existing files parsing.

        Args:
            parent: the tkinter parent view to use for this window construction.
        """
        self.app = tk.Toplevel(parent)
        self.app.title("Upload result file")
        self.rvalue = None
        self.parent = parent
        appFrame = ttk.Frame(self.app)
        self.form = FormPanel()
        self.form.addFormLabel(
            "Import one file or choose a directory", "", side=tk.TOP)
        self.form.addFormFile("File", ".+", width=50,
                              side=tk.TOP, mode="file|directory")
        self.form.addFormLabel("Plugins", side=tk.TOP)
        self.form.addFormCombo(
            "Plugin", ["auto-detect"]+listPlugin(), "auto-detect", side=tk.TOP)
        self.form.addFormButton("Parse", self.onOk, side=tk.TOP)

        self.form.constructView(appFrame)
        appFrame.pack(ipadx=10, ipady=10)

        self.app.transient(parent)
        self.app.grab_set()

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
        file_path = form_values_as_dicts["File"]
        plugin = form_values_as_dicts["Plugin"]
        files = []
        if os.path.isdir(file_path):
            # r=root, d=directories, f = files
            for r, _d, f in os.walk(file_path):
                for fil in f:
                    files.append(os.path.join(r, fil))
        else:
            files.append(file_path)
        dialog = ChildDialogProgress(self.parent, "Importing files", "Importing "+str(
            len(files)) + " files. Please wait for a few seconds.", 200, "determinate")
        dialog.show(len(files))
        # LOOP ON FOLDER FILES
        results = {}
        apiclient = APIClient.getInstance()
        for f_i, file_path in enumerate(files):
            results = apiclient.importExistingResultFile(file_path, plugin)
            dialog.update(f_i)
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
        self.app.destroy()
