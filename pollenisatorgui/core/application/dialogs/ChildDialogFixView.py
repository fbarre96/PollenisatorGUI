"""This class pop a defect view form in a subdialog"""

import tkinter as tk
import tkinter.ttk as ttk

class ChildDialogFixView:
    """
    Open a child dialog of a tkinter application to answer a question.
    """
    def __init__(self, parent, fixModel=None):
        """
        Open a child dialog of a tkinter application to choose autoscan settings.

        Args:
            parent: the tkinter parent view to use for this window construction.
            defectModel : A Defect Model object to load default values. None to have empty fields, default is None.
        """
        self.app = tk.Toplevel(parent)
        self.app.title("Fix edition")
        self.app.resizable(True, True)
        self.rvalue = None
        topFrame = ttk.Frame(self.app)
        appFrame = ttk.Frame(topFrame)
        if fixModel is None:
            fixModel = {"title":"Title", "gain": "Moderate", "execution": "Moderate"}

        title_lbl = ttk.Label(appFrame, text="Title:")
        title_lbl.pack(side="left")
        self.title_entry = ttk.Entry(appFrame, width=50)
        self.title_entry.pack(side="left")
        self.title_entry.insert(0, fixModel.get("title", ""))
        execution_lbl = ttk.Label(appFrame, text="Execution:")
        execution_lbl.pack(side="left")
        self.execution_combo = ttk.Combobox(appFrame, values=tuple(["Quick Win", "Moderate", "Arduous"]),state="readonly")
        self.execution_combo.pack(side="left")
        self.execution_combo.set(fixModel.get("execution", "Moderate"))
        gain_lbl = ttk.Label(appFrame, text="Gain:")
        gain_lbl.pack(side="left")
        self.gain_combo = ttk.Combobox(appFrame, values=tuple(["Weak", "Mean", "Strong"]),state="readonly")
        self.gain_combo.pack(side="left")
        self.gain_combo.set(fixModel.get("gain", "Mean"))
        appFrame.pack(fill=tk.BOTH, ipady=10, ipadx=10, expand=True)
        detailedFrame = ttk.Frame(topFrame)
        self.synthesis_txt = tk.scrolledtext.ScrolledText(detailedFrame, relief=tk.SUNKEN, height=3)
        self.synthesis_txt.pack(fill="x")
        self.synthesis_txt.insert(tk.INSERT, fixModel.get("synthesis", "Synthesis"))
        self.description_txt = tk.scrolledtext.ScrolledText(detailedFrame, relief=tk.SUNKEN, height=7)
        self.description_txt.pack(fill="x")
        self.description_txt.insert(tk.INSERT, fixModel.get("description", "Description"))
        detailedFrame.pack(fill=tk.BOTH, ipady=10, ipadx=10, expand=True)
        btn_frame = ttk.Frame(topFrame)
        cancel_button = ttk.Button(btn_frame, text="Cancel")
        cancel_button.pack(side="left", padx=5, pady=10)
        cancel_button.bind('<Button-1>', self.cancel)
        ok_button = ttk.Button(btn_frame, text="OK")
        ok_button.pack(side="left", padx=5, pady=10)
        ok_button.bind('<Button-1>', self.okCallback)
        topFrame.pack(side="top")
        btn_frame.pack(side="bottom", anchor="e")
        self.app.transient(parent)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.grab_set()
            self.app.focus_force()
            self.app.lift()
        except tk.TclError:
            pass

    def cancel(self, _event=None):
        """called when canceling the window.
        Close the window and set rvalue to False
        Args:
            _event: Not used but mandatory"""
        self.rvalue = None
        self.app.destroy()

    def okCallback(self, _event=None):
        """called when pressing the validating button
        Close the window if the form is valid.
        Set rvalue to True and perform the defect update/insert if validated.
        Args:
            _event: Not used but mandatory"""
        
        title = self.title_entry.get().strip()
        gain = self.gain_combo.get()
        execution = self.execution_combo.get()
        synthesis = self.synthesis_txt.get('1.0', tk.END)
        description = self.description_txt.get('1.0', tk.END)
        self.rvalue = {"title":title, "gain":gain, "execution":execution, "synthesis":synthesis, "description":description}
        self.app.destroy()