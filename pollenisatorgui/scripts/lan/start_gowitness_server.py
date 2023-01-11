import pollenisatorgui.core.Components.Utils as Utils
import shutil
import os
from pollenisatorgui.core.Components.apiclient import APIClient

def main(apiclient):
	APIClient.setInstance(apiclient)
	if not shutil.which("gowitness"):
		return False, "binary 'gowitness' is not in the PATH."
	gowitness_tools = apiclient.find("tools", {"status":"done",  "name":{"$regex": "Gowitness"}})
	export_dir = Utils.getExportDir()
	pentest = apiclient.getCurrentPentest().replace("/", "_")
	output_dir = os.path.join(export_dir, "gowitness_server/", pentest)
	os.system("rm -rf  "+str(output_dir))
	merge_str = ""
	for gowitness_tool in gowitness_tools:
		path = apiclient.getResult(str(gowitness_tool["_id"]), output_dir)
		os.system("unzip "+str(path) +" -d "+str(output_dir))
		merge_str += " -i "+path.replace(".zip", ".sqlite3")
	if merge_str == "":
		return False, "No done gotwitness found."
	Utils.executeInExternalTerm(f"gowitness merge{merge_str} -o {output_dir}/gowitness.sqlite3 & gowitness server -D {output_dir}/gowitness.sqlite3 -P {output_dir}/ & firefox localhost:7171")
	return True, f"Opened in firefox"
