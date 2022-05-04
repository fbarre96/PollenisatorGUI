"""User auth infos module to store and use user login informations """
import tkinter as tk
import tkinter.messagebox
import tkinter.ttk as ttk
from bson.objectid import ObjectId
from pollenisatorgui.core.Components.apiclient import APIClient
from pollenisatorgui.core.Application.Dialogs.ChildDialogProgress import ChildDialogProgress
from pollenisatorgui.core.Views.WaveView import WaveView
from pollenisatorgui.core.Views.IpView import IpView
from pollenisatorgui.core.Views.PortView import PortView
from pollenisatorgui.core.Views.ScopeView import ScopeView
from pollenisatorgui.core.Models.Tool import Tool


class AuthInfo:
    """
    Shows information about ongoing pentest. 
    """
    iconName = "tab_auth.png"
    tabName = " Auth Infos "
    def __init__(self, parent, settings):
        """
        Constructor
        """
        self.dashboardFrame = None
        self.parent = None
        self.treevw = None
        self.style = None
        self.icons = {}
    
    def open(self):
        apiclient = APIClient.getInstance()
        if apiclient.getCurrentPentest() is not None:
            self.refreshUI()
        return True

    def refreshUI(self):
        """
        Reload data and display them
        """
        self.loadData()
        self.displayData()

    def loadData(self):
        """
        Fetch data from database
        """
        apiclient = APIClient.getInstance()
        self.auths = apiclient.find("auths")

    def displayData(self):
        """
        Display loaded data in treeviews
        """
        dialog = ChildDialogProgress(self.parent, "Loading infos ",
                                     "Refreshing infos. Please wait for a few seconds.", 200, "determinate")
        dialog.show(3)

        # Reset Ip treeview
        for children in self.treevw.get_children():
            self.treevw.delete(children)
        dialog.update(1)
        auth = []
        for auth in self.auths:
            keys = list(auth.keys())

            self.treevw.insert(
                '', 'end', auth["_id"], text=auth["name"], values=(auth["value"], auth["type"],))
        dialog.update(3)
        # Reset Port treeview
        dialog.destroy()

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
        self.treevw = treevw
        self.moduleFrame = ttk.Frame(parent)

        self.rowHeight = 20
        self.style = ttk.Style()
        self.style.configure('AuthInfo.Treeview', rowheight=self.rowHeight)

        frameTwUsers = ttk.Frame(self.moduleFrame)
        self.treevw = ttk.Treeview(
            frameTwUsers, style='AuthInfo.Treeview', height=10)
        self.treevw['columns'] = ('name', 'value', 'type')
        self.treevw.heading("#0", text='Name', anchor=tk.W)
        self.treevw.column("#0", anchor=tk.W, width=50)
        self.treevw.heading('value', text='Value')
        self.treevw.column('value', anchor=tk.W, width=50)
        self.treevw.heading('type', text='Type')
        self.treevw.column('type', anchor=tk.W, width=30)
        self.treevw.grid(row=0, column=0, sticky=tk.NSEW)
        self.treevw.bind('<Delete>', self.onAuthDelete)
        scbVSel = ttk.Scrollbar(frameTwUsers,
                                orient=tk.VERTICAL,
                                command=self.treevw.yview)
        self.treevw.configure(yscrollcommand=scbVSel.set)
        scbVSel.grid(row=0, column=1, sticky=tk.NS)
        #frameTwHosts.pack(side=tk.TOP, fill=tk.X, padx=100, pady=10)
        frameTwUsers.columnconfigure(0, weight=1)
        frameTwUsers.rowconfigure(0, weight=1)
        frameTwUsers.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=10)
        frameActions = ttk.Frame(self.moduleFrame)
        self.text_add_users = tk.scrolledtext.ScrolledText(
            frameActions, relief=tk.SUNKEN, font = ("Sans", 10))
        self.text_add_users.pack(side=tk.TOP, padx=10,pady=10,fill=tk.X)
        self.typeCombo = ttk.Combobox(frameActions, values=("Cookie", "Password", "Hash"), state="readonly")
        self.typeCombo.current(0)
        self.typeCombo.pack(side=tk.TOP)
        lblDesc = ttk.Label(frameActions, text="Format is Name:Value (UserName:Cookie or Login:password for exemple. Each entry on a new line)")
        lblDesc.pack(side=tk.TOP)
        addBtn = ttk.Button(frameActions, text="Add auth info", command=self.insert_auths)
        addBtn.pack(side=tk.TOP)
        frameActions.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=10)
        self.moduleFrame.columnconfigure(0, weight=1)
        self.moduleFrame.columnconfigure(1, weight=1)
        self.moduleFrame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
     
    def onAuthDelete(self, event):
        """Callback for a delete key press on a worker.
        Force deletion of worker
        Args:
            event: Auto filled
        """
        apiclient = APIClient.getInstance()
        selected = self.treevw.selection()
        apiclient.bulkDelete({"auths":selected}) 


    def insert_auths(self):
        apiclient = APIClient.getInstance()
        toInsert = []
        for line in self.text_add_users.get('1.0', tk.END).split("\n"):
            if line.strip() == "":
                continue
            parts = line.strip().split(":")
            if len(parts) < 2:
                tkinter.messagebox.showerror("Syntax error", f"Format expected is name:value (line : {line})")
                return
            toInsert.append([parts[0],(":".join(parts[1:]))])
        print(toInsert)
        for t in toInsert:
            apiclient.insertInDb(apiclient.getCurrentPentest(), "auths", {"name": t[0], "value":t[1], "type":self.typeCombo.get().lower()}, "", True)

    def notify(self, db, collection, iid, action, _parent):
        """
        Callback for the observer implemented in mongo.py.
        Each time an object is inserted, updated or deleted the standard way, this function will be called.

        Args:
            collection: the collection that has been modified
            iid: the mongo ObjectId _id that was modified/inserted/deleted
            action: string "update" or "insert" or "delete". It was the action performed on the iid
            _parent: Not used. the mongo ObjectId of the parent. Only if action in an insert. Not used anymore
        """
        apiclient = APIClient.getInstance()
        if not apiclient.getCurrentPentest() != "":
            return
        if apiclient.getCurrentPentest() != db:
            return
        if collection != "auths":
            return
        if action == "insert":	
            res = apiclient.find("auths", {"_id": ObjectId(iid)}, False)	
            if res is None:
                return
            self.treevw.insert(
                '', 'end', res["_id"], text=res["name"], values=(res["value"], res["type"],))
        elif action == "delete":
            try:
                self.treevw.delete(str(iid))
            except tk.TclError:
                pass

    def _initContextualsMenus(self, parentFrame):
        """
        Create a contextual menu
        """
        self.contextualMenu = tk.Menu(parentFrame, tearoff=0, background='#A8CF4D',
                                      foreground='black', activebackground='#A8CF4D', activeforeground='white')
        self.contextualMenu.add_command(
            label="Add Credentials", command=self.addCredentials)
        return self.contextualMenu

    def addCredentials(self, _event=None):
        dialog = ChildDialogAuthInfo(self.tkApp)
        self.tkApp.wait_window(dialog.app)
        if isinstance(dialog.rvalue , dict):
            apiclient = APIClient.getInstance()
            apiclient.insertInDb(apiclient.getCurrentPentest(), "auths", {"name": dialog.rvalue["key"].strip(), "value":dialog.rvalue["value"].strip(), "type":dialog.rvalue["type"].lower()}, "", True)
        # for selected in self.treevw.selection():
        #     view_o = self.treevw.getViewFromId(selected)
        #     if view_o is not None:
        #         lvl = "network" if isinstance(view_o, ScopeView) else None
        #         lvl = "wave" if isinstance(view_o, WaveView) else lvl
        #         lvl = "ip" if isinstance(view_o, IpView) else lvl
        #         lvl = "port" if isinstance(view_o, PortView) else lvl
        #         if lvl is not None:
        #             inst = view_o.controller.getData()
        #             Tool().initialize()
        #             Terminal.openTerminal(lvl+"|"+inst.get("wave", "Imported")+"|"+inst.get(
        #                 "scope", "")+"|"+inst.get("ip", "")+"|"+inst.get("port", "")+"|"+inst.get("proto", ""))
        #         else:
        #             tk.messagebox.showerror(
        #                 "ERROR : Wrong selection", "You have to select a object that may have tools")

