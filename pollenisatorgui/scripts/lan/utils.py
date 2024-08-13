from pollenisatorgui.core.components import utils


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
    