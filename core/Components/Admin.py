"""Hold functions to interact with the admin api"""
from core.Components.apiclient import APIClient
from core.Application.Dialogs.ChildDialogEditPassword import ChildDialogEditPassword
import tkinter as tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk
import core.Components.Utils as Utils



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
        self.userTv['columns'] = ('Username', 'Admin')
        self.userTv.heading("#0", text='Username', anchor="nw")
        self.userTv.column("#0", anchor="nw")
        self.userTv.heading("#1", text='Admin', anchor="nw")
        self.userTv.column("#1", anchor="nw")
        self.userTv.pack(side=tk.TOP, padx=10, pady=10, fill=tk.X)
        self.userTv.bind("<Double-Button-1>", self.OnUserDoubleClick)
        self.userTv.bind("<Delete>", self.OnUserDelete)
        
        #### BUTTONS FOR AUTO SCANNING ####
        lblAddUsername = ttk.LabelFrame(parent, text="Add user")
        addUserFrame = ttk.Frame(lblAddUsername)
        lblAddUser = ttk.Label(addUserFrame, text="Username:")
        lblAddUser.grid(column=0, sticky=tk.E)
        self.entryAddUser = ttk.Entry(addUserFrame, width=20)
        self.entryAddUser.grid(row=0, column=1, sticky=tk.W)
        lblAddPwd = ttk.Label(addUserFrame, text="Password:")
        lblAddPwd.grid(row=1, column=0, sticky=tk.E)
        self.password = tk.StringVar() 
        entryAddPwd = ttk.Entry(addUserFrame, width=20, show="*", textvariable=self.password)
        entryAddPwd.grid(row=1, column=1, sticky=tk.W)
        lblAddConfirmPwd = ttk.Label(addUserFrame, text="Confirm:")
        lblAddConfirmPwd.grid(row=2, column=0, sticky=tk.E)
        self.confirmpassword = tk.StringVar() 
        entryAddConfirmPwd = ttk.Entry(addUserFrame, width=20, show="*", textvariable=self.confirmpassword)
        entryAddConfirmPwd.grid(row=2, column=1, sticky=tk.W)
        self.add_user_icon = tk.PhotoImage(file=Utils.getIcon("add_user.png"))
        btn_addUser = ttk.Button(
                addUserFrame, image=self.add_user_icon, command=self.addUser, style='icon.TButton')
        btn_addUser.grid(row=3, column = 2, sticky=tk.W)
        addUserFrame.pack()
        lblAddUsername.pack()
        self.refreshUI()

    def refreshUI(self):
        apiclient = APIClient.getInstance()
        users = apiclient.getUsers()
        for children in self.userTv.get_children():
            self.userTv.delete(children)
        for user in users:
            username = user["username"]
            admin = "Admin" if "admin" in user["scope"] else ""
            try:
                user_node = self.userTv.insert(
                    '', 'end', username, text=username, values=(admin))
            except tk.TclError:
                pass
       
    def addUser(self):
        apiclient = APIClient.getInstance()
        if self.confirmpassword.get() != self.password.get():
            tk.messagebox.showerror("Add user failed", "The password does not match the confirmation")
        apiclient.registerUser(self.entryAddUser.get(), self.password.get())

    def OnUserDoubleClick(self, event):
        tv = event.widget
        item = tv.identify("item", event.x, event.y)
        username = str(item)
        dialog = ChildDialogEditPassword(self.parent, username, askOldPwd=False)
        self.parent.wait_window(dialog.app)
        self.refreshUI()
    
    def OnUserDelete(self, event):
        apiclient = APIClient.getInstance()
        username = self.userTv.selection()[0]
        apiclient.deleteUser(username) 
        self.userTv.remove(username)
