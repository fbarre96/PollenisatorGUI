import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.application.dialogs.ChildDialogInfo import ChildDialogInfo
import psutil
from pollenisatorgui.core.components.apiclient import APIClient



def main(apiclient, **kwargs):
    APIClient.setInstance(apiclient)
    addrs = psutil.net_if_addrs()
    print(addrs.keys())
    dialog = ChildDialogCombo(None, addrs.keys(), displayMsg="Choose your ethernet device to listen on")
    dialog.app.wait_window(dialog.app)
    if dialog.rvalue is not None:
       utils.executeInExternalTerm(f"sudo responder -I {dialog.rvalue} -A")
    return True, f"Listening responder open"
