"""ActiveDirectory module"""
import tkinter as tk
import tkinter.ttk as ttk
import os
import re
from pollenisatorgui.core.Components.apiclient import APIClient
from pollenisatorgui.core.Application.Dialogs.ChildDialogProgress import ChildDialogProgress
from pollenisatorgui.core.Application.Dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.Application.Dialogs.ChildDialogAskText import ChildDialogAskText
from pollenisatorgui.core.Application.Dialogs.ChildDialogAskFile import ChildDialogAskFile
from pollenisatorgui.core.Application.ScrollableTreeview import ScrollableTreeview
from pollenisatorgui.core.Models.Port import Port
from pollenisatorgui.core.Forms.FormPanel import FormPanel
import tempfile
from bson import ObjectId
import pollenisatorgui.core.Components.Utils as Utils
from pollenisatorgui.core.Components.Settings import Settings

class ActiveDirectory:
    """
    Shows information about ongoing pentest. 
    """
    iconName = "tab_AD.png"
    tabName = "Active Directory"
    collName = "ActiveDirectory"
    settings = Settings()
    registerLvls = []
    running_commands = []

    def __init__(self, parent, settings):
        """
        Constructor
        """
        self.parent = None
        self.users = {}
        self.computers = {}
        self.shares = {}

    @classmethod
    def getSettings(cls):
        return cls.settings.local_settings.get(ActiveDirectory.collName, {})

    @classmethod
    def saveSettings(cls, newSettings):
        cls.settings.local_settings[ActiveDirectory.collName] = newSettings
        cls.settings.saveLocalSettings()

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
        self.reloadSettings()

    def loadData(self):
        """
        Fetch data from database
        """
        apiclient = APIClient.getInstance()
        dialog = ChildDialogProgress(self.parent, "Loading infos ",
                                     "Refreshing infos. Please wait for a few seconds.", 200, "determinate")
        dialog.show(5)
        dialog.update(0)
        self.users = apiclient.findInDb(apiclient.getCurrentPentest(
        ), ActiveDirectory.collName, {"type": "user"}, True)
        dialog.update(1)
        if self.users is None:
            self.users = []
        self.computers = apiclient.findInDb(apiclient.getCurrentPentest(
        ), ActiveDirectory.collName, {"type": "computer"}, True)
        dialog.update(2)
        if self.computers is None:
            self.computers = []
        self.shares = apiclient.findInDb(apiclient.getCurrentPentest(
        ), ActiveDirectory.collName, {"type": "share"}, True)
        dialog.update(3)
        if self.shares is None:
            self.shares = []
        ports = Port.fetchObjects({"port":str(445)})
        #for port in ports:
        #    self.loadInfoFromPort(port)
        dialog.update(4)
        # ports = Port.fetchObjects({"port":str(88)})
        # for port in ports:
        #     self.addDCinDb(port.ip)
        dialog.update(5)
        dialog.destroy()
            
    def displayData(self):
        """
        Display loaded data in treeviews
        """
        dialog = ChildDialogProgress(self.parent, "Displaying infos ",
                                     "Refreshing infos. Please wait for a few seconds.", 200, "determinate")
        dialog.show(4)

        self.tvUsers.reset()
        self.tvComputers.reset()
        self.tvShares.reset()
        dialog.update(1)
        for i,user in enumerate(self.users):
            if i > 100:
                break
            self.insertUser(user)
        dialog.update(2)
        for i,computer in enumerate(self.computers):
            if i > 100:
                break
            self.insertComputer(computer)
        dialog.update(3)
        for i,share in enumerate(self.shares):
            if i > 100:
                break
            self.insertShare(share)
        dialog.update(4)
        dialog.destroy()

    def mapLambda(self, c):
        if c[0].lower() in ["computer", "oncomputernewuser", "oncomputerfirstuser", "oncomputerfirstadmin", "ondcfirstuser", "ondcfirstadmin"]:
            return lambda : self.computerCommand(c[2])
        elif c[0].lower() == "share":
            return lambda : self.shareCommand(c[2])

    def reloadSettings(self):
        s = self.getSettings()
        listOfLambdas = [self.mapLambda(c) for c in s.get("commands", [])]
        i = 0
        for command_options in s.get("commands", []):
            if command_options[0].lower() in ["computer", "oncomputernewuser", "oncomputerfirstuser", "oncomputerfirstadmin", "ondcfirstuser", "ondcfirstadmin"]:
                self.tvComputers.addContextMenuCommand(command_options[1], listOfLambdas[i])
            elif command_options[0].lower() == "share":
                self.tvShares.addContextMenuCommand(command_options[1], listOfLambdas[i])
            i+=1
        

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
        settings_btn = ttk.Button(parent, text="Configure this module", command=self.openConfig)
        settings_btn.pack(side="bottom")
        self.moduleFrame = ttk.Frame(parent)
        frameUsers = ttk.Frame(self.moduleFrame)
        self.tvUsers = ScrollableTreeview(
            frameUsers, ("Username", "Password", "Domain", "N° groups","Desc"), binds={"<Delete>":self.deleteUser, "<Double-Button-1>":self.userDoubleClick})
        self.tvUsers.pack(fill=tk.BOTH)
        addUserButton = ttk.Button(frameUsers, text="Add user manually", command=self.addUsersDialog)
        addUserButton.pack(side="bottom")
        frameComputers = ttk.Frame(self.moduleFrame)
        self.tvComputers = ScrollableTreeview(
            frameComputers, ("IP", "Name", "Domain", "DC", "Admin count", "User count", "OS", "Signing", "SMBv1"), binds={"<Double-Button-1>":self.computerDoubleClick})
        self.tvComputers.pack(fill=tk.BOTH)
        frameShares = ttk.Frame(self.moduleFrame)
        self.tvShares = ScrollableTreeview(
            frameShares, ("IP", "Share", "Flagged", "Priv", "Size", "domain", "user"))
        self.tvShares.pack(fill=tk.BOTH)
        frameUsers.grid(row=0, column=0)
        frameComputers.grid(row=1, column=0)
        frameShares.grid(row=2, column=0)
        self.moduleFrame.columnconfigure(0, weight=1)
        self.moduleFrame.columnconfigure(1, weight=1)
        self.moduleFrame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def computerDoubleClick(self, event=None):
        selection = self.tvComputers.selection()[0]
        self.openComputerDialog(selection)

    def openComputerDialog(self, computer_iid):
        apiclient = APIClient.getInstance()
        computer_d = apiclient.findInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName,
            {"_id":ObjectId(computer_iid)}, False)
        if computer_d is None:
            return
        dialog = ChildDialogComputer(self.parent, computer_d)
        self.parent.wait_window(dialog.app)

    def insertUser(self, user):
        try:
            domain = user.get("domain", "")
            username = user.get("username", "")
            password = user.get("password", "")
            self.tvUsers.insert(
                '', 'end', user["_id"], text=username, values=(password, domain, len(user.get("groups", [])), user.get("desc", "")))
            self.newUserEvent("OnUserInsert", user=(domain, username, password))
        except tk.TclError:
            pass

    def userDoubleClick(self, event=None):
        selection = self.tvUsers.selection()[0]
        self.openUserDialog(selection)

    def openUserDialog(self, user_iid):
        apiclient = APIClient.getInstance()
        user_d = apiclient.findInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName,
            {"_id":ObjectId(user_iid)}, False)
        if user_d is None:
            return
        dialog = ChildDialogUser(self.parent, user_d)
        self.parent.wait_window(dialog.app)


    def deleteUser(self, event=None):
        apiclient = APIClient.getInstance() 
        selection = self.tvUsers.selection()
        for select in selection:
            try:
                item = self.tvUsers.item(select)
            except tk.TclError:
                pass
            username = item["text"]
            values = item["values"]
            password = values[0]
            domain = values[1] if values[1] != "None" and values[1] != "" else None
            computers = apiclient.findInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName, 
                {"type":"computer", "users":{"$elemMatch":{"0":domain,"1":username,"2":password}}}, True)
            for computer in computers:
                users = [ u for u in computer.get("users") if domain != u[0] and username != u[1] and username != u[2]]
                admins = [ u for u in computer.get("admins") if domain != u[0] and username != u[1] and username != u[2]]
                apiclient.updateInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName, 
                {"_id":ObjectId(computer["_id"])}, {"$set":{"users":users, "admins":admins}}, notify=True)
            apiclient.deleteFromDb(apiclient.getCurrentPentest(), ActiveDirectory.collName, {"_id":ObjectId(select)}, notify=True)       
            self.tvUsers.delete(select)
    
    def insertComputer(self, computer):
        newValues = (computer.get("name", computer.get("machine_name", "")), computer.get("domain", ""), str(computer.get("isDC", False)), len(computer.get("admins", [])), len(computer.get("users", [])), computer.get("OS", ""),
                        computer.get("signing", ""), computer.get("SMBv1", ""))
        try:
            self.tvComputers.insert(
                '', 'end', computer["_id"], text=computer.get("ip", ""),
                values=newValues)
        except tk.TclError:
            self.tvComputers.item(computer["_id"], values=newValues) 

    def insertShare(self, share):
        try:
            parentiid = self.tvShares.insert(
                        '', 'end', share["_id"], text=share.get("ip", ""), values=(share.get("name", ""),))
        except tk.TclError:
            parentiid = str(share["_id"])
        for file_infos in share.get("files"):
            toAdd = []
            for info in file_infos:
                if info is None:
                    info = ""
                toAdd.append(str(info))
            try:
                self.tvShares.insert(
                    parentiid, 'end', None, text="", values=(tuple(toAdd)))
            except tk.TclError:
                pass

    def addShareInDb(self, share_dict, port_o):
        apiclient = APIClient.getInstance()
        for shareName, path_infos in share_dict.items():
            existing = apiclient.findInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName, {
                                 "type": "share", "name": shareName, "ip":port_o.ip}, False)
            if existing is None:
                apiclient.insertInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName,
                    {"type": "share", "name": shareName, "ip": port_o.ip,
                    "files":path_infos}, notify=True)
            else:
                files = set(map(tuple, existing["files"]))
                files = list(files.union(set(map(tuple, path_infos))))
                apiclient.updateInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName,
                    {"_id":existing["_id"]}, {"$set":{"type": "share", "name": shareName, "ip": port_o.ip,
                    "files":files}})
    @staticmethod
    def normalize_users(user_records):
        ret = []
        for user_record in user_records:
            if isinstance(user_record, dict):
                domain = user_record.get("domain", "")
                username = user_record.get("username", "")
                password = user_record.get("password", "")
                ret.append([domain, username, password])
            elif isinstance(user_record, list) or isinstance(user_record, tuple):
                ret.append(user_record)
        return ret

    def addUserInDb(self, user):
        apiclient = APIClient.getInstance()
        list_norm_user = ActiveDirectory.normalize_users([user])
        if list_norm_user:
            norm_user = list_norm_user[0]
            if len(norm_user) == 3:
                domain = norm_user[0]
                username = norm_user[1]
                password = norm_user[2]
                key = {"type": "user", "username": username, "domain": domain, "password": password}
                data = key
                res = apiclient.updateInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName, key, {"$set":data}, notify=True, upsert=True)
            
    def addDomainUserInDb(self, user_login, user_infos):
        apiclient = APIClient.getInstance()
        domain = user_login.split("\\")[0]
        username = "\\".join(user_login.split("\\")[1:])
        key = {"type": "user", "username": username, "domain": domain}
        data = user_infos
        apiclient.updateInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName, key, {"$set":data}, notify=True, upsert=True)

    def addDCinDb(self, ip):
        apiclient = APIClient.getInstance()
        existing = apiclient.findInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName, {
                                 "type": "computer", "ip": ip}, False)
        if existing is None:
            apiclient.insertInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName,
                {"type": "computer", "domain":"", "isDC":True, "name": "", "ip": ip,
                 "OS": "", "signing": True, 
                 "SMBv1": "", "users":[],
                 "admins":[]}, notify=True)
        else:
            apiclient.updateInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName,
                                 {"_id": ObjectId(existing["_id"])}, {"$set": {"isDC":True}}, notify=True)
            if not existing.get("isDC", False):
                if len(existing.get("users", [])) > 0:
                    self.newComputerEvent("OnDCFirstUser", existing.get("users", [])[0], ip)
                if len(existing.get("admins", [])) > 0:
                    self.newComputerEvent("OnDCFirstAdmin", existing.get("admins", [])[0], ip)

    def addComputerinDb(self, port_o):
        apiclient = APIClient.getInstance()
        existing = apiclient.findInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName, {
                                 "type": "computer", "ip": port_o.ip}, False)
        existingUsers = []
        newUsers = []
        existingAdmins = []
        newAdmins = []
        isDC = False
        if existing is None:
            newUsers = ActiveDirectory.normalize_users(port_o.infos.get("users", []))
            newAdmins = ActiveDirectory.normalize_users(port_o.infos.get("admins", []))
            apiclient.insertInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName,
                {"type": "computer", "domain":port_o.infos.get("domain",""), "isDC": isDC, "name": port_o.infos.get("machine_name", ""), "ip": port_o.ip,
                 "OS": port_o.infos.get("OS", ""), "signing": port_o.infos.get("signing", ""), "secrets": port_o.infos.get("secrets", ""), "ntds":port_o.infos.get("ntds", ""),
                 "SMBv1": port_o.infos.get("SMBv1", ""), "users":newUsers,
                 "admins":newAdmins}, notify=True)
        else:
            isDC = existing.get("isDC", False)
            existingUsers = set(map(tuple, ActiveDirectory.normalize_users(existing.get("users", []))))
            newUsers = list(existingUsers.union(map(tuple, ActiveDirectory.normalize_users(port_o.infos.get("users", [])))))
            existingAdmins = set(map(tuple, ActiveDirectory.normalize_users(existing.get("admins", []))))
            newAdmins = list(existingAdmins.union(map(tuple, ActiveDirectory.normalize_users(port_o.infos.get("admins", [])))))
            apiclient.updateInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName,
                                 {"_id": ObjectId(existing["_id"])}, {"$set": {"name": port_o.infos.get("machine_name", ""), "domain":port_o.infos.get("domain", ""),"isDC": isDC,
                                                                          "OS": port_o.infos.get("OS", ""), "signing": port_o.infos.get("signing", ""), "secrets": port_o.infos.get("secrets", ""),
                                                                          "ntds":port_o.infos.get("ntds", ""), "SMBv1": port_o.infos.get("SMBv1", ""),
                                                                           "users":newUsers, "admins":newAdmins}})
        self.checkEvents(port_o, existingUsers, newUsers, existingAdmins, newAdmins, isDC)

    def checkEvents(self, port_o, existingUsers, newUsers, existingAdmins, newAdmins, isDC):
        if len(newUsers) > len(existingUsers):
            for user in  set(newUsers) - set(existingUsers):
                self.newComputerEvent("OnComputerNewUser", user, port_o.ip)
        if len(newAdmins) >= 1 and len(existingAdmins) == 0:
            admin = list(set(newAdmins) - set(existingAdmins))[0]
            self.newComputerEvent("OnComputerFirstAdmin", admin, port_o.ip)
            if isDC:
                self.newComputerEvent("OnDCFirstAdmin", admin, port_o.ip)
        if len(newUsers) > 0:
            realNewUsers = set()
            for user in newUsers:
                if not any(map(lambda x: x is None or x == '' or x == 'None', user)):
                    realNewUsers.add(user)
            if len(realNewUsers) > 0:
                oneExistingUser = False
                incompleteUsers = set()
                for user in existingUsers:
                    if not any(map(lambda x: x is None or x == '' or x == 'None', user)):
                        oneExistingUser = True
                        break
                    else:
                        incompleteUsers.add(user)
                if not oneExistingUser:
                    self.newComputerEvent("OnComputerFirstUser", list(set(newUsers) - incompleteUsers)[0], port_o.ip)
                    if isDC:
                        self.newComputerEvent("OnDCFirstUser", list(set(newUsers) - incompleteUsers)[0], port_o.ip)
    
    def newComputerEvent(self, eventName, user, ip):
        apiclient = APIClient.getInstance()
        existing = apiclient.findInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName, {
                                 "type": "computer", "ip": ip}, False)
        if existing is None:
            return
        s = self.getSettings()
        for command_options in s.get("commands", []):
            if command_options[0].lower() == eventName.lower():
                self.computerCommand(command_options[2],  ips=[existing["ip"]], user=user)

    def newUserEvent(self, eventName, user):
        s = self.getSettings()
        for command_options in s.get("commands", []):
            if command_options[0].lower() == eventName:
                self.userCommand(command_options[2],  user=user)

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
        if collection == ActiveDirectory.collName:
            self.handleActiveDirectoryNotif(iid, action)
        elif collection == "ports" and action != "delete":
            port_o = Port.fetchObject({"_id": ObjectId(iid)})
            if int(port_o.port) == 445:
                self.loadInfoFromPort(port_o)
            if int(port_o.port) == 88:
                self.addDCinDb(port_o.ip)

    def loadInfoFromPort(self, port_o):
        if port_o.infos.get("users", []):
            for user in port_o.infos.get("users", []):
                self.addUserInDb(user)
        if port_o.infos.get("domain_users", []):
            for user_login, user_infos in port_o.infos.get("domain_users", {}).items():
                self.addDomainUserInDb(user_login, user_infos)
        if port_o.infos.get("admins", []):
            for admin in port_o.infos.get("admins", []):
                self.addUserInDb(admin)
        self.addComputerinDb(port_o)
        if port_o.infos.get("shares", {}):
            self.addShareInDb(port_o.infos.get("shares", {}), port_o)

    def handleActiveDirectoryNotif(self, iid, action):
        apiclient = APIClient.getInstance()
        res = apiclient.findInDb(apiclient.getCurrentPentest(
                ), ActiveDirectory.collName, {"_id": ObjectId(iid)}, False)
        if action == "insert":
            if res is None:
                return
            if res["type"] == "computer":
                self.insertComputer(res)
            elif res["type"] == "user":
                self.insertUser(res)
            elif res["type"] == "share":
                self.insertShare(res)
        elif action == "update":
            if res is None:
                return
            if res["type"] == "computer":
                self.insertComputer(res)
            if res["type"] == "share":
                self.insertShare(res)
        elif action == "delete":
            if res is None:
                return
            try:
                if res["type"] == "computer":
                    self.tvComputers.delete(str(iid))
                elif res["type"] == "user":
                    self.tvUsers.delete(str(iid))
                elif res["type"] == "share":
                    self.tvShares.delete(str(iid))
            except tk.TclError:
                pass

    def openConfig(self, event=None):
        dialog = ChildDialogConfigureADModule(self.parent)
        self.parent.wait_window(dialog.app)
        if dialog.rvalue is not None and isinstance(dialog.rvalue, list):
            settings = {"commands":[]}
            for values in dialog.rvalue:
                settings["commands"].append(values)
            self.saveSettings(settings)
        self.reloadSettings()
            
    def addUsersDialog(self, event=None):
        dialog = ChildDialogAddUsers(self.parent)
        self.parent.wait_window(dialog.app)
        if dialog.rvalue is not None and isinstance(dialog.rvalue, list):
            lines = dialog.rvalue
            for line in lines:
                if line.strip() != "":
                    parts = line.split("\\")
                    domain = parts[0]
                    remaining = "\\".join(parts[1:])
                    parts = remaining.split(":")
                    username = parts[0]
                    password = ":".join(parts[1:])
                    self.addUserInDb((domain, username, password))
    
    def exportAllUsersAsFile(self, delim="\n"):
        fp = tempfile.mkdtemp()
        filepath = os.path.join(fp, "users.txt")
        with open(filepath, "w") as f:
            for selected_user in self.tvUsers.get_children():
                username = self.tvUsers.item(selected_user)["text"]
                f.write(username+delim)
        return filepath

    def exportAllComputersAsFile(self, delim="\n"):
        fp = tempfile.mkdtemp()
        filepath = os.path.join(fp, "computers.txt")
        with open(filepath, "w") as f:
            for selected_computer in self.tvComputers.get_children():
                computer = self.tvComputers.item(selected_computer)["text"]
                f.write(computer+delim)
        return filepath


    def shareCommand(self, command_option):
        selected = self.tvShares.selection()[0]
        parent_iid = self.tvShares.parent(selected)
        if not parent_iid: # file in share
            return
        ip = self.tvShares.item(parent_iid)["text"]
        item_values = self.tvShares.item(selected)["values"]
        domain = item_values[-2] if item_values[-2] != "" else None
        user = item_values[-1]
        share_name = item_values[0]
        apiclient = APIClient.getInstance()
        apiclient.getCurrentPentest()
        user_o = apiclient.findInDb(apiclient.getCurrentPentest(), ActiveDirectory.collName, 
                {"type":"user", "domain":domain, "username":user}, False)
        if user_o is None:
            tk.messagebox.showerror("user not found","User "+str(domain)+"\\"+str(user)+" was not found")
            return
        user = "" if user is None else user
        domain = "" if domain is None else domain
        command_option = command_option.replace("|username|", user)
        command_option = command_option.replace("|domain|", domain)
        command_option = command_option.replace("|password|", user_o["password"])
        command_option = command_option.replace("|share|",share_name.replace("\\\\", "\\"))
        command_option = command_option.replace("|ip|",ip)
        Utils.executeInExternalTerm(command_option)

    def userCommand(self, command_option, user):
        if user is None:
            selection_users = self.tvUsers.selection()
            if len(selection_users) >= 1:
                item = self.tvUsers.item(selection_users[0])
                user = (item["values"][1], item["text"], item["values"][0])
            else:
                user = None
        searching = [r"ask_text:([^:\|]+)", "computers_as_file"]
        for keyword in searching:
            s = re.search(r"\|"+keyword+r"\|", command_option)
            if s is not None:
                if keyword == "computers_as_file":
                    filepath = self.exportAllComputersAsFile()
                    command_option = command_option.replace(s.group(0), filepath)
                elif "|ask_text:" in s.group(0):
                    what = s.group(1)
                    dialog = ChildDialogAskText(self.tkApp, what)
                    self.tkApp.wait_window(dialog.app)
                    fp = tempfile.mkdtemp()
                    filepath = os.path.join(fp, what+".txt")
                    with open(filepath, "w") as f:
                        f.write(dialog.rvalue)
                    command_option = command_option.replace(s.group(0), filepath)
            command_option = command_option.replace("|domain|", user[0])
            command_option = command_option.replace("|username|", user[1])
            command_option = command_option.replace("|password|", user[2])
        Utils.executeInExternalTerm(command_option)

    def computerCommand(self, command_option, ips=None, user=None):
        if ips is None:
            ips = []
            selection = self.tvComputers.selection()
            for selected in selection:
                item = self.tvComputers.item(selected)
                ip = item["text"]
                ips.append(ip)
        if user is None:
            selection_users = self.tvUsers.selection()
            if len(selection_users) >= 1:
                item = self.tvUsers.item(selection_users[0])
                user = (item["values"][1], item["text"], item["values"][0])
            else:
                user = None
        for ip in ips:
            searching = ["wordlist", r"ask_text:([^:\|]+)", "users_as_file", "ip"]
            for keyword in searching:
                s = re.search(r"\|"+keyword+r"\|", command_option)
                if s is not None:
                    if keyword == "wordlist":
                        dialog = ChildDialogAskFile(self.tkApp, f"Choose a wordlist file")
                        command_option = command_option.replace(s.group(0), dialog.rvalue)
                    elif keyword == "ip":
                        command_option = command_option.replace(s.group(0), ip)
                    elif keyword == "users_as_file":
                        filepath = self.exportAllUsersAsFile()
                        command_option = command_option.replace(s.group(0), filepath)
                    elif "|ask_text:" in s.group(0):
                        what = s.group(1)
                        dialog = ChildDialogAskText(self.tkApp, what)
                        self.tkApp.wait_window(dialog.app)
                        fp = tempfile.mkdtemp()
                        filepath = os.path.join(fp, what+".txt")
                        with open(filepath, "w") as f:
                            f.write(dialog.rvalue)
                        command_option = command_option.replace(s.group(0), filepath)
            user_searching = {"domain":None, "username":None, "password":None}
            if any(map(lambda user_keyword: f"|{user_keyword}|" in command_option, user_searching)):
                if user is not None and len(user) == 3:
                    command_option = command_option.replace("|domain|", user[0])
                    command_option = command_option.replace("|username|", user[1])
                    command_option = command_option.replace("|password|", user[2])
                else:
                    for user_keyword in user_searching:
                        if f"|{user_keyword}|" in command_option:
                            dialog = ChildDialogAskText(self.parent, "Enter "+str(user_keyword), multiline=False)
                            self.parent.wait_window(dialog.app)
                            if dialog.rvalue is None:
                                return
                            command_option = command_option.replace(f"|{user_keyword}|", dialog.rvalue)
            Utils.executeInExternalTerm(command_option)
             
    def ask_confirmation(self, title, question):
        dialog = ChildDialogQuestion(self.parent, title, question)
        self.parent.wait_window(dialog.app)
        return dialog.rvalue == "Yes"
             

