import subprocess
import pollenisatorgui.core.components.utils as utils
import psutil
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.scripts.lan.utils import checkPath, getNICs
import os
import re

def main(apiclient, appli, **kwargs):
        
    APIClient.setInstance(apiclient)
    try:
        eth = getNICs(graphical=appli is not None)
    except ValueError as e:
        return False, str(e)
    nmcli_path = utils.which_expand_alias("nmcli")
    if nmcli_path is None:
        return False, "nmcli is not installed"
    probable_dc = []
    probable_domain = []
    if eth is not None:
        cmd = f"{nmcli_path} dev show {eth}"
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
