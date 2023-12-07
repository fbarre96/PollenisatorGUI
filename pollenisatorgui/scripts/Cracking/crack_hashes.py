from bson import ObjectId
from pollenisatorgui.core.application.dialogs.ChildDialogAskFile import ChildDialogAskFile
from pollenisatorgui.core.components.apiclient import APIClient
import pollenisatorgui.core.components.utils as utils
import os


def main(apiclient, appli, **kwargs):
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
        dialog = ChildDialogAskFile(None, "Hashes to crack:")
        if dialog.rvalue is None:
            return False, "No hash list given"
        hash_file_name = dialog.rvalue
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
    dialog = ChildDialogAskFile(None, "wordlist to use:")
    
    if dialog.rvalue is None:
        return False, "No wordlist list given"
    wordlist_file_name = dialog.rvalue
    if not os.path.exists(wordlist_file_name):
        return False, "wordlist file list given not found."
    iid = appli.launch_in_terminal(kwargs.get("default_target",None), "Crack hashes", f"{john_path} --wordlist={wordlist_file_name} {hash_file_name}")
    iid = appli.launch_in_terminal(kwargs.get("default_target",None), "Result hashes", f"{john_path} --show {hash_file_name}")
    return True, f"Launched john in terminal, if it fails, try another wordlist or add rules."
