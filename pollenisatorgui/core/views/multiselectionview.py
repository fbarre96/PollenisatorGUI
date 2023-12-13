"""View for multi selected object clicked. Present an multi modify form to user when interacted with."""

from tkinter import ttk
from pollenisatorgui.core.views.viewelement import ViewElement
from pollenisatorgui.core.components.settings import Settings
import pollenisatorgui.core.components.utils as utils
from customtkinter import *
from PIL import Image

class MultiSelectionView(ViewElement):
    """View for multi selected object clicked. Present an multi modify form to user when interacted with."""

    def __init__(self, appliTw, appViewFrame, mainApp):
        super().__init__(appliTw, appViewFrame, mainApp, None)

    def tagClicked(self, name):
        """Separate callback to apply when a tag button is clicked
        Applies the clicked tag to all selected objects
        Args:
            name: tag name clicked
        """
        return lambda : self.appliTw.setTagFromMenubar(name)

    def openModifyWindow(self, **kwargs):
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