from pollenisatorgui.core.components.apiclient import APIClient
import pollenisatorgui.core.components.utils as utils
import tempfile
import os
from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText

import shutil

users_to_test = [
    "test",
    "admin",
    "backup",
    "administrateur",
    "Administrateur",
    "administrator",
    "testad",
    "ad",
    "stage",
    "audit",
    "pentest",
    "pwn",
    "super",
    "preprod",
    "prod",
    "demo",
    "visio",
    "livesync",
    "guest",
    "glpiadmin",
    "adminglpi",
]

def main(apiclient, appli, **kwargs):
    if not utils.which_expand_alias("cme"):
        return False, "binary 'cme' is not in the PATH."
    APIClient.setInstance(apiclient)
    domain = kwargs.get("domain", "")
    if domain == "":
        dialog = ChildDialogAskText(None, "Enter domain name", multiline=False)
        dialog.app.wait_window(dialog.app)
        domain = dialog.rvalue
    if domain == "" or domain is None:
        return False, "No domain given"
    dc = None
    exec = 0
    dc_info = apiclient.find("ActiveDirectory", {"type":"computer", "domain":domain, "infos.is_dc":True}, False)
    if dc_info is None:
        dialog = ChildDialogAskText(None, "DC not known, give me IP if you know it", multiline=False)
        dialog.app.wait_window(dialog.app)
        dc = dialog.rvalue
    else:
        dc = dc_info.get("ip")
    if dc is None or dc == "":
        return False, "DC not known"
    temp_folder = tempfile.gettempdir() 
    file_name = os.path.join(temp_folder, "users_"+str(domain)+".txt")
    users = "\n".join(users_to_test)
    if users.strip() != "":
        with open(file_name, "w") as f:
            f.write(users+"\n")
        exec += 1
        appli.launch_in_terminal(kwargs.get("default_target",None), "CME try common users", f"'pollex cme smb {dc} -u {file_name} -p {file_name} -d {domain} --no-bruteforce --continue-on-success'"),
    return True, f"Launched {exec} cmes"
