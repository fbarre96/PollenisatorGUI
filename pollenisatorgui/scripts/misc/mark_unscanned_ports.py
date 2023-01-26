from pollenisatorgui.core.models.port import Port
from pollenisatorgui.core.models.tool import Tool
from pollenisatorgui.core.components.apiclient import APIClient


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
