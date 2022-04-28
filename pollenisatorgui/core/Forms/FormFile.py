"""Widget with an entry to type a file path and a '...' button to pick from file explorer."""

import tkinter as tk
import tkinter.ttk as ttk
from pollenisatorgui.core.Forms.Form import Form
import pollenisatorgui.core.Components.Utils as Utils
import tkinter.filedialog
import os

class FormFile(Form):
    """
    Form field representing a path input.
    Default setted values: 
        state="readonly"
        if pack : padx = pady = 5, side = "right"
        if grid: row = column = 0 sticky = "west"
        entry "width"=  20
    Additional values to kwargs:
        modes: either "file" or "directory" to choose which type of path picker to open
    """

    def __init__(self, name, regexValidation="", default=[], **kwargs):
        """
        Constructor for a form file

        Args:
            name: the entry name (id).
            regexValidation: a regex used to check the input in the checkForm function., default is ""
            default: a default value for the Entry, default is ""
            kwargs: same keyword args as you would give to ttk.Frame + "modes" which is either "file" or "directory" 
                    to choose which type of path picker to open
        """
        super().__init__(name)
        self.regexValidation = regexValidation
        self.default = default
        self.kwargs = kwargs
        self.listbox = None

    def constructView(self, parent):
        """
        Create the string view inside the parent view given

        Args:
            parent: parent FormPanel.
        """
        self.val = tk.StringVar()
        frame = ttk.Frame(parent.panel)
        listboxframe = ttk.Frame(frame)
        self.listbox = tk.Listbox(listboxframe, 
                              width=self.getKw("width", 20), height=self.getKw("height", 10), selectmode=tk.SINGLE)
        self.listbox.register_drop_target("*")
        self.listbox.bind('<<Drop:File>>', self.add_path_listbox)
        self.scrolbar = tk.Scrollbar(
            listboxframe,
            orient=tk.VERTICAL
        )
        self.scrolbarH = tk.Scrollbar(
            listboxframe,
            orient=tk.HORIZONTAL
        )
        self.listbox.grid(row=0, column=0, sticky=tk.NSEW)
        self.scrolbar.grid(row=0, column=1, sticky=tk.NS)
        self.scrolbarH.grid(row=1, column=0, sticky=tk.EW)
        # displays the content in listbox
        self.listbox.configure(yscrollcommand=self.scrolbar.set)
        self.listbox.configure(xscrollcommand=self.scrolbarH.set)

        # view the content vertically using scrollbar
        self.scrolbar.config(command=self.listbox.yview)
        self.scrolbarH.config(command=self.listbox.xview)
        for d in self.default:
            self.listbox.insert("end", d)
        listboxframe.pack(side="top", fill=tk.X, expand=1)
        self.modes = self.getKw("mode", "file").split("|")
        btn_frame = ttk.Frame(frame)
        info = ttk.Label(btn_frame, text="Or Drag and Drop")
        info.pack(side="right", pady=5)
        if "file" in self.modes:
            text = self.getKw("text", "add file")
            search_btn = ttk.Button(
                btn_frame, text=text, command=self.on_click)
            search_btn.pack(side="right", pady=5)
        if "directory" in self.modes:
            text = self.getKw("text", "add directory")
            search_btn = ttk.Button(
                btn_frame, text=text, command=self.on_click_dir)
            search_btn.pack(side="right", pady=5)
        
        btn_frame.pack(side=tk.BOTTOM)
        if parent.gridLayout:
            frame.grid(row=self.getKw("row", 0),
                       column=self.getKw("column", 0), **self.kwargs)
        else:
            frame.pack(fill=self.getKw("fill", "x"), side=self.getKw(
                "side", "top"), anchor=self.getKw("anchor", "center"), pady=self.getKw("pady", 5), padx=self.getKw("padx", 10), **self.kwargs)

    def on_click(self, _event=None):
        """Callback when '...' is clicked and modes Open a file selector (tkinter.filedialog.askopenfilename)
        Args:
            _event: not used but mandatory
        Returns:
            None if no file name is picked,
            the selected file full path otherwise.
        """
        f = tkinter.filedialog.askopenfilename(title="Select a file")
        if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return
        if f != "":
            filename = str(f)
            self.listbox.insert("end", filename)

    def on_click_dir(self, _event=None):
        """Callback when '...' is clicked and modes="directory" was set.
        Open a directory selector (tkinter.filedialog.askdirectory)
        Args:
            _event: not used but mandatory
        Returns:
            None if no directory is picked,
            the selected directory full path otherwise.
        """
        f = tkinter.filedialog.askdirectory(title="Select a directory")
        if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return
        if f != "":
            filename = str(f)
            self.listbox.insert("end", filename)

    def getValue(self):
        """
        Return the form value. Required for a form.

        Returns:
            Return the entry value as string.
        """
        return list(self.listbox.get('@1,0', tk.END))

    def checkForm(self):    
        """
        Check if this form is correctly filled. Check with the regex validation given in constructor.

        Returns:
            {
                "correct": True if the form is correctly filled, False otherwise.
                "msg": A message indicating what is not correctly filled.
            }
        """
        import re
        values = self.getValue()
        if not values and self.kwargs.get("required", False):
            return False, f"this form must is required {self.name}"
        for value in values:
            if re.match(self.regexValidation,value) is None:
                return False, f"{value} is incorrect"
        return True, ""

    def setFocus(self):
        """Set the focus to the ttk entry part of the widget.
        """
        self.lsitbox.focus_set()

    def add_path_listbox(self, event):
        data = Utils.drop_file_event_parser(event)
        for d in data:
            if os.path.isfile(d) and "file" in self.modes:
                self.listbox.insert("end", d)
            elif os.path.isdir(d) and "directory" in self.modes:
                self.listbox.insert("end", d)
