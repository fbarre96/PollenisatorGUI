"""
Extend the CTkScrollableFrame to bind also for linux
<MouseWheel> event is not handled by some distributions that only handle <Button-4> and <Button-5> events.
"""

from customtkinter import *
import tkinter as tk 

class ScrollableFrameXPlateform(CTkScrollableFrame):
    def __init__(self, parent, orientation=tk.VERTICAL, **kwargs):
        super().__init__(parent, orientation=orientation, **kwargs)
        self.parent = parent
        self.activate()


    def activate(self):
        self.bind('<Enter>', self.boundToMousewheel)
        self.bind('<Leave>', self.unboundToMousewheel)

    def _onMousewheel(self, event):
        """Scroll the settings canvas
        Args:
            event: scroll info filled when scroll event is triggered"""
        if event.num == 5 or event.delta == -120:
            count = -1
        if event.num == 4 or event.delta == 120:
            count = 1
        try:
            self.event_generate("<MouseWheel>", delta=count)
        except tk.TclError:
            pass
        

    def boundToMousewheel(self, _event=None):
        """Called when the main view canvas is focused.
        Bind the command scrollbar button on linux to the main view canvas
        Args:
            _event: not used but mandatory"""
        self.bind_all("<Button-5>", self._onMousewheel)
        self.bind_all("<Button-4>", self._onMousewheel)

    def unboundToMousewheel(self, _event=None):
        """Called when the main view canvas is unfocused.
        Unbind the command scrollbar button on linux to the main view canvas
        Args:
            _event: not used but mandatory"""
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")