class ChildDialogAddUsers:
    def __init__(self, parent, displayMsg="Add AD users"):
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
        self.app.title(displayMsg)
        self.rvalue = None
        self.parent = parent
        
        panel = FormPanel()
        self.formtext = panel.addFormText("Users", r"^\S+\\\S+:\S+$", default="domain\\username:password", side="top")
        button_panel = panel.addFormPanel(side="bottom")
        button_panel.addFormButton("Submit", self.onOk, side="right")
        b = button_panel.addFormButton("Cancel", self.onError, side="right")
        b.configure(style="Close.Titlebar.TButton")
        panel.constructView(appFrame)
        appFrame.pack(ipadx=10, ipady=5)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.grab_set()
            self.app.focus_force()
            self.app.lift()
        except tk.TclError:
            pass

    def onOk(self, event=""):
        """
        Called when the user clicked the validation button. Set the rvalue attributes to the value selected and close the window.
        """
        # send the data to the parent
        self.rvalue = self.formtext.getValue().split("\n")
        self.app.destroy()

    def onError(self, event=None):
        """
        Close the dialog and set rvalue to None
        """
        self.rvalue = None
        self.app.destroy()

class ChildDialogUser:
    def __init__(self, parent, user_data):
        """
        Open a child dialog of a tkinter application to ask a combobox option.

        Args:
            parent: the tkinter parent view to use for this window construction.
            user_data: user from database
        """
        self.app = tk.Toplevel(parent, bg="white")
        self.app.resizable(True, True)
        appFrame = ttk.Frame(self.app)
        self.app.title("View user info")
        self.rvalue = None
        self.parent = parent
        panel = FormPanel()
        panel_info = panel.addFormPanel(grid=True)
        panel_info.addFormLabel("Domain")
        panel_info.addFormStr("Domain", "", user_data.get("domain", ""), status="readonly", row=0, column=1)
        panel_info.addFormLabel("Username", row=1)
        panel_info.addFormStr("Username", "", user_data.get("username", ""), status="readonly", row=1, column=1)
        panel_info.addFormLabel("Password", row=2)
        panel_info.addFormStr("Password", "", user_data.get("password", ""), status="readonly", row=2, column=1)
        panel.addFormLabel("Desc", text=f"{user_data.get('desc', '')}" , side="top")
        panel.addFormTreevw("Groups", ("Group",), [ [x] for x in user_data.get('groups',[])], side="top")
        button_panel = panel.addFormPanel(side="bottom")
        button_panel.addFormButton("Quit", self.onError, side="right")
        panel.constructView(appFrame)
        appFrame.pack(ipadx=10, ipady=5, expand=1)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.grab_set()
            self.app.focus_force()
            self.app.lift()
        except tk.TclError:
            pass

    def onError(self, event=None):
        """
        Close the dialog and set rvalue to None
        """
        self.rvalue = None
        self.app.destroy()

