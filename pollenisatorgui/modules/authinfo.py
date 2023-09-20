# """User auth infos module to store and use user login informations """
# import tkinter as tk
# import tkinter.messagebox
# import tkinter.ttk as ttk
# from customtkinter import *
# from bson.objectid import ObjectId
# import pollenisatorgui.core.components.utils as utils
# from pollenisatorgui.core.components.apiclient import APIClient
# from pollenisatorgui.core.application.dialogs.ChildDialogProgress import ChildDialogProgress
# from pollenisatorgui.modules.module import Module
#from pollenisatorgui.core.application.pollenisatorentry import PopoEntry

# class AuthInfo(Module):
#     """
#     Shows information about ongoing pentest. 
#     """
#     iconName = "tab_auth.png"
#     tabName = "Auth Infos"
#     coll_name = "auth"
#     order_priority = Module.LOW_PRIORITY
#     pentest_types = ["web"]

#     def __init__(self, parent, settings):
#         """
#         Constructor
#         """
#         super().__init__()
#         self.dashboardFrame = None
#         self.parent = None
#         self.treevw = None
#         self.style = None
#         self.icons = {}
    
#     def open(self):
#         apiclient = APIClient.getInstance()
#         if apiclient.getCurrentPentest() is not None:
#             self.refreshUI()
#         return True

#     def refreshUI(self):
#         """
#         Reload data and display them
#         """
#         self.loadData()
#         self.displayData()

#     def loadData(self):
#         """
#         Fetch data from database
#         """
#         apiclient = APIClient.getInstance()
#         self.auth = apiclient.find("auth")

#     def displayData(self):
#         """
#         Display loaded data in treeviews
#         """
#         dialog = ChildDialogProgress(self.parent, "Loading infos ",
#                                      "Refreshing infos. Please wait for a few seconds.", 200, "determinate")
#         dialog.show(3)

#         # Reset Ip treeview
#         for children in self.treevw.get_children():
#             self.treevw.delete(children)
#         dialog.update(1)
#         for auth_d in self.auth:
#             keys = list(auth_d.keys())

#             self.treevw.insert(
#                 '', 'end', auth_d["_id"], text=auth_d["name"], values=(auth_d["value"], auth_d["type"],))
#         dialog.update(3)
#         # Reset Port treeview
#         dialog.destroy()

#     def initUI(self, parent, nbk, treevw, tkApp):
#         """
#         Initialize Dashboard widgets
#         Args:
#             parent: its parent widget
#         """
#         if self.parent is not None:  # Already initialized
#             return
#         self.parent = parent
#         self.tkApp = tkApp
#         self.treevwApp = treevw
#         self.moduleFrame = CTkFrame(parent)

#         self.rowHeight = 20
#         self.style = ttk.Style()
#         self.style.configure('AuthInfo.Treeview', rowheight=self.rowHeight)

#         frameTwUsers = CTkFrame(self.moduleFrame)
#         self.treevw = ttk.Treeview(
#             frameTwUsers, style='AuthInfo.Treeview', height=10)
#         self.treevw['columns'] = ('name', 'value', 'type')
#         self.treevw.heading("#0", text='Name', anchor=tk.W)
#         self.treevw.column("#0", anchor=tk.W, width=50)
#         self.treevw.heading('value', text='Value')
#         self.treevw.column('value', anchor=tk.W, width=50)
#         self.treevw.heading('type', text='Type')
#         self.treevw.column('type', anchor=tk.W, width=30)
#         self.treevw.grid(row=0, column=0, sticky=tk.NSEW)
#         self.treevw.bind('<Delete>', self.onAuthDelete)
#         scbVSel = CTkScrollbar(frameTwUsers,
#                                 orientation=tk.VERTICAL,
#                                 command=self.treevw.yview)
#         self.treevw.configure(yscrollcommand=scbVSel.set)
#         scbVSel.grid(row=0, column=1, sticky=tk.NS)
#         #frameTwHosts.pack(side=tk.TOP, fill=tk.X, padx=100, pady=10)
#         frameTwUsers.columnconfigure(0, weight=1)
#         frameTwUsers.rowconfigure(0, weight=1)
#         frameTwUsers.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=10)
#         frameActions = CTkFrame(self.moduleFrame)
#         self.text_add_users = CTkTextbox(
#             frameActions, wrap="word")
#         self.text_add_users.pack(side=tk.TOP, padx=10,pady=10,fill=tk.X)
#         self.typeCombo = CTkComboBox(frameActions, values=("Cookie", "Password", "Hash"), state="readonly")
#         self.typeCombo.set("Cookie")
#         self.typeCombo.pack(side=tk.TOP)
#         lblDesc = CTkLabel(frameActions, text="Format is Name:Value (UserName:Cookie or Login:password for exemple. Each entry on a new line)")
#         lblDesc.pack(side=tk.TOP)
#         addBtn = CTkButton(frameActions, text="Add auth info", command=self.insert_auths)
#         addBtn.pack(side=tk.TOP)
#         frameActions.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=10)
#         self.moduleFrame.columnconfigure(0, weight=1)
#         self.moduleFrame.columnconfigure(1, weight=1)
#         self.moduleFrame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
     
#     def onAuthDelete(self, event):
#         """Callback for a delete key press on a worker.
#         Force deletion of worker
#         Args:
#             event: Auto filled
#         """
#         apiclient = APIClient.getInstance()
#         selected = self.treevw.selection()
#         apiclient.bulkDelete({"auth":selected}) 