class ChildDialogAuthInfo:
    """
    Open a child dialog of a tkinter application to ask a user a calendar name.
    """
    def __init__(self, parent, displayMsg="Add a key value auth info (login:password) (cookie_name:value)"):
        """
        Open a child dialog of a tkinter application to ask a combobox option.

        Args:
            parent: the tkinter parent view to use for this window construction.
            displayMsg: The message that will explain to the user what he is choosing.
            default: Choose a default selected option (one of the string in options). default is None
        """
        self.app = tk.Toplevel(parent, bg="white")
        self.app.resizable(False, False)
        appFrame = ttk.Frame(self.app)
        self.rvalue = None
        self.parent = parent
        lbl = ttk.Label(appFrame, text=displayMsg)
        lbl.pack(pady=5)
        self.box = ttk.Combobox(
            appFrame, values=tuple(["Password","Cookie"]), state="readonly")
        self.box.bind('<<ComboboxSelected>>', self.box_modified)  
        self.box.set("Password")
        self.lbl_key = ttk.Label(appFrame, text="Login:")
        self.entry_key = ttk.Entry(appFrame)
        self.lbl_value = ttk.Label(appFrame, text="Password:")
        self.entry_value = ttk.Entry(appFrame)
        self.ok_button = ttk.Button(appFrame, text="OK", command=self.onOk)
        self.ok_button.bind('<Return>', self.onOk)
        self.ok_button.pack(padx=10, pady=5)
        appFrame.pack(ipadx=10, ipady=5)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.grab_set()
            self.app.focus_force()
            self.app.lift()
        except tk.TclError:
            pass
        self.box.after(50, self.openCombo)

    def openCombo(self):
        self.box.event_generate('<Button-1>')

    def boxModified(self, event=""):
        if self.box.get() == "Password":
            self.lbl_key.configure(text="Login:")
            self.lbl_value.configure(text="Password:")
        elif self.box.get() == "Cookie":
            self.lbl_key.configure(text="Name:")
            self.lbl_value.configure(text="Value:")

    def onOk(self, event=""):
        """
        Called when the user clicked the validation button. Set the rvalue attributes to the value selected and close the window.
        """
        # send the data to the parent
        self.rvalue = {"type":self.box.get(), "key":self.entry_key.get(), "value":self.entry_value.get()}
        self.app.destroy()

    def onError(self):
        """
        Close the dialog and set rvalue to None
        """
        self.rvalue = None
        self.app.destroy()
