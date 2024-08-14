from bson import ObjectId
from pollenisatorgui.core.components.apiclient import APIClient
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.pollex import pollex_exec
from pollenisatorgui.scripts.lan.utils import ask_text
import tempfile
import os

def main(apiclient, appli, **kwargs):
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
    "vagrant",
    "guest",
    "glpiadmin",
    "adminglpi",
]
    cme_path = utils.which_expand_alias("nxc")
    if not cme_path:
        return False, "binary 'nxc' is not in the PATH."
    APIClient.setInstance(apiclient)
    domain = ""
    if kwargs.get("target_type") == "computer":
        computer_info =  apiclient.find("computers", {"type":"computer", "_id":ObjectId(kwargs.get("target_iid", ""))}, False)
        if computer_info is not None:
            domain = computer_info.get("domain", "")
    if domain == "":
        domain = ask_text(appli is not None, "Enter domain name :", "")
    if domain == "" or domain is None:
        return False, "No domain given"
    response = ask_text(appli is not None, "Basic users to try :", "\n".join(users_to_test))
    if response is None or response == "":
        return False, "No users given"
    users_to_test = [r.strip() for r in response.split("\n")]
    dc = None
    exec = 0
    dc_info = apiclient.find("computers", {"type":"computer", "domain":domain, "infos.is_dc":True}, False)
    if dc_info is None:
        dc = ask_text(appli is not None, "DC not known, give me IP if you know it", "")
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
        if appli:
            appli.launch_in_terminal(kwargs.get("default_target",None), "NXC try common users", f"{cme_path} smb {dc} -u {file_name} -p {file_name} -d {domain} --no-bruteforce --continue-on-success"),
        else:
            pollex_exec(f"{cme_path} smb {dc} -u {file_name} -p {file_name} -d {domain} --no-bruteforce --continue-on-success")
    return True, f"Launched {exec} cmes"