class ChildDialogComputer:
    @staticmethod
    def remove_control_chars(s):
        import itertools
        control_chars = ''.join(map(chr, itertools.chain(range(0x00,0x20), range(0x7f,0xa0))))
        control_char_re = re.compile('[%s]' % re.escape(control_chars))
        return control_char_re.sub('', s)
        
    def __init__(self, parent, computer_data):
        """
        Open a child dialog of a tkinter application to ask a combobox option.

        Args:
            parent: the tkinter parent view to use for this window construction.
            computer_data: computer from database
        """
        self.app = tk.Toplevel(parent, bg="white")
        self.app.resizable(True, True)
        appFrame = ttk.Frame(self.app)
        self.app.title("View user info")
        self.rvalue = None
        self.parent = parent
        panel = FormPanel()
        panel_info = panel.addFormPanel(grid=True)
        panel_info.addFormLabel("IP")
        panel_info.addFormStr("IP", "", computer_data.get("ip", ""), status="readonly", row=0, column=1)
        panel_info.addFormLabel("Name", column=2)
        panel_info.addFormStr("Name", "", computer_data.get("name", ""), status="readonly", column=3)
        panel_info.addFormLabel("OS", row=1)
        panel_info.addFormStr("OS", "", computer_data.get("OS", ""), status="readonly", row=1, column=1)
        panel_info.addFormLabel("Signing", row=2)
        panel_info.addFormStr("Signing", "", computer_data.get("signing", ""), status="readonly", row=2, column=1)
        panel_info.addFormLabel("SMBv1", row=3)
        panel_info.addFormStr("SMBv1", "", computer_data.get("SMBv1", ""), status="readonly", row=3, column=1)
        panel.addFormLabel("Users", side="top")
        panel.addFormTreevw("Users", ("Domain", "Username", "Password"), computer_data.get("users", []), side="top")
        panel.addFormLabel("Admins", side="top")
        panel.addFormTreevw("Admins", ("Domain", "Username", "Password"), computer_data.get("admins", []), side="top")
        if computer_data.get("secrets", []):
            panel.addFormLabel("Secrets", side="top")
            panel.addFormTreevw("Secrets", ("Secret", ""), list(map(lambda s: (s, "") , computer_data.get("secrets", []))), side="top")
        ntds = computer_data.get("ntds", [])
        if ntds:
            panel.addFormLabel("NTDS", side="top")
            panel.addFormText("NTDS", "", "\n".join(ntds), side="top")
        button_panel = panel.addFormPanel(side="bottom")
        button_panel.addFormButton("Quit", self.onError, side="right")
        panel.constructView(appFrame)
        appFrame.pack(ipadx=10, ipady=5, expand=1)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.grab_set()
            self.app.focus_force()
            self.app.lift()
        except tk.TclError:
            pass

    def onError(self, event=None):
        """
        Close the dialog and set rvalue to None
        """
        self.rvalue = None
        self.app.destroy()

