"""Defines a sub-swindow window for connecting to the server"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from PIL import ImageTk, Image
from io import BytesIO
import base64
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.utils import loadClientConfig, saveClientConfig, getValidMarkIconPath, getBadMarkIconPath, getWaitingMarkIconPath


class CollapsibleFrame(CTkFrame):
    def __init__(self, master, text=None, border_width=2, width=0, height=16, interior_padx=0, interior_pady=8, background=None, caption_separation=4, caption_font=None, caption_builder=None, icon_x=5):
        CTkFrame.__init__(self, master)
        
        self._is_opened = False

        self._interior_padx = interior_padx
        self._interior_pady = interior_pady

        self._iconOpen = "R0lGODlhEAAQAKIAAP///9TQyICAgEBAQAAAAAAAAAAAAAAAACwAAAAAEAAQAAADNhi63BMgyinFAy0HC3Xj2EJoIEOM32WeaSeeqFK+say+2azUi+5ttx/QJeQIjshkcsBsOp/MBAA7"
        self._iconClose = "R0lGODlhEAAQAKIAAP///9TQyICAgEBAQAAAAAAAAAAAAAAAACwAAAAAEAAQAAADMxi63BMgyinFAy0HC3XjmLeA4ngpRKoSZoeuDLmo38mwtVvKu93rIo5gSCwWB8ikcolMAAA7"
        self._iconOpen = Image.open(BytesIO(base64.b64decode(self._iconOpen)))
        self._iconClose = Image.open(BytesIO(base64.b64decode(self._iconClose)))
        height_of_icon = max(self._iconOpen.height, self._iconClose.height)
        width_of_icon = max(self._iconOpen.width, self._iconClose.width)
        
        containerFrame_pady = (height_of_icon//2) +1

        self._height = height
        self._width = width

        self._containerFrame = CTkFrame(self, border_width=border_width, width=width, height=height)
        self._containerFrame.pack(expand=True, fill=tk.X, pady=(containerFrame_pady,0))
        
        self.interior = CTkFrame(self._containerFrame)

        self._collapseButton = CTkLabel(self,  text= "", image=CTkImage(self._iconOpen))
        self._collapseButton.place(in_= self._containerFrame, x=icon_x, y=-(height_of_icon//2), anchor=tk.NW, bordermode="ignore")
        self._collapseButton.bind("<Button-1>", lambda event: self.toggle())

        if caption_builder is None:
            self._captionLabel = CTkLabel(self, anchor=tk.W, text=text)
            if caption_font is not None:
                self._captionLabel.configure(font=caption_font)
        else:
            self._captionLabel = caption_builder(self)
            
            if not isinstance(self._captionLabel, ttk.Widget):
                raise Exception("'caption_builder' doesn't return a tkinter widget")

        self.after(0, lambda: self._place_caption(caption_separation, icon_x, width_of_icon))

    def update_width(self, width=None):
        # Update could be devil
        # http://wiki.tcl.tk/1255
        self.after(0, lambda width=width:self._update_width(width))

    def _place_caption(self, caption_separation, icon_x, width_of_icon):
        self.update()
        x = caption_separation + icon_x + width_of_icon
        y = -(self._captionLabel.winfo_reqheight()//2)

        self._captionLabel.place(in_= self._containerFrame, x=x, y=y, anchor=tk.NW, bordermode="ignore")

    def _update_width(self, width):
        self.update()
        if width is None:
            width=self.interior.winfo_reqwidth()

        if isinstance(self._interior_pady, (list, tuple)):
            width += self._interior_pady[0] + self._interior_pady[1]
        else:
            width += 2*self._interior_pady
            
        width = max(self._width, width)

        self._containerFrame.configure(width=width)
        
    def open(self):
        self._collapseButton.configure(image=CTkImage(self._iconClose))
        
        self._containerFrame.configure(height=self.interior.winfo_reqheight())
        self.interior.pack(expand=True, fill=tk.X, padx=self._interior_padx, pady =self._interior_pady)

        self._is_opened = True

    def close(self):
        self.interior.pack_forget()
        self._containerFrame.configure(height=self._height)
        self._collapseButton.configure(image=CTkImage(self._iconOpen))

        self._is_opened = False
    
    def toggle(self):
        if self._is_opened:
            self.close()
        else:
            self.open()

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

    def __init__(self, parent, displayMsg="Connect to api:"):
        """
        Open a child dialog of a tkinter application to connect to a pollenisator server.

        Args:
            parent: the tkinter parent view to use for this window construction.
            displayMsg: The message that will explain to the user what the form is.
        """
        self.parent = parent
        self.app = CTkToplevel(parent)
        self.app.title("Connect to server")
        self.app.resizable(False, False)
        appFrame = CTkFrame(self.app)
        self.rvalue = None
        self.parent = parent
        self.clientCfg = loadClientConfig()
        lbl = CTkLabel(self.app, text=displayMsg)
        lbl.pack()
        
        lbl_hostname = CTkLabel(appFrame, text="Host : ")
        lbl_hostname.grid(row=0, column=0)
        self.ent_hostname = CTkEntry(
            appFrame, placeholder_text="127.0.0.1", validate="focusout", validatecommand=self.validateHost)
        self.ent_hostname.insert(tk.END, self.clientCfg["host"])
        self.ent_hostname.bind('<Return>', self.validateHost)
        self.ent_hostname.bind('<KP_Enter>', self.validateHost)
        self.ent_hostname.grid(row=0, column=1)
        lbl_port = CTkLabel(appFrame, text="Port : ")
        lbl_port.grid(row=1, column=0)
        self.ent_port = CTkEntry(
            appFrame, placeholder_text="5000", validate="focusout", validatecommand=self.validateHost)
        self.ent_port.insert(tk.END, self.clientCfg.get("port", 5000), )
        self.ent_port.bind('<Return>', self.validateHost)
        self.ent_port.bind('<KP_Enter>', self.validateHost)
        self.ent_port.grid(row=1, column=1)
        self.img_indicator = CTkLabel(appFrame, text="", image=self.waitingIcon())
        self.img_indicator.grid(row=1, column=2)
        self.var_https = tk.IntVar()
        lbl_https = CTkLabel(appFrame, text="https: ")
        lbl_https.grid(row=2, column=0)
        self.check_https = CTkSwitch(appFrame, variable=self.var_https, text="", onvalue=True, offvalue=False, command=self.validateHost)
        self.check_https.grid(row=2, column=1)
        
        lbl_login = CTkLabel(appFrame, text="Login: ")
        lbl_login.grid(row=4, column=0)
        self.ent_login = CTkEntry(
            appFrame, placeholder_text="login")
        self.ent_login.grid(row=4, column=1)
        lbl_passwd = CTkLabel(appFrame, text="Password: ")
        lbl_passwd.grid(row=5, column=0)
        self.password = tk.StringVar() 
        self.ent_passwd = CTkEntry(
            appFrame, placeholder_text="password", show="*", textvariable = self.password)
        self.ent_passwd.bind('<Return>', self.onOk)
        self.ent_passwd.grid(row=5, column=1)
        appFrame.pack(ipadx=10, ipady=10)
        self.ent_login.focus_set()
        cf1 = CollapsibleFrame(appFrame, text = "Advanced options", interior_padx=5, interior_pady=15)
        lbl_proxy = CTkLabel(cf1.interior, text="Proxy url : ")
        lbl_proxy.grid(row=0, column=0)
        self.ent_proxy = CTkEntry(cf1.interior, placeholder_text="http://127.0.0.1:8080")
        self.ent_proxy.insert(tk.END, self.clientCfg.get("proxies", ""), )
        self.ent_proxy.grid(row=0, column=1)
        self.validateHost()

        cf1.update_width()

        cf1.grid(row=6,column=1)

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
