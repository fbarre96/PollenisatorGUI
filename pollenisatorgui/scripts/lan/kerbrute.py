from bson import ObjectId
from pollenisatorgui.core.components.apiclient import APIClient
import pollenisatorgui.core.components.utils as utils
import os
from pollenisatorgui.pollex import pollex_exec


def main(apiclient, appli, **kwargs):
    cme_path = utils.which_expand_alias("cme")
    if not cme_path:
        return False, "binary 'cme' is not in the PATH."
    APIClient.setInstance(apiclient)
    ip = ""
    if kwargs.get("target_type").lower() == "computer":
        computer_info =  apiclient.find("computers", {"type":"computer", "_id":ObjectId(kwargs.get("target_iid", ""))}, False)
        if computer_info is not None:
            ip = computer_info.get("ip", "")
    if ip == "" or ip is None:
        return False, "No ip given"
    if appli:
        from pollenisatorgui.core.application.dialogs.ChildDialogAskFile import ChildDialogAskFile

        dialog = ChildDialogAskFile(None, "List of users to test:")
        if dialog.rvalue is None:
            return False, "No user list given"
        file_name = dialog.rvalue
    else:
        file_name = input("List of users to test (abs. path):")
        file_name = os.path.normpath(file_name.strip())
        if not os.path.isfile(file_name):
            return False, "Userlist given not found."
    if not os.path.isfile(file_name):
        return False, "Userlist given not found."
    if appli:
        appli.launch_in_terminal(kwargs.get("default_target",None), "CME kerberos users", f"{cme_path} ldap {ip} -u {file_name} -p '' -k")
    else:
        pollex_exec( f"{cme_path} ldap {ip} -u {file_name} -p '' -k")
    return True, f"Launched cme in terminal, if an Invalid principal syntax is raised, you did not setup the krb5.conf or DNS for your env"
