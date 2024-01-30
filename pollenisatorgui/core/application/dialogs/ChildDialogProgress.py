"""Show a progess bar for the user.
"""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *


class ChildDialogProgress:
    """
    Open a child dialog of a tkinter application to inform the user about a ongoing process.
    """

    def __init__(self, parent, title, msg, speed=1, progress_mode="determinate", show_logs=False):
        """
        Open a child dialog of a tkinter application to display a progress bar.

        Args:
            parent: the tkinter parent view to use for this window construction.
            title: Title for the new window
            msg: Message to display on the window to inform about a progession.
            progress_mode: mode of progression. Either "determinate" or "inderterminate". Default to the second.
                           indeterminate: bouncing progress bar.
                           determinate: Show progression of a value against a max value.
        """
        self.app = CTkToplevel(parent)
        self.app.attributes("-type", "dialog")
        self.app.transient(parent)
        self.app.resizable(False, False)
        self.app.title(title)
        appFrame = CTkFrame(self.app)
        self.rvalue = None
        self.parent = parent
        self.lbl = CTkLabel(appFrame, text=msg)
        self.lbl.pack(side=tk.TOP, padx=10, pady=10, fill=tk.X)
        self.mode = progress_mode
        self.show_logs = show_logs
        if self.show_logs:
            self.text_log = CTkTextbox(
                appFrame, wrap="word")
            self.text_log.pack(side=tk.BOTTOM, padx=10,pady=10,fill=tk.X)
        if progress_mode == "determinate":
            speed = (100/speed)*50/100
        self.progressbar = CTkProgressBar(appFrame, orientation="horizontal",
                                           indeterminate_speed=speed, determinate_speed=speed, mode=progress_mode)
        self.progressbar.set(0)
        self.progressbar.pack(side=tk.BOTTOM, padx=10, pady=10, fill=tk.X)
        appFrame.pack(fill=tk.BOTH)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.focus_force()
            #self.app.grab_set()
            self.app.lift()
        except tk.TclError:
            pass

    def show(self, maximum=None, startValue=0):
        """Start displaying the progressbar.
        Args:
            - maximum: only for determinate mode. Set the goal value. Default to None.
            - startValue: only for determinate mode. Set the starting value. Default to None.
        """
        self.progressbar.start()
        self.app.update()


    def update(self, value=None, msg=None, log=None):
        """Update the progressbar and show progression value.
        Call this regularly if on inderminate mode.
        Args:
            - value: The new value for the progressbar. Default to None.
        """
        try:
            if self.mode == "indeterminate":
                try:
                    self.progressbar.step()
                except tk.TclError:
                    return
            elif self.mode == "determinate":
                self.progressbar.step()
            if msg is not None:
                self.lbl.configure(text=str(msg))
            if self.show_logs and log is not None:
                self.text_log.insert(tk.END, log)
                self.text_log.see(tk.END)
            self.app.update()
        except tk.TclError as e:
            #Probably exited
            raise e

    def destroy(self):
        """
        Close the window and stop the progressbar.
        """
        # send the data to the parent
        self.progressbar.stop()
        self.app.destroy()
