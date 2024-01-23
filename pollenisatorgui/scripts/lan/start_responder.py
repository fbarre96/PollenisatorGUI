import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
import psutil
from pollenisatorgui.core.components.apiclient import APIClient
import os


def main(apiclient, appli, **kwargs):
   responder_path = utils.which_expand_alias("responder")
   if responder_path is None:
      responder_path = utils.which_expand_alias("Responder.py")
   if responder_path is None:
      responder_path = utils.which_expand_alias("responder.py")
   if responder_path is None:
      return False, "Responder not found, create an alias or install it. (responder, Responder.py, responder.py were tested)"
   APIClient.setInstance(apiclient)
   addrs = psutil.net_if_addrs()
   print(addrs.keys())
   dialog = ChildDialogCombo(None, addrs.keys(), displayMsg="Choose your ethernet device to listen on")
   dialog.app.wait_window(dialog.app)
   if dialog.rvalue is not None:
      cmd = f"{responder_path} -I {dialog.rvalue} -A"
      if os.geteuid() != 0:
         cmd = "sudo "+cmd
      appli.launch_in_terminal(kwargs.get("default_target",None), "Responder listening", cmd, use_pollex=False)
   return True, f"Listening responder open"