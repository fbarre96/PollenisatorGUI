"""ActiveDirectory module"""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
import os
import re

from pollenisatorgui.modules.ActiveDirectory.controllers.sharecontroller import ShareController

from pollenisatorgui.modules.ActiveDirectory.controllers.computercontroller import ComputerController
from pollenisatorgui.modules.ActiveDirectory.views.shareview import ShareView
from pollenisatorgui.core.application.scrollableframexplateform import ScrollableFrameXPlateform
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.application.dialogs.ChildDialogProgress import ChildDialogProgress
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
from pollenisatorgui.core.application.dialogs.ChildDialogAskFile import ChildDialogAskFile
from pollenisatorgui.core.application.scrollabletreeview import ScrollableTreeview
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.components.tag import TagInfos
from pollenisatorgui.core.models.port import Port
from pollenisatorgui.core.forms.formpanel import FormPanel
from pollenisatorgui.modules.ActiveDirectory.controllers.computercontroller import ComputerController
from pollenisatorgui.modules.ActiveDirectory.controllers.usercontroller import UserController
from pollenisatorgui.modules.ActiveDirectory.views.computerview import ComputerView
from pollenisatorgui.modules.ActiveDirectory.views.userview import UserView
from pollenisatorgui.modules.module import Module
from pollenisatorgui.modules.ActiveDirectory.models.users import User # load it in registry
from pollenisatorgui.modules.ActiveDirectory.models.computers import Computer # load it in registry
from pollenisatorgui.modules.ActiveDirectory.models.shares import Share # load it in registry
import tempfile
from bson import ObjectId
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.components.settings import Settings
from PIL import Image
from pollenisatorgui.core.application.pollenisatorentry import PopoEntry


