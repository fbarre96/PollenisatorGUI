import pollenisatorgui.core.Components.Utils as Utils
import shutil
from pollenisatorgui.core.Components.apiclient import APIClient

def main(apiclient):
	APIClient.setInstance(apiclient)
	if not shutil.which("gowitness"):
		return False, "binary 'gowitness' is not in the PATH."
	Utils.executeInExternalTerm("gowitness server & firefox localhost:7171")
	return True, f"Opened in firefox"