class ChildDialogConfigureADModule:
    def __init__(self, parent, displayMsg="Configure AD module"):
        """
        Open a child dialog of a tkinter application to ask a combobox option.

        Args:
            parent: the tkinter parent view to use for this window construction.
            displayMsg: The message that will explain to the user what he is choosing.
            default: Choose a default selected option (one of the string in options). default is None
        """
        self.app = tk.Toplevel(parent, bg="white")
        self.app.resizable(True , True)
        appFrame = ttk.Frame(self.app)
        self.app.title(displayMsg)
        self.rvalue = None
        self.parent = parent
        
        panel = FormPanel()
        ad_settings = ActiveDirectory.getSettings()
        self.explanationLbl = panel.addFormText("Explanation","","""
        Explanations
        You can use those commands with different Types and Variables:
        
        Types:
            - Computer: those commands will be available when right clicking one or many computer and will execute the selected command for each one of them. 
                        It takes into account what user is selected in the user treeview or will ask information otherwise.
            - Share: those commands  will be available when right clicking one File in a share.
            - OnComputerNewUser: Same as computer + will be launched automatically for each new user that can connect to a computer for this computer/user combo.
            - OnComputerFirstUser: Same as computer + will be launched automatically for the first user discovered on each computer
            - OnComputerFirstAdmin: Same as OnComputerFirstUser but only for the first admin user discovered on each computer
            - OnDCFirstUser: Same as OnComputerFirstUser but only if the computer is a Domain Controller.
            - OnDCFirstUser: Same as OnDCFirstUser but only if the user is admin (domain admin).
        Variables:
            - |ip|: will be replaced by the selected computer IP
            - |share|: (Only for Share type commands) Will be replaced with the filename selected in the share table.
            - |username|, |domain|, |password|: will be replaced by the selected user information, or will be prompted if nothing is selected.
            - |wordlist|: will be prompted for a wordlist type of file and replaced by the filepath given
            - |ask_text:$name|: prompt for a text where name is what is asked. store it in a file and replace in command by filepath
            - |users_as_file|: will be replaced with a filename containing all users usernames
            - |computers_as_file|: will be replaced with a filename containing all computers IPs
        """, state="disabled")
        self.formtv = panel.addFormTreevw("Commands", ("Type", "Command name", "Command line"), 
                            ad_settings.get("commands", []), doubleClickBinds=[["Computer", "Share", "OnComputerNewUser", "OnComputerFirstUser", "OnComputerFirstAdmin", "OnDCFirstUser", "OnDCFirstAdmin"], "", ""],
                            side="top", width=800,height=10, fill=tk.BOTH)
        button_panel = panel.addFormPanel(side="bottom")
        button_panel.addFormButton("Submit", self.onOk, side="right")
        button_panel.addFormButton("Cancel", self.onError, side="right")
        panel.constructView(appFrame)
        appFrame.pack(ipadx=10, ipady=5, fill=tk.BOTH, expand=tk.TRUE)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.grab_set()
            self.app.focus_force()
            self.app.lift()
        except tk.TclError:
            pass

    def onOk(self, event=""):
        """
        Called when the user clicked the validation button. Set the rvalue attributes to the value selected and close the window.
        """
        # send the data to the parent
        self.rvalue = self.formtv.getValue()
        self.app.destroy()

    def onError(self, event=None):
        """
        Close the dialog and set rvalue to None
        """
        self.rvalue = None
        self.app.destroy()