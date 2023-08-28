import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
import psutil
from pollenisatorgui.core.components.apiclient import APIClient
import os


def main(apiclient, appli, **kwargs):
   APIClient.setInstance(apiclient)
   addrs = psutil.net_if_addrs()
   print(addrs.keys())
   dialog = ChildDialogCombo(None, addrs.keys(), displayMsg="Choose your ethernet device to listen on")
   dialog.app.wait_window(dialog.app)
   responder_path = utils.which_expand_alias("responder")
   if dialog.rvalue is not None:
      cmd = f"{responder_path} -I {dialog.rvalue} -A"
      if os.geteuid() != 0:
         cmd = "sudo "+cmd
      utils.executeInExternalTerm(f"'{cmd}'", default_target=kwargs.get("default_target", None))
   return True, f"Listening responder open"
