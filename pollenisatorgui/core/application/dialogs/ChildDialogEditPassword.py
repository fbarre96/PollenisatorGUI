"""ChildDialogEditPassword class
Ask the user to edit a user password"""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.forms.formpanel import FormPanel
from pollenisatorgui.core.views.viewelement import ViewElement
from pollenisatorgui.core.components.apiclient import APIClient

class ChildDialogEditPassword:
    """
    Open a child dialog of a tkinter application to ask a user to reset its password.
    """

    def __init__(self, parent, username, askOldPwd=True):
        """
        Open a child dialog of a tkinter application to ask the new password and possibly the old

        Args:
            parent: the tkinter parent view to use for this window construction.
            username: The username to reset the password of
            askOldPwd : a boolean to use changePassword (user api) or resetPassword (admin api)
        """
        self.parent = parent
        self.app = CTkToplevel(parent)
        self.app.attributes("-type", "dialog")
        self.app.bind("<Escape>", self.onError)
        self.askOldPwd = askOldPwd
        self.app.title("Change "+str(username)+" password")
        appFrame = CTkFrame(self.app)
        self.form = FormPanel()
        self.form.addFormLabel("Username")
        self.form.addFormStr("Username", ".+", default=username, readonly=True)
        if askOldPwd:
            self.form.addFormLabel("Old password")
            self.form.addFormStr("Old password", ".+", show="*")
        self.form.addFormLabel("New Password")
        self.form.addFormStr("New password", ".{8,}", show="*", error_msg="New password must be at least 8 characters long")
        self.form.addFormButton("OK", self.onOk)
        self.rvalue = None
        self.form.constructView(appFrame)
        appFrame.pack(ipadx=10, ipady=10)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.focus_force()
            self.app.grab_set()
            self.app.lift()
        except tk.TclError:
            pass

    def onError(self, _event=None):
        self.app.destroy()

    def onOk(self, _event=None):
        """Called the ok button is pressed.
        
        Args:
            _event: not used but mandatory"""
        res, msg = self.form.checkForm()
        apiclient = APIClient.getInstance()
        success = False
        if res:
            form_values = self.form.getValue()
            form_values_as_dicts = ViewElement.list_tuple_to_dict(form_values)
            username = form_values_as_dicts["Username"]
            newPwd = form_values_as_dicts["New password"]
            if self.askOldPwd:
                oldPwd = form_values_as_dicts["Old password"]
                msg = apiclient.changeUserPassword(oldPwd, newPwd)
            else:
                msg = apiclient.resetPassword(username, newPwd)
            if msg != "":
                tk.messagebox.showwarning(
                    "Change password", msg, parent=self.app)
        else:
            tk.messagebox.showwarning(
                "Form not validated", msg, parent=self.app)
        
        self.app.destroy()
        