class ActiveDirectory(Module):
    """
    Shows information about ongoing pentest. 
    """
    iconName = "tab_AD.png"
    tabName = "Active Directory"
    coll_name = "ActiveDirectory"
    classes = ["users", "computers", "shares"]
    order_priority = Module.HIGH_PRIORITY
    settings = Settings()
    pentest_types = ["lan"]

    def __init__(self, parent, settings, tkApp):
        """
        Constructor
        """
        super().__init__()
        self.parent = None
        self.users = {}
        self.treevw = None
        self.tkApp = tkApp
        self.computers = {}
        self.shares = {}
        self.inited = False
        
    

    @classmethod
    def getSettings(cls):
        return cls.settings.local_settings.get(ActiveDirectory.coll_name, {})

    @classmethod
    def saveSettings(cls, newSettings):
        cls.settings.local_settings[ActiveDirectory.coll_name] = newSettings
        cls.settings.saveLocalSettings()

    def open(self, view, nbk, treevw):
        apiclient = APIClient.getInstance()
        self.treevw = treevw
        if self.inited is False:
            self.initUI(view)
        if apiclient.getCurrentPentest() is not None:
            self.refreshUI()
        return True
    
    def onTreeviewLoad(self, checklistview, lazyload):
        """
        Called when the treeview is loaded
        """
        datamanager = DataManager.getInstance()
        if not checklistview and not lazyload:
            computers = list(datamanager.get("computers", '*'))
            for computer in computers:
                computer_o = ComputerController(computer)
                computer_vw = ComputerView(self.tkApp.treevw, self.tkApp.viewframe, self.tkApp, computer_o)
                computer_vw.addInTreeview(None, addChildren=False)
            shares = list(datamanager.get("shares", '*'))
            for share in shares:
                share_o = ShareController(share)
                share_vw = ShareView(self.tkApp.treevw, self.tkApp.viewframe, self.tkApp, share_o)
                share_vw.addInTreeview(None, addChildren=False)
        if not checklistview:
            users = list(datamanager.get("users", '*'))
            for user in users:
                user_o = UserController(user)
                user_vw = UserView(self.tkApp.treevw, self.tkApp.viewframe, self.tkApp, user_o)
                user_vw.addInTreeview(None, addChildren=False)
            

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
        self.users = apiclient.find("users", {"type": "user"}, True)
        dialog.update(1)
        if self.users is None:
            self.users = []
        self.computers = apiclient.find("computers", {"type": "computer"}, True)
        dialog.update(2)
        if self.computers is None:
            self.computers = []
        self.shares = apiclient.find("shares", {"type": "share"}, True)
        dialog.update(3)
        if self.shares is None:
            self.shares = []
        dialog.update(4)
        self.tags = {}
        find_tags = apiclient.find("tags", {"item_type": {"$in":["computers","users","shares"]}}, True)
        for tag in find_tags:
            self.tags[str(tag.get("item_id"))] = tag
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
            self.insertUser(user,  auto_update_pagination=False)
        self.tvUsers.setPaginationPanel()
        dialog.update(2)
        for i,computer in enumerate(self.computers):
            self.insertComputer(computer, auto_update_pagination=False)
        self.tvComputers.setPaginationPanel()
        
        dialog.update(3)
        for i,share in enumerate(self.shares):
            self.insertShare(share, auto_update_pagination=False)
        self.tvShares.setPaginationPanel()
        dialog.update(4)
        dialog.destroy()

    def statusbarClicked(self, tagname):
        self.searchBar.delete(0, tk.END)
        self.searchBar.insert(tk.END, tagname)
        self.search()

    def modelToView(self, data_type, model):
        if data_type.lower() == "users":
            return UserView(self.tkApp.treevw, self.tkApp.viewframe, self.tkApp, UserController(model))
        elif data_type.lower() == "computers":
            return ComputerView(self.tkApp.treevw, self.tkApp.viewframe, self.tkApp, ComputerController(model))
        elif data_type.lower() == "shares":
            return ShareView(self.tkApp.treevw, self.tkApp.viewframe, self.tkApp, ShareController(model))
        return None

    def mapLambda(self, c, treeview=None, model=None):
        if c[0].lower() in ["computer"]:
            return lambda : self.computerCommand(c[2], treeview=treeview, model=model)
        elif c[0].lower() == "share":
            return lambda : self.shareCommand(c[2], treeview=treeview, model=model)

    def reloadSettings(self):
        s = self.getSettings()
        listOfLambdas = [self.mapLambda(c) for c in s.get("commands", [])]
        i = 0
        for command_options in s.get("commands", []):
            if command_options[0].lower() == "computer":
                self.tvComputers.addContextMenuCommand(command_options[1], listOfLambdas[i], replace=True)
            elif command_options[0].lower() == "share":
                self.tvShares.addContextMenuCommand(command_options[1], listOfLambdas[i], replace=True)
            i+=1
        
    def getAdditionalContextualCommands(self, type, treeview, view):
        s = self.getSettings()
        listOfLambdas = [self.mapLambda(c, treeview, view.controller.model) for c in s.get("commands", [])]
        i = 0
        ret = {}
        for command_options in s.get("commands", []):
            if command_options[0].lower() == type.lower():
                ret[command_options[1]] = listOfLambdas[i]
            i+=1
        return ret

    def initUI(self, parent):
        """
        Initialize Dashboard widgets
        Args:
            parent: its parent widget
        """
        self.inited = True
        self.parent = parent
        settings_btn = CTkButton(parent, text="Configure this module", command=self.openConfig)
        settings_btn.pack(side="bottom", pady=5)
        self.moduleFrame = ScrollableFrameXPlateform(parent)
        frameSearchBar = CTkFrame(self.moduleFrame)
        self.searchBar = PopoEntry(frameSearchBar, placeholder_text="Search")
        self.searchBar.pack(side="left", fill=tk.X, expand=True)
        self.searchBar.bind("<KeyRelease>", self.search)
        frameSearchBar.pack(side="top", fill=tk.X, expand=True)
        self.frameTreeviews = CTkFrame(self.moduleFrame)
        frameUsers = CTkFrame(self.frameTreeviews)
        self.tvUsers = ScrollableTreeview(
            frameUsers, ("Username", "Password", "Domain", "N° groups","Desc", "hashNT", "Tags"), binds={"<Delete>":self.deleteUser, "<Double-Button-1>":self.userDoubleClick})
        self.tvUsers.pack(fill=tk.BOTH)
        addUserButton = CTkButton(frameUsers, text="Add user manually", command=self.addUsersDialog)
        addUserButton.pack(side="bottom")
        frameComputers = CTkFrame(self.frameTreeviews)
        self.tvComputers = ScrollableTreeview(
            frameComputers, ("IP", "Name", "Domain", "DC", "Admin count", "User count", "OS", "Signing", "SMBv1", "Tags"), width=parent.winfo_width()-100, binds={"<Double-Button-1>":self.computerDoubleClick})
        self.tvComputers.pack(fill=tk.BOTH)
        frameShares = CTkFrame(self.frameTreeviews)
        self.tvShares = ScrollableTreeview(
            frameShares, ("IP", "Share", "Flagged", "Size", "Tags"), paginate=False)
        self.tvShares.pack(fill=tk.BOTH)
        frameUsers.grid(row=0, column=0)
        frameComputers.grid(row=1, column=0)
        frameShares.grid(row=2, column=0)
        self.frameTreeviews.columnconfigure(0, weight=1)
        self.frameTreeviews.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.moduleFrame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def search(self, event=None):
        """
        Search in treeviews
        """
        if event is not None:
            if event.keysym != "BackSpace" and event.keysym != "Delete" and (len(event.keysym) > 1 or not event.keysym.isalnum()):
                return
        search = self.searchBar.get()
        self.tvUsers.filter(search, search, search, search, search, search, search, check_all=False, check_case=False)
        self.tvComputers.filter(search, search, search, search, search, search, search, search, search, search, check_all=False, check_case=False)
        self.tvShares.filter(search, search, search, search, search, check_all=False, check_case=False)

    def computerDoubleClick(self, event=None):
        selection = self.tvComputers.selection()
        if selection:
            self.openComputerDialog(selection[0])

    def openComputerDialog(self, computer_iid):
        self.getComputerDialog(computer_iid)

    def getComputerDialog(self, computer_iid):
        apiclient = APIClient.getInstance()
        computer_d = apiclient.find("computers",
            {"_id":ObjectId(computer_iid)}, False)
        if computer_d is None:
            return
        cw = ComputerView(self.treevw, None, self.tkApp, ComputerController(Computer(computer_d)))
        cw.openInDialog(False)

    def insertUser(self, user, auto_update_pagination=True):
        try:
            domain = user.get("domain", "")
            username = user.get("username", "")
            password = user.get("password", "")
            groups = user.get("groups", [])
            datamanager = DataManager.getInstance()
            if groups is None:
                groups = []
            user_tags = self.tags.get(str(user["_id"]), {})
            tags_info = user_tags.get("tags", [])
            tags_names = [tag.get("name", "") for tag in tags_info if tag.get("name", "") != ""]
            self.tvUsers.insert('', 'end', user["_id"], text=username, 
                                values=(password, domain, str(len(groups)), user.get("description", ""), user.get("infos", {}).get("hashNT", ""),", ".join(tags_names)), auto_update_pagination=auto_update_pagination)
        except tk.TclError as e:
            pass

    def userDoubleClick(self, event=None):
        selection = self.tvUsers.selection()
        if selection:
            self.openUserDialog(selection[0])

    def openUserDialog(self, user_iid):
        self.getUserDialog(user_iid)

    def getUserDialog(self, user_iid):
        apiclient = APIClient.getInstance()
        user_d = apiclient.find("users",
            {"_id":ObjectId(user_iid)}, False)
        if user_d is None:
            return
        user_vw = UserView(self.treevw, None, self.tkApp, UserController(User(user_d)))
        user_vw.openInDialog(False)

    def deleteUser(self, event=None):
        apiclient = APIClient.getInstance() 
        selection = self.tvUsers.selection()
        users_iid = [str(x["_id"]) for x in self.users]
        for select in selection:
            try:
                item = self.tvUsers.item(select)
            except tk.TclError:
                pass
            apiclient.delete( ActiveDirectory.coll_name+"/users", select)
            try:
                index = users_iid.index(str(select))
                del users_iid[index]
                del self.users[index]
            except ValueError:
                pass

            self.tvUsers.delete(select)
    
    def insertComputer(self, computer, auto_update_pagination=True):
        infos = computer.get("infos",{})
        computer_tags = self.tags.get(str(computer["_id"]), {})
        tags_info = computer_tags.get("tags", [])
        tags_names = [tag.get("name", "") for tag in tags_info if tag.get("name", "") != ""]
        newValues = (computer.get("name",""), computer.get("domain", ""), infos.get("is_dc", False), len(computer.get("admins", [])), len(computer.get("users", [])), infos.get("os", ""), \
                        infos.get("signing", ""), infos.get("smbv1", ""), ", ".join(tags_names))
        
        try:
            self.tvComputers.insert(
                '', 'end', computer["_id"], text=computer.get("ip", ""),
                values=newValues, auto_update_pagination=auto_update_pagination)
        except tk.TclError:
            self.tvComputers.item(computer["_id"], values=newValues) 

    def insertShare(self, share, auto_update_pagination=True):
        share_tags = self.tags.get(str(share["_id"]), {})
        tags_info = share_tags.get("tags", [])
        tags_names = [tag.get("name", "") for tag in tags_info if tag.get("name", "") != ""]
        try:
            parentiid = self.tvShares.insert(
                        '', 'end', share["_id"], text=share.get("ip", ""), values=(share.get("share", ""), ", ".join(tags_names),"",""), auto_update_pagination=auto_update_pagination)
        except tk.TclError:
            parentiid = str(share["_id"])
        for file_infos in share.get("files",[]):
            if not file_infos["flagged"]:
                continue
            toAdd = (file_infos["path"], str(file_infos["flagged"]), str(file_infos["size"]), "")
            try:
                self.tvShares.insert(
                    parentiid, 'end', None, text="", values=tuple(toAdd), auto_update_pagination=auto_update_pagination)
            except tk.TclError:
                pass

    def addUserInDb(self, domain, username, password):
        apiclient = APIClient.getInstance()
        user = {"type": "user", "username": username, "domain": domain, "password": password}
        res = apiclient.insert( ActiveDirectory.coll_name+"/users", {"username": username, "domain": domain, "password": password})
        
     
    def update_received(self, dataManager, notif, obj, old_obj):
        if not self.inited:
            return
        if notif["collection"] not in ActiveDirectory.classes:
            return
        apiclient = APIClient.getInstance()
        res = apiclient.find(notif["collection"], {"_id": ObjectId(notif["iid"])}, False)
        iid = notif["iid"]
        if notif["action"] == "insert":
            if res is None:
                return
            if notif["collection"] == "computers":
                self.insertComputer(res)
            elif notif["collection"] == "users":
                self.insertUser(res)
            elif notif["collection"] == "shares":
                self.insertShare(res)
        elif notif["action"] == "update":
            if res is None:
                return
            if notif["collection"] == "computers":
                self.insertComputer(res)
            if notif["collection"] == "shares":
                self.insertShare(res)
        elif notif["action"] == "delete":
            if res is None:
                return
            try:
                if notif["collection"] == "computers":
                    self.tvComputers.delete(str(iid))
                elif notif["collection"] == "users":
                    self.tvUsers.delete(str(iid))
                elif notif["collection"] == "shares":
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
            res = apiclient.find("users", search)
            for selected_user in res:
                username = selected_user["username"]
                f.write(username+delim)
        return filepath

    def exportAllComputersAsFile(self, delim="\n"):
        fp = tempfile.mkdtemp()
        filepath = os.path.join(fp, "computers.txt")
        with open(filepath, mode="w") as f:
            apiclient = APIClient.getInstance()
            res = apiclient.find("computers", {"type":"computers"})
            for selected_computer in self.tvComputers.get_children():
                computer = self.tvComputers.item(selected_computer)["text"]
                f.write(computer+delim)
        return filepath


    def shareCommand(self, command_option, treeview=None, model=None):
        if treeview is None:
            treeview = self.tvShares
        selected = treeview.selection()[0]
        if model is None:
            parent_iid = treeview.parent(selected)
            if not parent_iid: # file in share
                return
            ip = treeview.item(parent_iid)["text"]
            apiclient = APIClient.getInstance()
            share_m = apiclient.find("shares", {"_id": ObjectId(parent_iid)}, False)
            path = item_values[0]
            share_name = item_values[0]
        else:
            ip = model.ip
            share_m = model.getData()
            path = treeview.item(selected)["text"]
            share_name = model.share
            

        item_values = treeview.item(selected)["values"]
        if share_m is None:
            return
        
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
        
        apiclient = APIClient.getInstance()
        apiclient.getCurrentPentest()
        user_o = apiclient.find("users", 
                {"type":"user", "domain":domain, "username":user}, False)
        if user_o is None:
            tk.messagebox.showerror("user not found","User "+str(domain)+"\\"+str(user)+" was not found")
            return
        user = "" if user is None else user
        domain = "" if domain is None else domain
        command_option = command_option.replace("|username|", user)
        command_option = command_option.replace("|domain|", domain)
        command_option = command_option.replace("|password|", user_o["password"])
        command_option = command_option.replace("|share|",share_m["share"])
        command_option = command_option.replace("|filepath|",path.replace("\\\\", "\\"))
        just_path = path.replace("\\\\", "\\").replace(share_m["share"], "",1).replace("/", "\\")
        while just_path.startswith("\\"):
            just_path = just_path[1:]
        command_option = command_option.replace("|file|",path.replace("\\\\", "\\").replace(share_m["share"], "",1))
        command_option = command_option.replace("|filename|",os.path.basename(path.replace("\\\\", "\\").replace(share_m["share"], "",1)))

        command_option = command_option.replace("|ip|",ip)
        self.tkApp.launch_in_terminal(None, "Share command", command_option, use_pollex=False)

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
        self.tkApp.launch_in_terminal(None, "user command", command_option)

    def computerCommand(self, command_option, ips=None, user=None, treeview=None, model=None):
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
            self.tkApp.launch_in_terminal(None, "computer command", command_option)
             
    def ask_confirmation(self, title, question):
        dialog = ChildDialogQuestion(self.parent, title, question)
        self.parent.wait_window(dialog.app)
        return dialog.rvalue == "Yes"
             
    def _insertChildren(self, coll_name, parent_data):
        """Insert every children defect in database as DefectView under this node"""
        if coll_name == "ips":
            apiclient = APIClient.getInstance()
            computers = apiclient.find("computers", {"ip": parent_data.get("ip")})
            for computer in computers:
                computer_o = ComputerController(Computer(computer))
                computer_vw = ComputerView(
                    self.tkApp.treevw, self.tkApp.viewframe, self.tkApp, computer_o)
                computer_vw.addInTreeview(str(parent_data.get("_id")), addChildren=False)
            shares = apiclient.find("shares", {"ip": parent_data.get("ip")})
            for share in shares:
                share_o = ShareController(Share(share))
                share_vw = ShareView(
                    self.tkApp.treevw, self.tkApp.viewframe, self.tkApp, share_o)
                share_vw.addInTreeview(str(parent_data.get("_id")), addChildren=False)
            return computers

