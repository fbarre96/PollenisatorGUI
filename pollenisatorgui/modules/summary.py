# """Controllers for summary view of notebook"""
# import tkinter.ttk as ttk
# from customtkinter import *
# import tkinter as tk
# from pollenisatorgui.core.application.dialogs.ChildDialogProgress import ChildDialogProgress
# from pollenisatorgui.core.application.scrollableframexplateform import ScrollableFrameXPlateform
# from pollenisatorgui.core.models.ip import Ip
# from pollenisatorgui.core.models.port import Port
# from pollenisatorgui.core.components.settings import Settings
# from pollenisatorgui.core.components.apiclient import APIClient
# from pollenisatorgui.modules.module import Module

# def smart_grid(parent, root, *args, **kwargs):  # *args are the widgets!
#     """Grid adapted to each treeview size.
#     Adapted from stackoverflow but cannot find it anymore =/"""
#     divisions = kwargs.pop('divisions', 100)
#     force_f = kwargs.pop('force', False)
#     if 'sticky' not in kwargs:
#         kwargs.update(sticky='w')
#     try:
#         parent.win_width
#     except AttributeError:
#         parent.win_width = -1
#     parent.update_idletasks()
#     root.update_idletasks()
#     winfo_width = root.winfo_reqwidth()
#     if 1 < winfo_width != parent.win_width or force_f:
#         parent.win_width = winfo_width
#         row = col = width = 0
#         argc = len(args)

#         for i in range(argc):
#             widget_width = args[i].winfo_reqwidth()
#             columns = max(
#                 1, int(widget_width * float(divisions) / winfo_width))
#             width += widget_width
#             if width > winfo_width:
#                 width = widget_width
#                 row += 1
#                 col = 0
#             args[i].grid(row=row, column=col, columnspan=columns, **kwargs)
#             col += columns
#         parent.update_idletasks()  # update() #
#         return row + 1


# class Summary(Module):
#     """
#     Store elements to summarize the ongoing pentest
#     """
#     iconName = "tab_summary.png"
#     tabName = "  Summary  "
#     order_priority = Module.MEDIUM_PRIORITY
#     def __init__(self, root, settings):
#         """Constructor
#         Args:
#             root: the root widget of tkinter
#         """
#         super().__init__()
#         self.linkTw = None
#         self.root = root
#         self.treeviews = {}
#         self.parent = None
#         self.nbk = None
#         self.summaryFrame = None
#         self.scroller = None
#         self.frameTw = None
    
#     def open(self):
#         apiclient = APIClient.getInstance()
#         if apiclient.getCurrentPentest() is not None:
#             self.refreshUI()
#         return True

#     def refreshUI(self):
#         """Refresh information then reloads the view with them.
#         """
#         if self.frameTw is not None:
#             for widget in self.frameTw.winfo_children():
#                 widget.destroy()
#         if self.summaryFrame is not None:
#             for widget in self.summaryFrame.winfo_children():
#                 widget.destroy()
#         if self.treeviews is not None:
#             for k in list(self.treeviews.keys()):
#                 del self.treeviews[k]
#             del self.treeviews
#         self.treeviews = {}
#         self.frameTw = CTkFrame(self.summaryFrame)
#         self.frameTw.pack(side=tk.LEFT, padx=10, pady=10)
#         self.loadSummary()

#     def initUI(self, parent, nbk, linkTw, tkApp):
#         """Initialize widgets of the summary
#         Args:
#             parent: parent tkinter container widget 
#             nbk: a ref to the notebook
#             linkTw: the treeview holding more info in the notebook to be displayed after an interaction
#         """
#         self.parent = parent
#         self.nbk = nbk
#         if self.linkTw is not None:  # UI Already built
#             self.linkTw = linkTw
#             self.refreshUI()
#             return
#         self.linkTw = linkTw
#         self.summaryFrame = ScrollableFrameXPlateform(self.parent)
#         self.summaryFrame.pack(side=tk.TOP, anchor=tk.W, expand=True,
#                                fill=tk.BOTH, padx=10, pady=10)

