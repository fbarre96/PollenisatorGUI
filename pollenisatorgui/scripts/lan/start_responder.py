import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.application.dialogs.ChildDialogInfo import ChildDialogInfo
import psutil
from pollenisatorgui.core.components.apiclient import APIClient
import os


def main(apiclient, **kwargs):
   APIClient.setInstance(apiclient)
   addrs = psutil.net_if_addrs()
   print(addrs.keys())
   dialog = ChildDialogCombo(None, addrs.keys(), displayMsg="Choose your ethernet device to listen on")
   dialog.app.wait_window(dialog.app)
   if dialog.rvalue is not None:
      cmd = f"responder -I {dialog.rvalue} -A"
      if os.geteuid() != 0:
         cmd = "sudo "+cmd
      utils.executeInExternalTerm(f"'{cmd}'", default_target=kwargs.get("default_target", None))
   return True, f"Listening responder open"
