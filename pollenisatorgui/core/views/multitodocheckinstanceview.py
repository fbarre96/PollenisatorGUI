"""View for multi checkinstance list object. Present a form to user when interacted with."""

from pollenisatorgui.core.views.viewelement import ViewElement
from customtkinter import *
from PIL import ImageTk, Image
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.components.settings import Settings
import tkinter.ttk as ttk


class MultiTodoCheckInstanceView(ViewElement):
    """View for checlist multi object. Present an multi  form to user when interacted with."""

    ### TODO : CHECKLIST VIEW ADD SCOPES filtering when there is too many checkintances.
    def __init__(self, appliTw, appViewFrame, mainApp, models, parent=None):
        super().__init__(appliTw, appViewFrame, mainApp, None)
        self.checks = models
        self.parent = parent

    def addInTreeview(self, title, **kwargs):
        from pollenisatorgui.core.views.checkinstanceview import CheckInstanceView
        iid = "multi|todo|"+str(self.parent)
        self.appliTw.views[iid] = {"view": self}
        self.appliTw.insert(self.parent, "end", iid,text=f"{title} TODO ({len(self.checks)})", image=CheckInstanceView.getStatusIcon("todo"))

    def openModifyWindow(self):
        """
        Creates a tkinter form using Forms classes. This form aims to update or perform actions on multiple different objects common properties like tags.
        """
        self.form.clear()
        top_panel = self.form.addFormPanel()
        top_panel.addFormButton("Export", self.appliTw.exportSelection)
        top_panel.addFormButton("Hide", self.appliTw.hideSelection)
        self.delete_image = CTkImage(Image.open(utils.getIcon("delete.png")))
        #top_panel.addFormButton("Custom Command", self.appliTw.customCommand)
        top_panel.addFormButton("Delete", self.appliTw.deleteSelected, image=self.delete_image,
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
        panTags = self.form.addFormPanel(grid=True)
        registeredTags = Settings.getTags()
        keys = list(registeredTags.keys())
        column = 0
        listOfLambdas = [self.tagClicked(keys[i]) for i in range(len(keys))]
        for registeredTag, tag_info in registeredTags.items():
            s = ttk.Style(self.mainApp)
            btn_tag = panTags.addFormButton(registeredTag, listOfLambdas[column], column=column)
            btn_tag.configure(fg_color=tag_info.get("color"))
            column += 1
        self.showForm()
