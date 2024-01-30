"""Defines a sub-swindow window for connecting to the server"""

import tkinter as tk
import tkinter.ttk as ttk
import re
from customtkinter import *
from pollenisatorgui.core.application.pollenisatorentry import PopoEntry
from PIL import ImageTk, Image
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.utils import loadClientConfig, saveClientConfig, getValidMarkIconPath, getBadMarkIconPath, getWaitingMarkIconPath
from pollenisatorgui.core.application.CollapsibleFrame import CollapsibleFrame

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
            self.__class__.cvalid_icon = CTkImage(
                Image.open(getValidMarkIconPath()))
        return self.__class__.cvalid_icon

    def badIcon(self):
        """Returns a icon indicating a bad state.
        Returns:
            ImageTk PhotoImage"""
        if self.__class__.cbad_icon is None:
            self.__class__.cbad_icon = CTkImage(
                Image.open(getBadMarkIconPath()))
        return self.__class__.cbad_icon

    def waitingIcon(self):
        """Returns a icon indicating a waiting state.
        Returns:
            ImageTk PhotoImage"""
        if self.__class__.cwaiting_icon is None:
            self.__class__.cwaiting_icon = CTkImage(
                Image.open(getWaitingMarkIconPath()))
        return self.__class__.cwaiting_icon

    def __init__(self, parent, displayMsg="Connect to api"):
        """
        Open a child dialog of a tkinter application to connect to a pollenisator server.

        Args:
            parent: the tkinter parent view to use for this window construction.
            displayMsg: The message that will explain to the user what the form is.
        """
        self.parent = parent
        self.app = CTkToplevel(parent)
        self.app.attributes("-type", "dialog")
        self.app.title("Connect to server")
        self.app.resizable(False, False)
        appFrame = CTkFrame(self.app)
        self.app.bind("<Escape>", self.onError)
        self.rvalue = None
        self.parent = parent
        self.clientCfg = loadClientConfig()
        lbl = CTkLabel(self.app, text=displayMsg)
        lbl.pack()
        settings = Settings()
        settings.reloadLocalSettings()
        prev_hosts = settings.local_settings.get("hosts", [])
        row = 0
        if len(prev_hosts) > 0:
            CTkLabel(appFrame, text="Previous connections").grid(row=0, column=0, sticky="e")
            box_uri = CTkComboBox(appFrame, values=[x["url"] for x in prev_hosts], state="readonly", width=300, command=self.fill_with_uri)
            box_uri.grid(sticky="w", padx=5, row=0, column=1)
            box_uri.set(prev_hosts[0]["url"])
            row += 1
        lbl_hostname = CTkLabel(appFrame, text="Host : ")
        lbl_hostname.grid(row=row, column=0, sticky="e")
        self.ent_hostname = PopoEntry(
            appFrame, placeholder_text="127.0.0.1", validate="focusout", width=300, validatecommand=self.validateHost)
        self.ent_hostname.insert(tk.END, self.clientCfg["host"])
        self.ent_hostname.bind('<Return>', self.validateHost)
        self.ent_hostname.bind('<KP_Enter>', self.validateHost)
        self.ent_hostname.grid(row=row, column=1, sticky="w", padx=5)
        row += 1
        lbl_port = CTkLabel(appFrame, text="Port : ")
        lbl_port.grid(row=row, column=0, sticky="e")
        self.ent_port = PopoEntry(
            appFrame, placeholder_text="5000", validate="focusout", validatecommand=self.validateHost)
        self.ent_port.insert(tk.END, self.clientCfg.get("port", 5000), )
        self.ent_port.bind('<Return>', self.validateHost)
        self.ent_port.bind('<KP_Enter>', self.validateHost)
        self.ent_port.grid(row=row, column=1, sticky="w", padx=5)
        self.img_indicator = CTkLabel(appFrame, text="",image=self.waitingIcon())
        self.img_indicator.grid(row=row, column=2)
        row += 1

        self.var_https = tk.IntVar()
        lbl_https = CTkLabel(appFrame, text="https: ")
        lbl_https.grid(row=row, column=0, sticky="e")
        self.check_https = CTkSwitch(appFrame, variable=self.var_https, text="", onvalue=True, offvalue=False, command=self.validateHost)
        self.check_https.grid(row=row, column=1, sticky="w", padx=5)
        row += 1
        lbl_login = CTkLabel(appFrame, text="Login: ")
        lbl_login.grid(row=row, column=0, sticky="e")
        self.ent_login = PopoEntry(
            appFrame, placeholder_text="login", width=300)
        self.ent_login.grid(row=row, column=1, sticky="w", padx=5)
        row += 1
        lbl_passwd = CTkLabel(appFrame, text="Password: ")
        lbl_passwd.grid(row=row, column=0, sticky="e")
        self.password = tk.StringVar() 
        self.ent_passwd = PopoEntry(
            appFrame, placeholder_text="password", show="*", width=300, textvariable = self.password)
        self.ent_passwd.bind('<Return>', self.onOk)
        self.ent_passwd.grid(row=row, column=1, sticky="w", padx=5)
        appFrame.pack(padx=10, pady=10)
        self.ent_login.focus_set()
        cf1 = CollapsibleFrame(appFrame, text = "Advanced options", interior_padx=5, interior_pady=15)
        lbl_proxy = CTkLabel(cf1.interior, text="Proxy url : ")
        lbl_proxy.grid(row=0, column=0, sticky="e")
        self.ent_proxy = PopoEntry(cf1.interior, placeholder_text="http://127.0.0.1:8080")
        proxies = self.clientCfg.get("proxies", "")
        if proxies != "" and str(proxies).strip() != "{}":
            self.ent_proxy.insert(tk.END, proxies)
            cf1.toggle()
        self.ent_proxy.grid(row=0, column=1, sticky="w", padx=5)
        self.validateHost()

        cf1.update_width()

        cf1.grid(row=6,column=0, columnspan=2)

        self.ok_button = CTkButton(self.app, text="OK", command=self.onOk)
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
        config["proxies"] = self.ent_proxy.get()
        return config


    def validateHost(self, _event=None):
        """Validate host on both mongo and sftp connections. Change icons on the dialog accordingly.
        Returns:
            - True if the server is reachable on both mongo and sftp services, False otherwise. Does not test authentication.
        """
        apiclient = APIClient.getInstance()
        apiclient.reinitConnection()
        config = self.getForm()
        self.img_indicator.configure(image=self.waitingIcon())
        res = apiclient.tryConnection(config)
        if res:
            self.img_indicator.configure(image=self.validIcon())
        else:
            self.img_indicator.configure(image=self.badIcon())
        return res

    def valideLogin(self):
        pass

    def fill_with_uri(self, uri):
        regex_host = r"^(http|https)://([^:]+):(\d+)"
        groups = re.search(regex_host,uri)
        if groups:
            self.ent_hostname.delete(0, tk.END)
            self.ent_hostname.insert(0, groups.group(2))
            self.ent_port.delete(0, tk.END)
            self.ent_port.insert(0, groups.group(3))
            self.var_https.set(groups.group(1) == "https")

    def onError(self, _event=None):
        self.rvalue = None
        self.app.quit()
        
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
                self.rvalue = True
                self.app.destroy()
            else:
                tk.messagebox.showerror("Connection failure", "The login/password you entered does not exists")
        else:
            tk.messagebox.showerror("Connection failure", "The host is not responding. Check if server is alive or if you have a local proxy configured.")
