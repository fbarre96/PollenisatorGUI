"""View for multi checkinstance list object. Present a form to user when interacted with."""

from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.views.viewelement import ViewElement
from customtkinter import *
from PIL import ImageTk, Image
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.components.settings import Settings
import tkinter.ttk as ttk
import tkinter as tk


class CheckInstanceMultiView(ViewElement):
    """View for checlist multi object. Present an multi  form to user when interacted with."""


    def __init__(self, appliTw, appViewFrame, mainApp):
        super().__init__(appliTw, appViewFrame, mainApp, None)

    def openModifyWindow(self, **kwargs):
        """
        Creates a tkinter form using Forms classes. This form aims to update or perform actions on multiple different objects common properties like tags.
        """
        self.form.clear()
        top_panel = self.form.addFormPanel()
        top_panel.addFormButton("Mark as done", self.markDoneSelection)
        top_panel.addFormButton("Mark as not done", self.markNotDoneSelection)
        top_panel.addFormButton("Export", self.appliTw.exportSelection)
        self.delete_image = CTkImage(Image.open(utils.getIcon("delete.png")))
        top_panel.addFormButton("Delete", self.appliTw.deleteSelected, image=self.delete_image,
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
        selected = self.appliTw.selection()
        dones = []
        not_dones = []
        runnings = []
        for iid in selected:
            view = self.appliTw.views.get(iid, {}).get("view")
            if view is None:
                continue
            if view.controller.getStatus() == "done":
                dones.append(iid)
            elif view.controller.getStatus() == "running":
                runnings.append(iid)
            else:
                not_dones.append(iid)

        if not_dones:
            top_panel.addFormButton("Queue Selection", self.queueSelection)
        self.showForm()

    def markDoneSelection(self, _event=None):
        selected = self.appliTw.selection()
        if selected:
            apiclient = APIClient.getInstance()
            apiclient.multiChangeStatus(selected, "done")
    
    def markNotDoneSelection(self, _event=None):
        selected = self.appliTw.selection()
        if selected:
            apiclient = APIClient.getInstance()
            apiclient.multiChangeStatus(selected, "todo")

    def queueSelection(self, _event = None):
        selected = self.appliTw.selection()
        if selected:
            apiclient = APIClient.getInstance()
            results = apiclient.queueCheckInstances(selected, force=True)
            if len(results.get("successes", [])) < 10:
                for iid in results.get("successes", []):
                    self.mainApp.subscribe_notification("tool_start", self.toolStartedEvent, pentest=apiclient.getCurrentPentest(), iid=iid)
                tk.messagebox.showinfo("Info", "Tasks queued successfully. They should appear in the terminal view below when started", parent=self.mainApp)
            else:
                tk.messagebox.showinfo("Info", "Tasks queued successfully. There is too many to get notified on start.", parent=self.mainApp)
            if results.get("failures", []):
                failure = results.get("failures", [])[0]
                tk.messagebox.showerror("Error", "Error while queueing task : "+str(failure.get("error", "unknown error")), parent=self.mainApp)
                  