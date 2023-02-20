"""ActiveDirectory module"""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
import os
import re
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.application.dialogs.ChildDialogProgress import ChildDialogProgress
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
from pollenisatorgui.core.application.dialogs.ChildDialogAskFile import ChildDialogAskFile
from pollenisatorgui.core.application.scrollabletreeview import ScrollableTreeview
from pollenisatorgui.core.models.port import Port
from pollenisatorgui.core.forms.formpanel import FormPanel
from pollenisatorgui.modules.module import Module
import tempfile
from bson import ObjectId
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.components.settings import Settings

class ActiveDirectory(Module):
    """
    Shows information about ongoing pentest. 
    """
    iconName = "tab_AD.png"
    tabName = "Active Directory"
    collName = "ActiveDirectory"
    settings = Settings()
    pentest_types = ["lan"]

    def __init__(self, parent, settings):
        """
        Constructor
        """
        super().__init__()
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
        self.users = apiclient.find(ActiveDirectory.collName, {"type": "user"}, True)
        dialog.update(1)
        if self.users is None:
            self.users = []
        self.computers = apiclient.find(ActiveDirectory.collName, {"type": "computer"}, True)
        dialog.update(2)
        if self.computers is None:
            self.computers = []
        self.shares = apiclient.find(ActiveDirectory.collName, {"type": "share"}, True)
        dialog.update(3)
        if self.shares is None:
            self.shares = []
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
            self.insertUser(user)
        dialog.update(2)
        for i,computer in enumerate(self.computers):
            self.insertComputer(computer)
        dialog.update(3)
        for i,share in enumerate(self.shares):
            self.insertShare(share)
        dialog.update(4)
        dialog.destroy()

    def mapLambda(self, c):
        if c[0].lower() in ["computer"]:
            return lambda : self.computerCommand(c[2])
        elif c[0].lower() == "share":
            return lambda : self.shareCommand(c[2])

    def reloadSettings(self):
        s = self.getSettings()
        listOfLambdas = [self.mapLambda(c) for c in s.get("commands", [])]
        i = 0
        for command_options in s.get("commands", []):
            if command_options[0].lower() == "computer":
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
        settings_btn = CTkButton(parent, text="Configure this module", command=self.openConfig)
        settings_btn.pack(side="bottom")
        self.moduleFrame = CTkFrame(parent)
        frameUsers = CTkFrame(self.moduleFrame)
        self.tvUsers = ScrollableTreeview(
            frameUsers, ("Username", "Password", "Domain", "N° groups","Desc"), binds={"<Delete>":self.deleteUser, "<Double-Button-1>":self.userDoubleClick})
        self.tvUsers.pack(fill=tk.BOTH)
        addUserButton = CTkButton(frameUsers, text="Add user manually", command=self.addUsersDialog)
        addUserButton.pack(side="bottom")
        frameComputers = CTkFrame(self.moduleFrame)
        self.tvComputers = ScrollableTreeview(
            frameComputers, ("IP", "Name", "Domain", "DC", "Admin count", "User count", "OS", "Signing", "SMBv1"), binds={"<Double-Button-1>":self.computerDoubleClick})
        self.tvComputers.pack(fill=tk.BOTH)
        frameShares = CTkFrame(self.moduleFrame)
        self.tvShares = ScrollableTreeview(
            frameShares, ("IP", "Share", "Flagged", "Size"))
        self.tvShares.pack(fill=tk.BOTH)
        frameUsers.grid(row=0, column=0)
        frameComputers.grid(row=1, column=0)
        frameShares.grid(row=2, column=0)
        self.moduleFrame.columnconfigure(0, weight=1)
        self.moduleFrame.columnconfigure(1, weight=1)
        self.moduleFrame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def computerDoubleClick(self, event=None):
        selection = self.tvComputers.selection()
        if selection:
            self.openComputerDialog(selection[0])

    def openComputerDialog(self, computer_iid):
        apiclient = APIClient.getInstance()
        computer_d = apiclient.find(ActiveDirectory.collName,
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
            groups = user.get("groups", [])
            if groups is None:
                groups = []
            self.tvUsers.insert(
                '', 'end', user["_id"], text=username, values=(password, domain, str(len(groups)), user.get("description", "")))
        except tk.TclError as e:
            pass

    def userDoubleClick(self, event=None):
        selection = self.tvUsers.selection()
        if selection:
            self.openUserDialog(selection[0])

    def openUserDialog(self, user_iid):
        apiclient = APIClient.getInstance()
        user_d = apiclient.find(ActiveDirectory.collName,
            {"_id":ObjectId(user_iid)}, False)
        if user_d is None:
            return
        dialog = ChildDialogUser(self.parent, user_d)
        self.parent.wait_window(dialog.app)


    def deleteUser(self, event=None):
        apiclient = APIClient.getInstance() 
        selection = self.tvUsers.selection()
        users_iid = [str(x["_id"]) for x in self.users]
        for select in selection:
            try:
                item = self.tvUsers.item(select)
            except tk.TclError:
                pass
            apiclient.delete( ActiveDirectory.collName+"/users", select)
            try:
                index = users_iid.index(str(select))
                del users_iid[index]
                del self.users[index]
            except ValueError:
                pass

            self.tvUsers.delete(select)
    
    def insertComputer(self, computer):
        infos = computer.get("infos",{})
        newValues = (computer.get("name",""), computer.get("domain", ""), infos.get("is_dc", False), len(computer.get("admins", [])), len(computer.get("users", [])), infos.get("os", ""), \
                        infos.get("signing", ""), infos.get("smbv1", ""))
        try:
            self.tvComputers.insert(
                '', 'end', computer["_id"], text=computer.get("ip", ""),
                values=newValues)
        except tk.TclError:
            self.tvComputers.item(computer["_id"], values=newValues) 

    def insertShare(self, share):
        try:
            parentiid = self.tvShares.insert(
                        '', 'end', share["_id"], text=share.get("ip", ""), values=(share.get("share", ""),))
        except tk.TclError:
            parentiid = str(share["_id"])
        for file_infos in share.get("files",[]):
            toAdd = (file_infos["path"], str(file_infos["flagged"]), str(file_infos["size"]))
            try:
                self.tvShares.insert(
                    parentiid, 'end', None, text="", values=tuple(toAdd))
            except tk.TclError:
                pass

    def addUserInDb(self, domain, username, password):
        apiclient = APIClient.getInstance()
        user = {"type": "user", "username": username, "domain": domain, "password": password}
        res = apiclient.insert( ActiveDirectory.collName+"/users", {"username": username, "domain": domain, "password": password})
        
     
    def update(self, dataManager, notif, obj, old_obj):
        if notif["collection"] != ActiveDirectory.collName:
            return
        apiclient = APIClient.getInstance()
        res = apiclient.find(ActiveDirectory.collName, {"_id": ObjectId(notif["iid"])}, False)
        iid = notif["iid"]
        if notif["action"] == "insert":
            if res is None:
                return
            if res["type"] == "computer":
                self.insertComputer(res)
            elif res["type"] == "user":
                self.insertUser(res)
            elif res["type"] == "share":
                self.insertShare(res)
        elif notif["action"] == "update":
            if res is None:
                return
            if res["type"] == "computer":
                self.insertComputer(res)
            if res["type"] == "share":
                self.insertShare(res)
        elif notif["action"] == "delete":
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
                    self.addUserInDb(domain, username, password)
    
    def exportAllUsersAsFile(self, domain="", delim="\n"):
        fp = tempfile.mkdtemp()
        filepath = os.path.join(fp, "users.txt")
        with open(filepath, mode="w") as f:
            apiclient = APIClient.getInstance()
            search = {"type":"user"}
            if domain != "":
                search["domain"] = domain 
            res = apiclient.find(ActiveDirectory.collName, search)
            for selected_user in res:
                username = selected_user["username"]
                f.write(username+delim)
        return filepath

    def exportAllComputersAsFile(self, delim="\n"):
        fp = tempfile.mkdtemp()
        filepath = os.path.join(fp, "computers.txt")
        with open(filepath, mode="w") as f:
            apiclient = APIClient.getInstance()
            res = apiclient.find(ActiveDirectory.collName, {"type":"computers"})
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
        apiclient = APIClient.getInstance()
        share_m = apiclient.find(ActiveDirectory.collName, {"_id": ObjectId(parent_iid)}, False)
        path = item_values[0]
        files = share_m.get("files", [])
        try:
            path_index = [x["path"] for x in files].index(path)
        except:
            tk.messagebox.showerror("path not found","Path "+str(path)+" was not found in share")
            return
        
        file_infos = files[path_index]
        users = file_infos.get("users", [])
        if not users:
            tk.messagebox.showerror("No users known","This share has no no known user ")
            return
        u = users[0] # take first one
        domain = u[0] if u[0] is not None else ""
        user = u[1] if u[1] is not None else ""
        share_name = item_values[0]
        apiclient = APIClient.getInstance()
        apiclient.getCurrentPentest()
        user_o = apiclient.find(ActiveDirectory.collName, 
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
        utils.executeInExternalTerm(command_option)

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
                    with open(filepath, mode="w") as f:
                        f.write(dialog.rvalue)
                    command_option = command_option.replace(s.group(0), filepath)
            command_option = command_option.replace("|domain|", user[0])
            command_option = command_option.replace("|username|", user[1])
            command_option = command_option.replace("|password|", user[2])
        utils.executeInExternalTerm(command_option)

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
                        if user is not None and len(user) == 3:
                            domain = user[0]
                        else:
                            domain = ""
                        filepath = self.exportAllUsersAsFile(domain)
                        command_option = command_option.replace(s.group(0), filepath)
                    elif "|ask_text:" in s.group(0):
                        what = s.group(1)
                        dialog = ChildDialogAskText(self.tkApp, what)
                        self.tkApp.wait_window(dialog.app)
                        fp = tempfile.mkdtemp()
                        filepath = os.path.join(fp, what+".txt")
                        with open(filepath, mode="w") as f:
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
            utils.executeInExternalTerm(command_option)
             
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
        self.app = CTkToplevel(parent, fg_color="white")
        self.app.resizable(False, False)
        appFrame = CTkFrame(self.app)
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
        """he rvalue attributes to the value selected and close the window.
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
        self.app = CTkToplevel(parent, fg_color="white")
        self.app.resizable(True, True)
        appFrame = CTkFrame(self.app)
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
        panel.addFormLabel("Desc", text=f"Desc : {user_data.get('desc', '')}" , side="top")
        groups = user_data.get('groups', []) 
        if groups is None:
            groups = []
        panel.addFormTreevw("Groups", ("Group",), [ [x] for x in groups], side="top")
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
        self.app = CTkToplevel(parent, fg_color="white")
        self.app.resizable(True, True)
        appFrame = CTkFrame(self.app)
        self.app.title("View user info")
        self.rvalue = None
        self.parent = parent
        panel = FormPanel()
        panel_info = panel.addFormPanel(grid=True)
        panel_info.addFormLabel("IP")
        panel_info.addFormStr("IP", "", computer_data.get("ip", ""), status="readonly", row=0, column=1)
        panel_info.addFormLabel("Name", column=2)
        panel_info.addFormStr("Name", "", computer_data.get("name", ""), status="readonly", column=3)
        row = 1
        for info_name, val in computer_data.get("infos", {}).items():
            panel_info.addFormLabel(info_name, row=row)
            panel_info.addFormStr(info_name, "", val, status="readonly", row=row, column=1)
            row += 1
        apiclient = APIClient.getInstance()
        res = apiclient.getComputerUsers(str(computer_data["_id"]))
        if res is  None:
            res = {}
        users_data = [(d["domain"], d["username"], d["password"]) for d in res.get("users", [])]
        admins_data = [(d["domain"], d["username"], d["password"]) for d in res.get("admins",[])]
        panel.addFormLabel("Users", side="top")
        panel.addFormTreevw("Users", ("Domain", "Username", "Password"), users_data, side="top")
        
        panel.addFormLabel("Admins", side="top")
        panel.addFormTreevw("Admins", ("Domain", "Username", "Password"), admins_data, side="top")
        if computer_data.get("secrets", []):
            panel.addFormLabel("Secrets", side="top")
            panel.addFormTreevw("Secrets", ("Secret", ""), [(s, "") for s in computer_data.get("infos", {}).get("secrets", [])], side="top")
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
        self.app = CTkToplevel(parent, fg_color="white")
        self.app.resizable(True , True)
        appFrame = CTkFrame(self.app)
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
                            ad_settings.get("commands", []), doubleClickBinds=[["Computer", "Share"], "", ""],
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
        """he rvalue attributes to the value selected and close the window.
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