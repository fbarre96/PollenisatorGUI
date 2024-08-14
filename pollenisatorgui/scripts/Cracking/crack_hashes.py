from bson import ObjectId
from pollenisatorgui.core.components.apiclient import APIClient
import pollenisatorgui.core.components.utils as utils
import os
import subprocess


def main(apiclient, appli, **kwargs):
    if appli:
        from pollenisatorgui.core.application.dialogs.ChildDialogAskFile import ChildDialogAskFile
    print(kwargs)
    john_path = utils.which_expand_alias("john")
    if not john_path:
        return False, "binary 'john' is not in the PATH."
    APIClient.setInstance(apiclient)
    secrets = None
    if kwargs.get("target_type").lower() == "user" or kwargs.get("target_type").lower() == "computer":
        info =  apiclient.find(kwargs.get("target_type").lower()+"s", {"type":kwargs.get("target_type").lower(), "_id":ObjectId(kwargs.get("target_iid", ""))}, False)
        if info is not None:
            secrets = info.get("infos", {}).get("secrets", [])
    if secrets is None:
        if appli:
            dialog = ChildDialogAskFile(None, "Hashes to crack:")
            if dialog.rvalue is None:
                return False, "No hash list given"
            hash_file_name = dialog.rvalue
        else:
            hash_file_name = input("Hashes to crack (abs. path):")
            hash_file_name = os.path.normpath(hash_file_name.strip())

        if not os.path.exists(hash_file_name):
            return False, "hash file list given not found."
    else:
        export_dir = utils.getExportDir()
        out_path = os.path.join(export_dir, str(kwargs.get("target_iid")))
        try:
            os.makedirs(out_path)
        except:
            pass
        hash_file_name = os.path.join(out_path, "secrets.txt")
        with open(hash_file_name, "w") as f:
            f.write("\n".join(secrets))
    if appli:
        dialog = ChildDialogAskFile(None, "wordlist to use:")
        
        if dialog.rvalue is None:
            return False, "No wordlist list given"
    
        wordlist_file_name = dialog.rvalue
    else:
        wordlists_bin = utils.which_expand_alias("fzf-wordlists")
        if wordlists_bin is None:
            wordlist_file_name = input("wordlist to use (abs. path):")
            wordlist_file_name = os.path.normpath(wordlist_file_name.strip())
        else:
            res = os.popen(wordlists_bin)
            wordlist_file_name = res.read().strip()
    if not os.path.exists(wordlist_file_name):
        return False, "wordlist file list given not found."
    if appli:
        appli.launch_in_terminal(kwargs.get("default_target",None), "Crack hashes", f"{john_path} --wordlist={wordlist_file_name} {hash_file_name}")
        appli.launch_in_terminal(kwargs.get("default_target",None), "Result hashes", f"{john_path} --show {hash_file_name}")
    else:
        subprocess.run(f"{john_path} --wordlist={wordlist_file_name} {hash_file_name}")
        subprocess.run(f"{john_path} --show {hash_file_name}")
    return True, f"Launched john in terminal, if it fails, try another wordlist or add rules."
