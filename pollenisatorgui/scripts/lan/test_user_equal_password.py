from pollenisatorgui.core.Components.apiclient import APIClient
import pollenisatorgui.core.Components.Utils as Utils
import tempfile
import os
import shutil

def main(apiclient):
    if not shutil.which("cme"):
        return False, "binary 'cme' is not in the PATH."
    APIClient.setInstance(apiclient)
    unk_users = apiclient.find("ActiveDirectory", {"type":"user", "password":""})
    users_to_test = set()
    domains = set()
    for user in unk_users:
        users_to_test.add((user["domain"], user["username"]))
        domains.add(user["domain"])
    dcs = {}
    exec = 0
    for domain in domains:
        dc_info = apiclient.find("ActiveDirectory", {"type":"computer", "domain":domain, "infos.is_dc":True}, False)
        if dc_info is None:
            continue
        temp_folder = tempfile.gettempdir() 
        file_name = os.path.join(temp_folder, "users_"+str(domain)+".txt")
        users = "\n".join(x[1] for x in users_to_test if x[0] == domain)
        if users.strip() != "":
            with open(file_name, "w") as f:
                f.write(users+"\n")
            exec += 1
            Utils.executeInExternalTerm(f"'pollex cme smb {dc_info['ip']} -u {file_name} -p {file_name} -d {domain} --no-bruteforce --continue-on-success'")
    return True, f"Launched {exec} cmes"
