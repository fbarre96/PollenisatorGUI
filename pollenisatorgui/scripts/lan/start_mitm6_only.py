import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
import os
from pollenisatorgui.core.components.apiclient import APIClient
import psutil

from pollenisatorgui.scripts.lan.utils import checkPath


def main(apiclient, appli, **kwargs):
    res, path = checkPath(["mitm6", "mitm6.py"])
    if not res:
        return False, path
    APIClient.setInstance(apiclient)
    smb_signing_list = apiclient.find("computers", {}, True)
    export_dir = utils.getExportDir()
    domains = set()
    for computer in smb_signing_list:
        domain = computer.get("domain", "")
        if domain.strip() != "":
            domains.add(domain)
    domains = list(domains)
    relaying_loot_path = os.path.join(export_dir, "loot_relay")
    try:
        os.makedirs(relaying_loot_path)
    except:
        pass
    relaying_loot_path = os.path.join(relaying_loot_path, "hashes-mitm6.log")
    addrs = psutil.net_if_addrs()
    dialog = ChildDialogCombo(None, addrs.keys(), displayMsg="Choose your ethernet device to listen on")
    dialog.app.wait_window(dialog.app)
    device = dialog.rvalue
    if device is None:
        return False, "No device selected"
    domain = ""
    if len(domains) == 0:
        dialog = ChildDialogAskText(None, "Enter domain name", multiline=False)
        dialog.app.wait_window(dialog.app)
        domain = dialog.rvalue
    elif len(domains) == 1:
        domain = domains[0]
    else:
        dialog = ChildDialogCombo(None, domains, displayMsg="Choose target domain")
        dialog.app.wait_window(dialog.app)
        domain = dialog.rvalue
    if domain is None:
        return False, "No domain choosen"
    cmd = f"mitm6 -i {device} -d {domain}"
    if os.geteuid() != 0:
        cmd = "sudo "+cmd
    appli.launch_in_terminal(kwargs.get("default_target",None), "mitm6", f"{cmd}", use_pollex=False)
    return True, f"Listening ntlmrelayx with mittm6 opened, loot directory is here:"+str(relaying_loot_path)+"\n"
    