#     def insert_auths(self):
#         apiclient = APIClient.getInstance()
#         toInsert = []
#         for line in self.text_add_users.get('1.0', tk.END).split("\n"):
#             if line.strip() == "":
#                 continue
#             parts = line.strip().split(":")
#             if len(parts) < 2:
#                 tkinter.messagebox.showerror("Syntax error", f"Format expected is name:value (line : {line})")
#                 return
#             toInsert.append([parts[0],(":".join(parts[1:]))])
#         print(toInsert)
#         for t in toInsert:
#             apiclient.insert("auth", {"name": t[0], "value":t[1], "type":self.typeCombo.get().lower()})

#     def update_received(self, dataManager, notif, obj, old_obj):
#         apiclient = APIClient.getInstance()
#         if apiclient.getCurrentPentest() != notif["db"]:
#             return
#         iid =  notif["iid"]
#         if notif["action"] == "insert":	
#             res = apiclient.find("auth", {"_id": ObjectId(iid)}, False)	
#             if res is None:
#                 return
#             self.treevw.insert(
#                 '', 'end', res["_id"], text=res["name"], values=(res["value"], res["type"],))
#         elif notif["action"] == "delete":
#             try:
#                 self.treevw.delete(str(iid))
#             except tk.TclError:
#                 pass

#     def _initContextualsMenus(self, parentFrame):
#         """
#         Create a contextual menu
#         """
#         self.contextualMenu = utils.craftMenuWithStyle(parentFrame)
#         self.contextualMenu.add_command(
#             label="Add Credentials", command=self.addCredentials)
#         return self.contextualMenu

#     def addCredentials(self, _event=None):
#         dialog = ChildDialogAuthInfo(self.tkApp)
#         self.tkApp.wait_window(dialog.app)
#         if isinstance(dialog.rvalue , dict):
#             apiclient = APIClient.getInstance()
#             name = dialog.rvalue["key"].strip()
#             value = dialog.rvalue["value"].strip()
#             auth_info = {"name": name, "value":value, "type":dialog.rvalue["type"].lower()}
#             res, iid = apiclient.insert("auth", auth_info)
#             for selected in self.treevwApp.selection():
#                 view_o = self.treevwApp.getViewFromId(selected)
#                 if view_o is not None:
#                     res = apiclient.linkAuth(str(iid), view_o.controller.getDbId())

# class ChildDialogAuthInfo:
#     """
#     Open a child dialog of a tkinter application to ask a user a pentest name.
#     """
#     def __init__(self, parent, displayMsg="Add a key value auth info (login:password) (cookie_name:value)"):
#         """
#         Open a child dialog of a tkinter application to ask a combobox option.

#         Args:
#             parent: the tkinter parent view to use for this window construction.
#             displayMsg: The message that will explain to the user what he is choosing.
#             default: Choose a default selected option (one of the string in options). default is None
#         """
#         self.app = CTkToplevel(parent, fg_color=utils.getBackgroundColor())
#         self.app.title("Auth information")
#         self.app.resizable(False, False)
#         appFrame = CTkFrame(self.app)
#         self.rvalue = None
#         self.parent = parent
#         lbl = CTkLabel(appFrame, text=displayMsg)
#         lbl.pack(pady=5)
#         valFrame = CTkFrame(self.app)
#         self.box = CTkComboBox(
#             valFrame, values=tuple(["Password","Cookie"]), state="readonly")
#         self.box.bind('<<ComboboxSelected>>', self.box_modified)  
#         self.box.set("Password")
#         self.box.grid(column=0, row=0)
#         self.lbl_key = CTkLabel(valFrame, text="Login:")
#         self.lbl_key.grid(row=0, column=1)
#         self.entry_key = PopoEntry(valFrame)
#         self.entry_key.grid(row=0, column=2)
#         self.lbl_value = CTkLabel(valFrame, text="Password:")
#         self.lbl_value.grid(row=0, column=3)
#         self.entry_value = PopoEntry(valFrame)
#         self.entry_value.grid(row=0, column=4)
#         valFrame.pack(ipadx=10, ipady=5, pady=10, padx=10)
#         self.ok_button = CTkButton(appFrame, text="OK", command=self.onOk)
#         self.ok_button.bind('<Return>', self.onOk)
#         self.ok_button.pack(padx=10, pady=5, side="right")
#         self.cancel_button = CTkButton(appFrame, text="Cancel", command=self.onError, 
#                                fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
#                                border_width=1, border_color="firebrick1", hover_color="tomato")
#         self.cancel_button.pack(padx=10, pady=5, side="right")
#         appFrame.pack(ipadx=10, ipady=5)
#         try:
#             self.app.wait_visibility()
#             self.app.transient(parent)
#             self.app.grab_set()
#             self.app.focus_force()
#             self.app.lift()
#         except tk.TclError:
#             pass
#         self.box.after(50, self.openCombo)

#     def openCombo(self):
#         self.box.event_generate('<Button-1>')

#     def box_modified(self, event=""):
#         if self.box.get() == "Password":
#             self.lbl_key.configure(text="Login:")
#             self.lbl_value.configure(text="Password:")
#         elif self.box.get() == "Cookie":
#             self.lbl_key.configure(text="Name:")
#             self.lbl_value.configure(text="Value:")

#     def onOk(self, event=""):
#         """
#         Called when the user clicked the validation button. Set the rvalue attributes to the value selected and close the window.
#         """
#         # send the data to the parent
#         self.rvalue = {"type":self.box.get(), "key":self.entry_key.get(), "value":self.entry_value.get()}
#         self.app.destroy()

#     def onError(self):
#         """
#         Close the dialog and set rvalue to None
#         """
#         self.rvalue = None
#         self.app.destroy()
