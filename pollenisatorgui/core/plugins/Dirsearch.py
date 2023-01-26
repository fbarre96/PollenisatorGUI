from pollenisatorgui.core.plugins.plugin import Plugin
from pollenisatorgui.core.models.port import Port
import webbrowser

class Dirsearch(Plugin):

    def __init__(self):
        """Constructor"""
        self.toolmodel = None
        self.port_m = None

    def getActions(self, toolmodel):
        """
        Summary: Add buttons to the tool view.
        Args:
            toolmodel : the tool model opened in the pollenisator client.
        Return:
            A dictionary with buttons text as key and function callback as value.
        """
        self.toolmodel = toolmodel
        self.port_m = Port.fetchObject(
            {"ip": toolmodel.ip, "port": toolmodel.port, "proto": toolmodel.proto})
        if self.port_m is None:
            return {}
        return {"Open 200 in browser": self.openInBrowser}

    def openInBrowser(self, _event=None):
        """Callback of action  Open 200 in browser
        Open scanned host port in browser as tabs.
        Args:
            _event: not used but mandatory
        """
        if self.port_m is None:
            return
        ssl = self.port_m.infos.get("SSL", None) == "True" or ("https" in self.port_m.service or "ssl" in self.port_m.service)
        protocol = "https://" if ssl else "http://"
        dirs = self.port_m.infos.get("Dirsearch_200", [])
        if len(dirs) > 10:
            return "Too much 200 to be opened this way"
        for finding in dirs:
            url = protocol+self.port_m.ip+":"+str(self.port_m.port)+finding
            webbrowser.open_new_tab(url)