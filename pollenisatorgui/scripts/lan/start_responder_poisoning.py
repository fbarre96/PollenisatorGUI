import subprocess
import pollenisatorgui.core.components.utils as utils
import psutil
from pollenisatorgui.core.components.apiclient import APIClient
import os

from pollenisatorgui.scripts.lan.utils import checkPath, getNICs


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
            if appli:
                import tkinter as tk
                file = tk.filedialog.askopenfilename(title="Locate responder conf file please:", filetypes=[('Config Files', '*.conf')])
                if file:
                    responder_conf = file
                else:
                    return False, "Responder conf not given"
            else:
                responder_conf = input("Responder conf not found, give full path to it please:")
                if responder_conf.strip() == "":
                    return False, "Responder conf not given"
            if not os.path.isfile(responder_conf):
                return False, "Responder conf not found"
        else:
            if appli:
                from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
                dialog = ChildDialogCombo(None, stdout.split("\n"), displayMsg="Choose your responder config file", width=200)
                dialog.app.wait_window(dialog.app)
                if dialog.rvalue is not None:
                    responder_conf = dialog.rvalue.strip()
                    if os.geteuid() != 0:
                        cmd = "sudo "+cmd
                    cmd = 'sed -i -E "s/(HTTP|SMB) = On/\\1 = Off/gm" '+str(responder_conf)
                    appli.launch_in_terminal(None, "sed for responder", cmd, use_pollex=False)
            else:
                possibilites = [x.strip() for x in stdout.split("\n") if x.strip() != ""]
                if len(possibilites) > 1:
                    print("Many responder conf found, choose one :")

                    for i, path in enumerate(possibilites):
                        if path.strip() == "":
                            continue
                        print(str(i+1)+". "+path)
                    responder_conf = input("Choose your responder config file by its number:")
                    try:
                        responder_conf = possibilites[int(responder_conf)-1]
                    except:
                        return False, "Wrong number given"
                else:
                    responder_conf = possibilites[0]
                if responder_conf.strip() == "":
                    return False, "Responder conf not given"
                if os.geteuid() != 0:
                    cmd = "sudo "+cmd
                cmd = 'sed -i -E "s/(HTTP|SMB) = On/\\1 = Off/gm" '+str(responder_conf)
                os.popen(cmd)
   device = getNICs(appli is not None)
   if device is not None and device != "":
      cmd = f"{responder_path} -I {dialog.rvalue} -w -d"
      if os.geteuid() != 0:
        cmd = "sudo "+cmd
        if appli:
            appli.launch_in_terminal(kwargs.get("default_target",None), "Responder listening", cmd, use_pollex=False)
        else:
            subprocess.run(f"{cmd}", shell=True)
   return True, f"Listening responder open"