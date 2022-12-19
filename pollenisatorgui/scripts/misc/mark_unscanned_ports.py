from pollenisatorgui.core.Models.Port import Port
from pollenisatorgui.core.Models.Tool import Tool
from pollenisatorgui.core.Components.apiclient import APIClient


def main(apiclient):
	APIClient.setInstance(apiclient)
	apiclient.registerTag(apiclient.getCurrentPentest(), "unscanned", "yellow")
	ports = Port.fetchObjects({})
	n = 0
	for port in ports:
		port_key = port.getDbKey()
		res = Tool.fetchObject(port_key)
		if res is None:
			port.setTags(["unscanned"])
			n += 1

	return True, f"{n} ports found and marked as unscanned"
