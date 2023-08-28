from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.settings import Settings
import tkinter as tk
import json
import pandas as pd

def main(apiclient):
    APIClient.setInstance(apiclient)
    apiclient = APIClient.getInstance()
    pentests_list = apiclient.getPentestList()
    pentests = {}
    for pentest in pentests_list:
        pentests[pentest["nom"]] = pentest
    dialog = ChildDialogAskText(None, "Remove unwanted pentests", default="\n".join([pentest["nom"] for pentest in pentests_list]))
    dialog.app.wait_window(dialog.app)
    pentests_name = dialog.rvalue
    defects_stats = []
    for p in pentests_name.split("\n"):
        p = p.strip()
        if p == "":
            continue
        pentest = pentests[p]
        pentest_name = pentest.get("uuid", pentest["nom"])
        pentest_type = apiclient.findInDb(pentest_name, "settings", {"key":"pentest_type"}, False)["value"]
        defects = apiclient.findInDb(pentest_name, "defects", {"ip":""}, True)
        for defect in defects:
            defects_stats.append({"title":defect.get("title",""), "risk":defect.get("risk",""),
                            "date":pentest["creation_date"], "pentest_type":pentest_type})
    f = tk.filedialog.asksaveasfilename(parent=None, defaultextension=".json")
    # asksaveasfile return `None` if dialog closed with "cancel".
    with open(f, "w") as f:
        f.write(json.dumps(defects_stats, indent=4))
    df = pd.DataFrame(defects_stats)
    
    f = tk.filedialog.asksaveasfilename(parent=None, defaultextension=".csv")
    # asksaveasfile return `None` if dialog closed with "cancel".
    df.to_csv(f, index=False)
    return True, f"Dumped"
