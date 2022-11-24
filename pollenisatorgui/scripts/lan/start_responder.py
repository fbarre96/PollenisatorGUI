import pollenisatorgui.core.Components.Utils as Utils
from pollenisatorgui.core.Application.Dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.Application.Dialogs.ChildDialogInfo import ChildDialogInfo
import psutil
from pollenisatorgui.core.Components.apiclient import APIClient



def main(apiclient):
    APIClient.setInstance(apiclient)
    addrs = psutil.net_if_addrs()
    print(addrs.keys())
    dialog = ChildDialogCombo(None, addrs.keys(), displayMsg="Choose your ethernet device to listen on")
    dialog.app.wait_window(dialog.app)
    if dialog.rvalue is not None:
       Utils.executeInExternalTerm(f"sudo responder -I {dialog.rvalue} -A")
    return True, f"Listening responder open"