class ChildDialogAddUsers:
    def __init__(self, parent, displayMsg="Add AD users"):
        """
        Open a child dialog of a tkinter application to ask a combobox option.

        Args:
            parent: the tkinter parent view to use for this window construction.
            displayMsg: The message that will explain to the user what he is choosing.
            default: Choose a default selected option (one of the string in options). default is None
        """
        self.app = CTkToplevel(parent, fg_color=utils.getBackgroundColor())
        self.app.attributes("-type", "dialog")
        self.app.resizable(False, False)
        appFrame = CTkFrame(self.app)
        self.app.title(displayMsg)
        self.rvalue = None
        self.parent = parent
        
        panel = FormPanel()
        self.formtext = panel.addFormText("Users", r"^\S+\\\S+:\S+$", default="domain\\username:password", side="top")
        button_panel = panel.addFormPanel(side="bottom")
        self.save_image = CTkImage(Image.open(utils.getIcon("save.png")))
        button_panel.addFormButton("Submit", self.onOk, side="right", image=self.save_image)
        b = button_panel.addFormButton("Cancel", self.onError, side="right", 
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
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

class ChildDialogShare:
    def __init__(self, parent, share_data):
        self.app = CTkToplevel(parent, fg_color=utils.getBackgroundColor())
        self.app.attributes("-type", "dialog")
        self.app.resizable(True, True)
        appFrame = CTkFrame(self.app)
        self.app.title("View share info")
        self.rvalue = None
        self.parent = parent
        panel = FormPanel()
        panel_info = panel.addFormPanel(grid=True)
        panel_info.addFormLabel("IP")
        panel_info.addFormStr("IP", "", share_data.get("ip", ""), status="readonly", row=0, column=1)
        panel_info.addFormLabel("Share", row=1)
        panel_info.addFormStr("Share", "", share_data.get("share", ""), status="readonly", row=1, column=1)
        files = share_data.get('files', []) 
        if files is None:
            files = []
        defaults = []
        for file in files:
            defaults.append([file["path"],file["flagged"], file["size"]])
        panel.addFormTreevw("Files", ("Path","Flagged","Size"), default_values=defaults, side="top")
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
        self.app = CTkToplevel(parent, fg_color=utils.getBackgroundColor())
        self.app.attributes("-type", "dialog")
        self.app.resizable(True , True)
        appFrame = CTkFrame(self.app)
        self.app.title(displayMsg)
        self.rvalue = None
        self.parent = parent
        self.save_image = CTkImage(Image.open(utils.getIcon("save.png")))
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
            - |share|: (Only for Share type commands) Will be replaced with the share name (drive name like ADMIN$) selected in the share table.
            - |filepath|: (Only for Share type commands) Will be replaced with the full filepath selected in the share table (like ADMIN$\\folder\path.txt).
            - |file|: (Only for Share type commands) Will be replaced with the filepath WITHOUT THE SHARE NAME selected in the share table (like folder\path.txt).
            - |filename|: (Only for Share type commands) Will be replaced with only the filename selected in the share table (like path.txt).
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
        button_panel.addFormButton("Submit", self.onOk, side="right",  image=self.save_image)
        button_panel.addFormButton("Cancel", self.onError, side="right", 
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
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