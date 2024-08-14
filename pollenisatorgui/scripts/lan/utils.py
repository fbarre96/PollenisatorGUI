from getpass import getpass
from pollenisatorgui.core.components import utils
import psutil


def findDc(apiclient, domain=None, ask_if_fail=True, graphical=False):
    search = {"type":"computer", "infos.is_dc":True}
    if domain is not None:
        search["domain"] = domain
    dc_info = apiclient.find("computers", search, False)
    if dc_info is None:
        if not ask_if_fail:
            return False, "DC not known"
        if graphical:
            from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
            dialog = ChildDialogAskText(None, "DC not known, give me its IP if you know it", multiline=False)
            dialog.app.wait_window(dialog.app)
            dc = dialog.rvalue
        else:
            dc = input("DC not found, give me its IP if you know it:")
    else:
        dc = dc_info.get("ip")
    if dc is None or dc == "":
        return False, "DC not known"
    return True, dc
    

def checkPath(appnames):
    if isinstance(appnames, str):
        appnames = [appnames]
    for appname in appnames:
        path = utils.which_expand_alias(appname)
        if path is not None:
            return True, path
    return False, "App name not found, create an alias or install it. ("+", ".join(appnames)+" were tested)"
    
def getNICs(graphical=False):
    addrs = psutil.net_if_addrs()
    addrs_keys = list(addrs.keys())
    if graphical:
        from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo

        dialog = ChildDialogCombo(None, addrs_keys, displayMsg="Choose your ethernet device to listen on")
        dialog.app.wait_window(dialog.app)
        if dialog.rvalue is None:
            raise ValueError("No ethernet device chosen")
        eth = dialog.rvalue
    else:
        
        print("Choose your ethernet device to listen on")
        for i, ethitem in enumerate(addrs_keys):
            print(str(i+1)+". "+ethitem)

        eth = input("Choose your ethernet device to listen on (type its number):")
        if eth is None:
            raise ValueError("No ethernet device chosen")
        try:
            eth = addrs_keys[int(eth)-1]
        except ValueError:
            raise ValueError("Wrong number given")
    if eth is None or eth == "":
        raise ValueError("No ethernet device chosen")
        
    return eth


def ask_text(graphical, title, default, secret=False):
    if graphical:
        from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
        dialog = ChildDialogAskText(None, title, default, secret)
        return dialog.rvalue
    else:
        if secret:
            res = getpass(title+ " (or default to :"+str(default)+")")
        res = input(title+" (or default to :"+str(default)+")").strip()
        if res == "" or res is None:
            return default
        return res