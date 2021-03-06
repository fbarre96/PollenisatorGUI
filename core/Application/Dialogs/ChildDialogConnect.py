"""Defines a sub-swindow window for connecting to the server"""

import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk, Image
import requests
from core.Components.apiclient import APIClient
from core.Components.Utils import loadClientConfig, saveClientConfig, getValidMarkIconPath, getBadMarkIconPath, getWaitingMarkIconPath

class ChildDialogConnect:
    """
    Open a child dialog of a tkinter application to ask server and login infos
    """
    cvalid_icon = None
    cbad_icon = None
    cwaiting_icon = None

    def validIcon(self):
        """Returns a icon indicating a valid state.
        Returns:
            ImageTk PhotoImage"""
        if self.__class__.cvalid_icon is None:
            self.__class__.cvalid_icon = ImageTk.PhotoImage(
                Image.open(getValidMarkIconPath()))
        return self.__class__.cvalid_icon

    def badIcon(self):
        """Returns a icon indicating a bad state.
        Returns:
            ImageTk PhotoImage"""
        if self.__class__.cbad_icon is None:
            self.__class__.cbad_icon = ImageTk.PhotoImage(
                Image.open(getBadMarkIconPath()))
        return self.__class__.cbad_icon

    def waitingIcon(self):
        """Returns a icon indicating a waiting state.
        Returns:
            ImageTk PhotoImage"""
        if self.__class__.cwaiting_icon is None:
            self.__class__.cwaiting_icon = ImageTk.PhotoImage(
                Image.open(getWaitingMarkIconPath()))
        return self.__class__.cwaiting_icon

    def __init__(self, parent, displayMsg="Connect to api:"):
        """
        Open a child dialog of a tkinter application to connect to a pollenisator server.

        Args:
            parent: the tkinter parent view to use for this window construction.
            displayMsg: The message that will explain to the user what the form is.
        """
        self.parent = parent
        self.app = tk.Toplevel(parent, bg="white")
        self.app.resizable(False, False)
        appFrame = ttk.Frame(self.app)
        self.rvalue = None
        self.parent = parent
        self.clientCfg = loadClientConfig()
        lbl = ttk.Label(self.app, text=displayMsg)
        lbl.pack()
        
        lbl_hostname = ttk.Label(appFrame, text="Host : ")
        lbl_hostname.grid(row=0, column=0)
        self.ent_hostname = tk.Entry(
            appFrame, width="20", validate="focusout", validatecommand=self.validateHost)
        self.ent_hostname.insert(tk.END, self.clientCfg["host"])
        self.ent_hostname.bind('<Return>', self.validateHost)
        self.ent_hostname.bind('<KP_Enter>', self.validateHost)
        self.ent_hostname.grid(row=0, column=1)
        lbl_port = ttk.Label(appFrame, text="Port : ")
        lbl_port.grid(row=1, column=0)
        self.ent_port = ttk.Entry(
            appFrame, width="5", validate="focusout", validatecommand=self.validateHost)
        self.ent_port.insert(tk.END, self.clientCfg.get("port", 5000), )
        self.ent_port.bind('<Return>', self.validateHost)
        self.ent_port.bind('<KP_Enter>', self.validateHost)
        self.ent_port.grid(row=1, column=1)
        self.img_indicator = ttk.Label(appFrame, image=self.waitingIcon())
        self.img_indicator.grid(row=1, column=2)
        self.var_https = tk.IntVar()
        lbl_https = ttk.Label(appFrame, text="https: ")
        lbl_https.grid(row=2, column=0)
        self.check_https = ttk.Checkbutton(appFrame, variable=self.var_https, onvalue=True, offvalue=False, command=self.validateHost)
        self.check_https.grid(row=2, column=1)
        self.validateHost()
        lbl_login = ttk.Label(appFrame, text="Login: ")
        lbl_login.grid(row=3, column=0)
        self.ent_login = ttk.Entry(
            appFrame, width="20")
        self.ent_login.grid(row=3, column=1)
        lbl_passwd = ttk.Label(appFrame, text="Password: ")
        lbl_passwd.grid(row=4, column=0)
        self.password = tk.StringVar() 
        self.ent_passwd = ttk.Entry(
            appFrame, width="20", show="*", textvariable = self.password)
        self.ent_passwd.bind('<Return>', self.onOk)
        self.ent_passwd.grid(row=4, column=1)
        appFrame.pack(ipadx=10, ipady=10)
        self.ent_login.focus_set()

        self.ok_button = ttk.Button(self.app, text="OK", command=self.onOk)
        self.ok_button.bind('<Return>', self.onOk)
        self.ok_button.pack(pady=10)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.focus_force()
            self.app.grab_set()
            self.app.lift()

        except tk.TclError:
            pass
        appFrame.tkraise()
        self.ent_login.focus_set()
        appFrame.tkraise()
        
    def getForm(self):
        """Return the content of this form
        Returns:
            a dict with values: host, mongo_port, sftp_port, ssl (string with value True or False),
                                user, password, sftp_user, sftp_password"""
        config = {}
        config["host"] = self.ent_hostname.get()
        config["port"] = self.ent_port.get()
        config["https"] = self.var_https.get()
        return config


    def validateHost(self, _event=None):
        """Validate host on both mongo and sftp connections. Change icons on the dialog accordingly.
        Returns:
            - True if the server is reachable on both mongo and sftp services, False otherwise. Does not test authentication.
        """
        apiclient = APIClient.getInstance()
        apiclient.reinitConnection()
        config = self.getForm()
        self.img_indicator.config(image=self.waitingIcon())
        return  apiclient.tryConnection(config)

    def valideLogin(self):
        pass

    def onOk(self, event=None):
        """
        Called when the user clicked the validation button.
        Try a full connection with authentication to the host given.
        Side effects:
            - Open dialogs if the connection failed. Does not close this dialog.
            - If the connections succeeded : write the client.cfg file accordingly.
        """
        # send the data to the parent
        config = self.getForm()
        apiclient = APIClient.getInstance()
        apiclient.reinitConnection()
        res = apiclient.tryConnection(config)
        self.rvalue = False
        if res:
            #  pylint: disable=len-as-condition
            loginRes = apiclient.login(self.ent_login.get(), self.password.get())
            if loginRes:
                self.rvalue = len(apiclient.getPentestList()) > 0
                for key, value in self.clientCfg.items():
                    if key not in config.keys():
                        config[key] = value
                saveClientConfig(config)
                self.app.destroy()
            else:
                tk.messagebox.showerror("Connection failure", "The login/password you entered does not exists")
        else:
            tk.messagebox.showerror("Connection failure", "The host is not responding. Check if server is alive or if you have a local proxy configured.")
