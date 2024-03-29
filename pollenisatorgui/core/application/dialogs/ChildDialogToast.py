"""Show a message to the user for a limited amount of time
"""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
import threading


class ChildDialogToast(CTkToplevel):
    """floating basic window with info text inside, fading away after a short time.
    """

    def __init__(self, parent, text, *args, **kwargs):
        """
        create the floating window but do not display it

        Args:
            parent: the tkinter parent view to use for this window construction.
            text: the text to display inside the toast
            args: not used
            kwargs: 
                - if fadingTime is defined, delay before fading starts. Default to 1.0s
                - if x is defined, x position of the toast top left corner, else default to parent x +25 .
                - if y is defined, y position of the toast top left corner, else default to parent botoom - 100.
        """
        super().__init__()

        self.text = text
        self.parent = parent
        self.kwargs = kwargs

    def show(self):
        """
        show the floating window, fading on 1.0 sec
        """
        x = self.kwargs.get("x")
        if x is None:
            x = self.parent.winfo_rootx() + 25
        y = self.kwargs.get("y")
        if y is None:
            y = (self.parent.winfo_rooty() + self.parent.winfo_reqheight() - 100)
        # creates a toplevel window
        # Leaves only the label and removes the app window
        self.wm_overrideredirect(True)
        self.wm_geometry("+%d+%d" % (x, y))
        w = self.kwargs.get("width", 200)
        h = self.kwargs.get("height", 20)
        self.geometry("%dx%d" % (w, h))
        label = CTkLabel(self, text=self.text, justify='left')
        label.pack(fill=tk.BOTH)
        self.transparency = 1.0
        fadingTime = self.kwargs.get("fadingTime", 1.0)
        self.timer_fade = None
        if fadingTime is not None:
            self.timer_fade = threading.Timer(fadingTime, self.fade)
            self.timer_fade.start()
        try:
            self.wait_visibility()
            self.lift()
        except tk.TclError:
            pass
    
    def moveto(self, x, y):
        self.wm_geometry("+%d+%d" % (x, y))

    def fade(self):
        try:
            self.transparency -= 0.2
            if self.transparency <= 0.0:
                self.destroy()
                del self
                return
            self.wm_attributes("-alpha", self.transparency)
            self.timer_fade = threading.Timer(0.1, self.fade)
            self.timer_fade.start()
        except RuntimeError:
            return