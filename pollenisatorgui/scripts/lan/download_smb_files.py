from bson import ObjectId
from pollenisatorgui.core.application.dialogs.ChildDialogAskFile import ChildDialogAskFile
from pollenisatorgui.core.components.apiclient import APIClient
import pollenisatorgui.core.components.utils as utils
import os


def main(apiclient, appli, **kwargs):
    cme_path = utils.which_expand_alias("cme")
    if not cme_path:
        return False, "binary 'cme' is not in the PATH."
    APIClient.setInstance(apiclient)
    ip = ""
    if kwargs.get("target_type").lower() == "share":
        share_info =  apiclient.find("shares", {"type":"share", "_id":ObjectId(kwargs.get("target_iid", ""))}, False)
        if share_info is not None:
            ip = share_info.get("ip", "")
    if ip == "" or ip is None:
        return False, "No ip given"
    files_to_download = share_info.get("infos", {}).get("flagged_files", [])
    export = utils.getExportDir()    
    export_dir = os.path.join(export,share_info.get("ip", ""), share_info.get("share", ""))
    try:
        os.makedirs(export_dir, exist_ok=True)
    except OSError:
        pass
    commands = []
    for file in share_info.get("files" ,[]):
        if file["users"] and file["flagged"]:
            file_name = file["path"].replace(share_info["share"], "", 1)[1:]
            export_path = os.path.join(export_dir, os.path.basename(file_name))
            user_info =  apiclient.find("users", {"type":"user","username":file["users"][0][1], "domain":file["users"][0][0]}, False)
            if user_info and user_info.get("password", "") != "":
                commands.append(f'{cme_path} smb {ip} -d {file["users"][0][0]} -u {file["users"][0][1]} -p {user_info.get("password")} --share {share_info["share"]} --get-file {file_name} {export_path}')
    iid = appli.launch_in_terminal(kwargs.get("default_target",None), "CME download files", " && ".join(commands), use_pollex=False)
    utils.openPathForUser(export_dir)
    
    return True, f"Launched cme in terminal"
