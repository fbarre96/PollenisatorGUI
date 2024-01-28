import subprocess
import tkinter
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
import psutil
from pollenisatorgui.core.components.apiclient import APIClient
import os

from pollenisatorgui.scripts.lan.utils import checkPath


def main(apiclient, appli, **kwargs):
   res, path = checkPath(["responder", "Responder.py", "responder.py"])
   if res is None:
      return False, path
   responder_path = path
   APIClient.setInstance(apiclient)
   responder_conf = ""
   if utils.which_expand_alias("locate"):
        resp = subprocess.run("locate Responder.conf", capture_output=True, text=True, shell=True)
        stdout = resp.stdout
        if stdout.strip() == "":
            file = tkinter.filedialog.askopenfilename(title="Locate responder conf file please:", filetypes=[('Config Files', '*.conf')])
            if file:
                responder_conf = file
            else:
                return False, "Responder conf not given"
        else:
            dialog = ChildDialogCombo(None, stdout.split("\n"), displayMsg="Choose your responder config file", width=200)
            dialog.app.wait_window(dialog.app)
            if dialog.rvalue is not None:
                responder_conf = dialog.rvalue.strip()
                cmd = 'sed -i -E "s/(HTTP|SMB) = Off/\\1 = On/gm" '+str(responder_conf)
                if os.geteuid() != 0:
                    cmd = "sudo "+cmd
                appli.launch_in_terminal(None, "sed for responder", cmd, use_pollex=False)
   addrs = psutil.net_if_addrs()
   print(addrs.keys())
   dialog = ChildDialogCombo(None, addrs.keys(), displayMsg="Choose your ethernet device to listen on")
   dialog.app.wait_window(dialog.app)
   if dialog.rvalue is not None:
      cmd = f"{responder_path} -I {dialog.rvalue} -w -d"
      if os.geteuid() != 0:
         cmd = "sudo "+cmd
      appli.launch_in_terminal(kwargs.get("default_target",None), "Responder listening", cmd, use_pollex=False)
   return True, f"Listening responder open"