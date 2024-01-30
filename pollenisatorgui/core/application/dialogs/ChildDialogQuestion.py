"""Ask a question to the user.
"""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
import pollenisatorgui.core.components.utils as utils

class ChildDialogQuestion:
    """
    Open a child dialog of a tkinter application to ask a question.
    """

    def __init__(self, parent, title, question, answers=("Yes", "No")):
        """
        Open a child dialog of a tkinter application to ask a question.

        Args:
            parent: the tkinter parent view to use for this window construction.
            title: title of the new window
            question: question to answer
            answers: a tuple with possible answers. Default to ("Yes" ,"No")
        """
        self.app = CTkToplevel(parent)
        self.app.attributes("-type", "dialog")
        self.app.title(title)
        self.app.resizable(True, True)
        
        appFrame = CTkFrame(self.app)
        self.rvalue = None
        self.parent = parent
        lbl = CTkLabel(appFrame, text=question)
        lbl.pack(side=tk.TOP, padx=10, pady=10, fill=tk.X)
        buttonsFrame = CTkFrame(appFrame)
        for i, answer in enumerate(answers):
            if answer == "Cancel" or answer == "No":
                self.cancel_button = CTkButton(buttonsFrame, text=answer, fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                                border_width=1, border_color="firebrick1", hover_color="tomato")
                self.app.bind("<Escape>", self.escape)
                self.cancel_button.bind("<Button-1>", self.onOk)
                self.cancel_button.grid(row=0, column=i, padx=15)
            else:
                _button = CTkButton(buttonsFrame, text=answer)
                _button.bind("<Button-1>", self.onOk)
                _button.grid(row=0, column=i, padx=15)

        buttonsFrame.pack(side=tk.TOP, ipadx=5, pady=5)
        appFrame.pack(fill=tk.BOTH)
        _button.focus_set()
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.focus_force()
            self.app.grab_set()
            self.app.lift()
        except tk.TclError:
            pass

    def escape(self, _event=None):
        self.rvalue = self.cancel_button.cget("text")
        self.quit()
        
    def onOk(self, event):
        """
        Called when the user clicked the validation button.
        Set the rvalue attributes to the answer string choosen.
        """
        # send the data to the parent
        widget = event.widget.master
        self.rvalue = widget.cget("text")
        self.quit()

    def quit(self):
        self.app.destroy()
