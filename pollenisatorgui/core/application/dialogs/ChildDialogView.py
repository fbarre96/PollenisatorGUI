"""This class pop a defect view form in a subdialog"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *


class ChildDialogView:
    """
    Open a child dialog of a tkinter application to answer a question.
    """
    def __init__(self, parent, title):
        """
        Open a child dialog of a tkinter application to choose autoscan settings.

        Args:
            parent: the tkinter parent view to use for this window construction.
            model : A Defect model object to load default values. None to have empty fields, default is None.
        """
        self.app = CTkToplevel(parent)
        self.app.title = title
        self.parent = parent
        self.app.resizable(True, True)
        self.app.geometry("800x600")
        self.container = CTkFrame(self.app)
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)
        self.rvalue = None
        self.canvas = tk.Canvas(self.container, bg="white")
        self.appFrame = CTkFrame(self.canvas)
        self.myscrollbar = CTkScrollbar(self.container, orientation="vertical", command=self.canvas.yview)
        self.canvas.bind('<Enter>', self.boundToMousewheel)
        self.canvas.bind('<Leave>', self.unboundToMousewheel)
        self.canvas.bind('<Configure>',  lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        ))
        self.canvas_main_frame = self.canvas.create_window((0, 0), window=self.appFrame, anchor='nw')
        self.canvas.configure(yscrollcommand=self.myscrollbar.set)  


    def completeDialogView(self, addButtons=True):
        if addButtons:
            ok_button = CTkButton(self.appFrame, text="OK")
            ok_button.pack(side="right", padx=5, pady=10)
            ok_button.bind('<Button-1>', self.okCallback)
            cancel_button = CTkButton(self.appFrame, text="Cancel")
            cancel_button.pack(side="right", padx=5, pady=10, ipadx=10)
            cancel_button.bind('<Button-1>', self.cancel)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.bind("<Configure>", self.resizeAppFrame)
        self.canvas.grid(column=0, row=0, sticky="nsew")
        self.myscrollbar.grid(column=1, row=0, sticky="ns")
        self.container.pack(fill=tk.BOTH, ipady=10, ipadx=10, expand=True)

        # self.appFrame.pack(fill=tk.X, ipady=10, ipadx=10, expand=True) this break the canvas drawing with scrollbar
        try:
            self.app.wait_visibility()
            self.app.transient(self.parent)
            self.app.grab_set()
            self.app.focus_force()
            self.app.lift()
        except tk.TclError:
            pass

    def resizeAppFrame(self, event):
        self.canvas.itemconfig(self.canvas_main_frame, height=self.appFrame.winfo_height(), width=event.width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def boundToMousewheel(self, _event=None):
        """Called when the **command canvas** is on focus.
        Bind the command scrollbar button on linux to the command canvas
        Args:
            _event: not used but mandatory
        """
        if self.canvas is None:
            return
        self.canvas.bind_all("<Button-4>", self._onMousewheel)
        self.canvas.bind_all("<Button-5>", self._onMousewheel)

    def unboundToMousewheel(self, _event=None):
        """Called when the **command canvas** is unfocused.
        Unbind the command scrollbar button on linux to the command canvas
        Args:
            _event: not used but mandatory"""
        if self.canvas is None:
            return
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def cancel(self, _event=None):
        """called when canceling the window.
        Close the window and set rvalue to False
        Args:
            _event: Not used but mandatory"""
        self.rvalue = False
        self.unboundToMousewheel()
        self.app.destroy()

    def okCallback(self, _event=None):
        """called when pressing the validating button
        Close the window if the form is valid.
        Set rvalue to True and perform the defect update/insert if validated.
        To be overriden
        Args:
            _event: Not used but mandatory"""
        
        pass

    def _onMousewheel(self, event):
        """Scroll the settings canvas
        Args:
            event: scroll info filled when scroll event is triggered"""
        if event.num == 5 or event.delta == -120:
            count = 1
        if event.num == 4 or event.delta == 120:
            count = -1
        self.canvas.yview_scroll(count, "units")