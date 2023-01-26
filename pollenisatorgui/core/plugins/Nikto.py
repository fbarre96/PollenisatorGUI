from pollenisatorgui.core.plugins.plugin import Plugin
from pollenisatorgui.core.models.port import Port
import webbrowser

class Nikto(Plugin):
    def __init__(self):
        self.toolmodel = None
    def getActions(self, toolmodel):
        """
        Summary: Add buttons to the tool view.
        Args:
            * toolmodel : the tool model opened in the pollenisator client.
        Return:
            A dictionary with buttons text as key and function callback as value.
        """
        self.toolmodel = toolmodel
        return {"Open in browser": self.openInBrowser}

    def openInBrowser(self, _event=None):
        """Callback of action  Open 200 in browser
        Open scanned host port in browser as tabs.
        Args:
            _event: not used but mandatory
        """
        port_m = Port.fetchObject(
            {"ip": self.toolmodel.ip, "port": self.toolmodel.port, "proto": self.toolmodel.proto})
        if port_m is None:
            return
        ssl = port_m.infos.get("SSL", None) == "True" or ("https" in port_m.service or "ssl" in port_m.service)
        url = "https://" if ssl else "http://"
        url += port_m.ip+":"+str(port_m.port)+"/"
        webbrowser.open_new_tab(url)