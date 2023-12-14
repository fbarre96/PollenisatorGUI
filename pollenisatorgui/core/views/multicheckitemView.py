"""View for command list object. Present an multi editing form to userh."""

from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.views.viewelement import ViewElement
import pollenisatorgui.core.components.utils as utils

class MultiCheckItemView(ViewElement):
    """View for command list object. Present an multi editing form to user when interacted with."""
    
    def __init__(self, appliTw, appViewFrame, mainApp):
        super().__init__(appliTw, appViewFrame, mainApp, None)

    def openModifyWindow(self, **kwargs):
        """
        Creates a tkinter form using Forms classes. This form aims to manipulate many commands
        """
        self.form.clear()
        top_panel = self.form.addFormPanel()
        # top_panel.addFormButton("Add to my commands", self.addSelectedToMyCommands)
        # top_panel.addFormButton("Add to Worker commands", self.addSelectedToWorkerCommands)
        # top_panel.addFormButton("Remove selection from my commands", self.removeSelectedFromMyCommands)
        top_panel.addFormButton("Delete", self.appliTw.deleteSelected, 
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
        self.showForm()

    # def addSelectedToMyCommands(self, event=None):
    #     apiclient = APIClient.getInstance()
    #     for selected in self.appliTw.selection():
    #         apiclient.addCommandToMyCommands(selected)

    # def addSelectedToWorkerCommands(self, event=None):
    #     apiclient = APIClient.getInstance()
    #     for selected in self.appliTw.selection():
    #         apiclient.addCommandToWorkerCommands(selected)

    # def removeSelectedFromMyCommands(self, event=None):
    #     apiclient = APIClient.getInstance()
    #     for selected in self.appliTw.selection():
    #         apiclient.removeCommandFromMyCommands(selected)