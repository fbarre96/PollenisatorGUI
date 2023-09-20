"""Hold functions to interact with the admin api"""
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.application.dialogs.ChildDialogEditPassword import ChildDialogEditPassword
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from PIL import Image, ImageTk
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.pollenisatorentry import PopoEntry


class AdminView:
    """View for admin module"""

    def __init__(self, nbk):
        self.nbk = nbk
        self.parent = None
        self.userTv = None

    def initUI(self, parent):
        """Create widgets and initialize them
        Args:
            parent: the parent tkinter widget container."""
        if self.userTv is not None:
            self.refreshUI()
            return
        self.parent = parent
        ### WORKER TREEVIEW : Which worker knows which commands
        self.userTv = ttk.Treeview(self.parent)
        self.headings = ["Username", "Password", "Admin", "Name", "Surname", "Email"]
        self.userTv['columns'] = self.headings
        self.userTv.heading("#0", text='Username', anchor="nw")
        self.userTv.column("#0", anchor="nw")
        self.userTv.heading("#1", text='Password', anchor="nw")
        self.userTv.column("#1", anchor="nw")
        self.userTv.heading("#2", text='Admin', anchor="nw")
        self.userTv.column("#2", anchor="nw")
        self.userTv.heading("#3", text='Name', anchor="nw")
        self.userTv.column("#3", anchor="nw")
        self.userTv.heading("#4", text='Surname', anchor="nw")
        self.userTv.column("#4", anchor="nw")
        self.userTv.heading("#5", text='Email', anchor="nw")
        self.userTv.column("#5", anchor="nw")
        self.userTv.pack(side=tk.TOP, padx=10, pady=10, fill=tk.X)
        self.userTv.bind("<Double-Button-1>", self.OnUserDoubleClick)
        self.userTv.bind("<Delete>", self.OnUserDelete)
        
        #### BUTTONS FOR AUTO SCANNING ####
        lblAddUsername = ttk.LabelFrame(parent, text="Add user", padding=10)
        addUserFrame = CTkFrame(lblAddUsername)
        lblAddUser = CTkLabel(addUserFrame, text="Username")
        lblAddUser.grid(column=0, sticky=tk.E)
        self.entryAddUser = PopoEntry(addUserFrame)
        self.entryAddUser.grid(row=0, column=1, sticky=tk.W)
        lblAddPwd = CTkLabel(addUserFrame, text="Password")
        lblAddPwd.grid(row=1, column=0, sticky=tk.E)
        self.password = tk.StringVar() 
        entryAddPwd = PopoEntry(addUserFrame, show="*", textvariable=self.password)
        entryAddPwd.grid(row=1, column=1, sticky=tk.W)
        lblAddConfirmPwd = CTkLabel(addUserFrame, text="Confirm")
        lblAddConfirmPwd.grid(row=2, column=0, sticky=tk.E)
        self.confirmpassword = tk.StringVar() 
        entryAddConfirmPwd = PopoEntry(addUserFrame, show="*", textvariable=self.confirmpassword)
        entryAddConfirmPwd.grid(row=2, column=1, sticky=tk.W)
        lblName = CTkLabel(addUserFrame, text="Name")
        lblName.grid(row=3, column=0, sticky=tk.E)
        self.name = PopoEntry(addUserFrame)
        self.name.grid(row=3, column=1, sticky=tk.W)
        lblSurname = CTkLabel(addUserFrame, text="Surname")
        lblSurname.grid(row=4, column=0, sticky=tk.E)
        self.surname = PopoEntry(addUserFrame)
        self.surname.grid(row=4, column=1, sticky=tk.W)
        lblEmail = CTkLabel(addUserFrame, text="Email")
        lblEmail.grid(row=5, column=0, sticky=tk.E)
        self.email = PopoEntry(addUserFrame)
        self.email.grid(row=5, column=1, sticky=tk.W)
        self.add_user_icon = CTkImage(Image.open(utils.getIcon("add_user.png")))
        btn_addUser = CTkButton(
                addUserFrame, text="Add user", image=self.add_user_icon, command=self.addUser)
        btn_addUser.grid(row=6, column = 2, sticky=tk.W)
        addUserFrame.pack()
        lblAddUsername.pack()

    def refreshUI(self):
        apiclient = APIClient.getInstance()
        users = apiclient.getUsers()
        for children in self.userTv.get_children():
            self.userTv.delete(children)
        for user in users:
            username = user["username"]
            name = user.get("name", "")
            surname = user.get("surname", "")
            email = user.get("email", "")
            admin = "Admin" if "admin" in user["scope"] else ""
            try:
                user_node = self.userTv.insert(
                    '', 'end', username, text=username, values=("Change pass", admin, name, surname, email))
            except tk.TclError:
                pass
       
    def addUser(self):
        apiclient = APIClient.getInstance()
        if self.confirmpassword.get() != self.password.get():
            tk.messagebox.showerror("Add user failed", "The password does not match the confirmation")
        username = self.entryAddUser.get()
        passw = self.password.get()
        name = self.name.get()
        surname = self.surname.get()
        email = self.email.get()
        apiclient.registerUser(username, passw, name, surname, email)
        self.userTv.insert('', 'end', username, text=username, values=("Change pass", '', name, surname, email,))

    def OnUserDoubleClick(self, event):
        treevw = event.widget
        item = treevw.identify("item", event.x, event.y)
        username = str(item)
        column = treevw.identify_column(event.x)
        columnNb = int(column[1:])
        values = treevw.item(item)["values"]
        if columnNb == 0:
            pass
        elif columnNb == 1:
            self.openEditPassword(username)
        elif columnNb > 1:
            oldVal = values[columnNb-1]
            newVal = tk.simpledialog.askstring(
                "Modify infos", "New value for "+self.headings[columnNb].lower(), initialvalue=oldVal)
            if newVal is None:
                return
            if newVal.strip() == "" or newVal.strip() == oldVal.strip():
                return
            newVals = list(values)
            newVals[columnNb-1] = newVal.strip()
            treevw.item(item, values=newVals)
            values = treevw.item(item)["values"]
            newName = values[self.headings.index("Name") - 1]
            newSurname = values[self.headings.index("Surname") - 1]
            newEMail = values[self.headings.index("Email") - 1]
            apiclient = APIClient.getInstance()
            apiclient.updateUserInfos(username, newName, newSurname, newEMail)

    def openEditPassword(self, username):
        dialog = ChildDialogEditPassword(self.parent, username, askOldPwd=False)
        self.parent.wait_window(dialog.app)
        self.refreshUI()
    
    def OnUserDelete(self, event):
        apiclient = APIClient.getInstance()
        username = self.userTv.selection()[0]
        apiclient.deleteUser(username) 
        self.userTv.delete(username)