#     def loadSummary(self):
#         """Reload information about IP and Port and reload the view.
#         """
#         apiclient = APIClient.getInstance()
#         nonEmptyIps = list(apiclient.aggregate("ports",[{"$group":{"_id":"$ip"}}, {"$count": "total"}]))
#         if not nonEmptyIps:
#             return
#         nonEmptyIps = nonEmptyIps[0]
#         step = 0
#         dialog = ChildDialogProgress(self.parent, "Loading summary ", "Refreshing summary. Please wait for a few seconds.", 200, "determinate")
#         dialog.show(nonEmptyIps["total"])
#         nonEmptyIps = apiclient.aggregate("ports",[{"$group":{"_id":"$ip"}}])
#         for ipCIDR in nonEmptyIps:
#             step += 1
#             ip = Ip.fetchObject({"ip": ipCIDR["_id"]})
#             if ip is None:
#                 continue
#             if ip.in_scopes:
#                 try:
#                     dialog.update(step)
#                 except tk.TkError as e:
#                     #probably claused the windows, stopping
#                     break
#                 self.insertIp(ip.ip)
#         self.frameTw.update_idletasks()
#         self.parent.update_idletasks()
#         smart_grid(self.frameTw, self.root, *list(self.treeviews.values()))
#         dialog.destroy()


#     def OnDoubleClick(self, event):
#         """Callback for treeview double click.
#         If a link treeview is defined, open mainview and focus on the item with same iid clicked.
#         Args:
#             event: used to identified which link was clicked. Auto filled
#         """
#         if self.linkTw is not None:
#             self.nbk.select("Main View")
#             tv = event.widget
#             item = tv.identify("item", event.x, event.y)
#             self.linkTw.focus(item)
#             self.linkTw.see(item)
#             self.linkTw.selection_set(item)

#     def updatePort(self, port_data):
#         """Update a port line according to a new port_data (just change colors now)
#         Args:
#             port_data: a port data dictionnary
#         """
#         newTags = port_data.get("tags", [])
#         treeviewToUpdate = self.treeviews.get(port_data["ip"], None)
#         if treeviewToUpdate is not None:
#             if port_data.get("_id", None) is not None:
#                 try:
#                     treeviewToUpdate.item(str(port_data["_id"]), tags=newTags)
#                 except:
#                     pass

#     def insertPort(self, port_o):
#         """Insert a new port in the summary
#         Args:
#             port_o: a port object to be inserted
#         """
#         treeviewToUpdate = self.treeviews.get(port_o["ip"], None)
#         if treeviewToUpdate is None:
#             self.insertIp(port_o["ip"])
#         treeviewToUpdate = self.treeviews.get(port_o["ip"], None)
#         port_text = port_o["port"]
#         if port_o["proto"] == "udp":
#             port_text = "udp/"+port_text
#         treeviewToUpdate.configure(height=len(treeviewToUpdate.get_children())+1)
#         treeviewToUpdate.insert('', 'end', str(
#             port_o["_id"]), text=port_text, tags=list(port_o["tags"]))

#     def insertIp(self, ip):
#         """Insert a new IP in the summary. Also insert its port
#         Args:
#             ip: an IP object to be inserted
#         """
#         treevw = ttk.Treeview(self.frameTw)
#         treevw.heading("#0", text=ip, anchor='w')
#         treevw.column("#0", anchor='w')
#         tags = Settings.getTags()
#         for tag, color in tags.items():
#             if color == "transparent": 
#                 continue
#             treevw.tag_configure(tag, background=color)
#         treevw.bind("<Double-Button-1>", self.OnDoubleClick)
#         count = 0
#         self.treeviews[ip] = treevw
#         ports = Port.fetchObjects({"ip": ip})
#         for port in ports:
#             if port.proto.strip() != "" and str(port.port).strip() != "":
#                 port_text = port.port
#                 if port.proto == "udp":
#                     port_text = "udp/"+port_text
#                 try:
#                     treevw.insert('', 'end', str(port.getId()),
#                               text=port_text, tags=list(port.getTags()))
#                 except:
#                     pass
#                 count += 1
#         treevw.configure(height=count)
#         treevw.update_idletasks()

#     def deleteIp(self, ip):
#         """Remvoe an IP from the summary.
#         Args:
#             ip: an IP object to be removed
#         """
#         if self.treeviews.get(ip, None) is not None:
#             del self.treeviews[ip]
