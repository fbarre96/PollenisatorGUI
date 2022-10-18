"""ActiveDirectory module"""
from ipaddress import IPv4Network, AddressValueError
import tkinter as tk
import tkinter.ttk as ttk
from pollenisatorgui.core.Components.apiclient import APIClient
from pollenisatorgui.core.Application.ScrollableTreeview import ScrollableTreeview
from pollenisatorgui.Modules.Module import Module
from bson import ObjectId
from pollenisatorgui.core.Components.Settings import Settings


class NetworkDiscovery(Module):
    """
    Shows information about ongoing pentest. 
    """
    iconName = "tab_NetDiscovery.png"
    tabName = "Network Discovery"
    collName = "NetworkDiscovery"
    pentest_types = ["lan"]
    
    def __init__(self, parent, settings):
        """
        Constructor
        """
        self.parent = None
        # self.networks = {}
        # self.tools = {}
        self.settings = settings

    def open(self):
        apiclient = APIClient.getInstance()
        if apiclient.getCurrentPentest() is not None:
            self.refreshUI()
        return True

    def refreshUI(self):
        """
        Reload data and display them
        """
        pass
        #self.loadData()
        #self.displayData()

    # def loadData(self):
    #     """
    #     Fetch data from database
    #     """
        #apiclient = APIClient.getInstance()
        # networks = apiclient.find(self.__class__.collName, {})
        # tools = [x for x in apiclient.find("tools", {"lvl":"NetworkDiscovery"})]
        # if tools is None:
        #     self.tools = {}
        # if networks is None:
        #     self.networks = {}
        # for network in networks:
        #     self.networks[network["_id"]] = network
        # for tool in tools:
        #     tool_network = tool["infos"].get("network", "")
        #     self.tools[tool_network] = self.tools.get(tool_network, []) + [tool]

    # def displayData(self):
    #     """
    #     Display loaded data in treeviews
    #     """
        # self.tvNetworks.reset()
        # for network in self.networks.values():
        #     self.insertNetwork(network, self.tools.get(network["network"], []))

    def initUI(self, parent, nbk, treevw, tkApp):
        """
        Initialize Dashboard widgets
        Args:
            parent: its parent widget
        """
        if self.parent is not None:  # Already initialized
            return
        self.parent = parent
        self.tkApp = tkApp
        self.treevwApp = treevw
        self.moduleFrame = ttk.Frame(parent)
        # frameNetworks = ttk.Frame(self.moduleFrame)
        # self.tvNetworks = ScrollableTreeview(
        #     frameNetworks, ("Network", "host count", "tools"), binds={"<Delete>":self.deleteNetwork})
        # self.tvNetworks.pack(fill=tk.BOTH)
        # addNetworkPanel = ttk.Frame(frameNetworks)
        # self.addNetworkEntry = ttk.Entry(addNetworkPanel, width=20)
        # self.addNetworkEntry.pack(side="left")
        # addNetworkButton = ttk.Button(addNetworkPanel, text="Add Network", command=self.addNetwork)
        # addNetworkButton.pack(side="right")
        # addNetworkPanel.pack(side="bottom")
        
        # frameNetworks.grid(row=0, column=0)
        # self.moduleFrame.columnconfigure(0, weight=1)
        # self.moduleFrame.columnconfigure(1, weight=1)
        apiclient = APIClient.getInstance()
        frameActions = ttk.Frame(parent)
        btn = ttk.Button(frameActions, text="try /24 ranges of discovered IPs", command=apiclient.addRangeMatchingIps)
        btn.pack()
        btn = ttk.Button(frameActions, text="try ranges neighours", command=apiclient.addRangeCloseToOthers)
        btn.pack()
        btn = ttk.Button(frameActions, text="try common ranges", command=apiclient.addCommonRanges)
        btn.pack()
        btn = ttk.Button(frameActions, text="try all LAN ranges as /16", command=apiclient.addAllLANRanges)
        btn.pack()
        self.moduleFrame.pack(padx=10, pady=10, side="top", fill=tk.BOTH, expand=True)
        frameActions.pack(padx=10, pady=10, side="top")



    # def insertNetwork(self, network, tools):
    #     try:    
    #         net = network.get("network", "")
    #         self.tvNetworks.insert(
    #             '', 'end', network["_id"], text=net, values=(network["hostCount"],""))
    #     except tk.TclError as e:
    #         pass
    #     if tools is None:
    #         tools = []
    #     for tool in tools:
    #         self.tvNetworks.insert(
    #             network["_id"], 'end', tool["_id"], text=tool["name"], values=(str(tool["status"]),))

    # def addNetwork(self, _event=None):
    #     net = self.addNetworkEntry.get().strip()
    #     try:
    #         IPv4Network(net)
    #     except AddressValueError:
    #         tk.messagebox.showerror("Network invalid", "Invalid ipv4 network given")
    #         return

    #     self.addNetworkInDb(net)

    # def addNetworkInDb(self, network):
    #     apiclient = APIClient.getInstance()
    #     apiclient.insert(self.__class__.collName, {"network": network})
        

    # def deleteNetwork(self, event=None):
    #     apiclient = APIClient.getInstance() 
    #     selection = self.tvNetworks.selection()
    #     for select in selection:
    #         try:
    #             item = self.tvNetworks.item(select)
    #         except tk.TclError:
    #             pass
    #         apiclient.delete(self.__class__.collName, select)       
    #         try:
    #             del self.tools[self.networks[str(select)]["network"]]
    #             del self.networks[str(select)]
    #         except KeyError:
    #             pass
    #         self.tvNetworks.delete(select)

    # def handleNotif(self, collection, iid, action):
    #     apiclient = APIClient.getInstance()
    #     res = apiclient.find(self.__class__.collName, {"_id": ObjectId(iid)}, False)
    #     if action == "insert":
    #         if res is None:
    #             return
    #         if res["type"] == "network":
    #             tools = apiclient.find("tools", {"lvl":"NetworkDiscovery","infos.network":res["network"]}, True)
    #             self.insertNetwork(res, tools)
    #     elif action == "delete":
    #         if res is None:
    #             return
    #         try:
    #             if res["type"] == "network":
    #                 self.tvNetworks.delete(str(iid))
    #         except tk.TclError:
    #             pass

