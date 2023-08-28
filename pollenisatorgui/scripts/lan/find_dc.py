import subprocess
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
import psutil
from pollenisatorgui.core.components.apiclient import APIClient
import os
import re

def main(apiclient, appli, **kwargs):
    APIClient.setInstance(apiclient)
    addrs = psutil.net_if_addrs()
    print(addrs.keys())
    dialog = ChildDialogCombo(None, addrs.keys(), displayMsg="Choose your ethernet device connected to a domain")
    dialog.app.wait_window(dialog.app)
    nmcli_path = utils.which_expand_alias("nmcli")
    if nmcli_path is None:
        return False, "nmcli is not installed"
    probable_dc = []
    probable_domain = []
    if dialog.rvalue is not None:
        cmd = f"{nmcli_path} dev show {dialog.rvalue}"
        result = subprocess.check_output(cmd, shell=True)
        result = result.decode("utf-8")
        regex_res = re.findall(r"\.DNS\[\d+\]:\s+(\S+)$", result, re.MULTILINE)
        if regex_res:
            probable_dc += regex_res
        regex_res = re.findall(r"\.DOMAIN\[\d+\]:\s+(\S+)$", result, re.MULTILINE)
        if regex_res:
            probable_domain += regex_res
        msg = ""
        if probable_dc:
            msg += "Probable DC founds: "+"\n".join(probable_dc)
        if probable_domain:
            msg += "\nProbable domain found: "+"\n".join(probable_domain)
        if msg == "":
            msg = "No IP found."
        return True, msg
    return None
