"""Help the user to create a new pentest database.
"""
import tkinter as tk
from tkinter import ttk
from customtkinter import *
from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
from pollenisatorgui.core.application.scrollableframexplateform import ScrollableFrameXPlateform
from pollenisatorgui.core.application.scrollabletreeview import ScrollableTreeview
import pollenisatorgui.core.components.utils as utils
from PIL import Image, ImageTk

from pollenisatorgui.core.forms.formpanel import FormPanel

class ChildDialogToolsInstalled(CTkToplevel):
    """
    Open a child dialog of a tkinter application to show binary installed
    """
    cvalid_icon = None
    cbad_icon = None

    def validIcon(self):
        """Returns a icon indicating a valid state.
        Returns:
            ImageTk PhotoImage"""
        if self.__class__.cvalid_icon is None:
            self.__class__.cvalid_icon = ImageTk.PhotoImage(Image.open(utils.getValidMarkIconPath()))
        return self.__class__.cvalid_icon

    def badIcon(self):
        """Returns a icon indicating a bad state.
        Returns:
            ImageTk PhotoImage"""
        if self.__class__.cbad_icon is None:
            self.__class__.cbad_icon = ImageTk.PhotoImage(Image.open(utils.getBadMarkIconPath()))
        return self.__class__.cbad_icon

    
    def __init__(self, tools_results, parent=None):
        """
        Open a child dialog of a tkinter application to ask details about
        the new pentest.

        Args:
            parent: the tkinter parent view to use for this window construction.
        """
        super().__init__(parent)
        self.parent = parent
        self.tools_results = tools_results
        self.title("Tools configured supported")
        self.attributes("-type", "dialog")
        self.resizable(True, True)
        self.rvalue = None
        
        self.bind("<Escape>", self.quit)
        self.mainFrame = CTkFrame(self)
        self.reloadUI()
        self.mainFrame.pack(fill=tk.BOTH, ipadx=10, ipady=10, expand=1)
        try:
            self.wait_visibility()
            self.transient(self.parent)
            self.focus_force()
            self.grab_set()
            self.lift()
        except tk.TclError:
            pass

    def OnDoubleClick(self, event):
        item = self.tv.identify("item", event.x, event.y)
        if item is None or item == '':
            return
        plugin_name = self.tv.item(item)["text"]
        current_bin_path = self.tv.item(item)["values"][0]
        dialog_ask_text = ChildDialogAskText(self, info=f"New path for plugin {plugin_name}", default=current_bin_path ,multiline=False)
        self.wait_window(dialog_ask_text.app)
        if dialog_ask_text.rvalue is not None:
            new_path = dialog_ask_text.rvalue
            if utils.which_expand_alias(new_path):
                self.tv.item(item, values=(new_path,), image=self.validIcon())
            else:
                self.tv.item(item, values=(new_path,), image=self.badIcon())
                tk.messagebox.showerror("Invalid path", f"Path '{new_path}' does not seem to be detected as a valid binary.", parent=self)
    
    def reloadUI(self):
        for widget in self.mainFrame.winfo_children():
            widget.destroy()
        self.tv = ScrollableTreeview(self.mainFrame,('Plugin name','Local command Configured'), height=25, maxPerPage=25)
        self.tv.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=1)
        self.tv.bind("<Double-Button-1>", self.OnDoubleClick)
        for tool_result in self.tools_results.get("failures", []):
            self.tv.insert("", "end", tool_result["plugin"]["plugin"], text=tool_result["plugin"]["plugin"], values=(tool_result["bin_path"],),
                           image=self.badIcon())
        for tool_result in self.tools_results.get("successes", []):
            self.tv.insert("", "end", tool_result["plugin"]["plugin"], text=tool_result["plugin"]["plugin"], values=(tool_result["bin_path"],),
                           image=self.validIcon())
        CTkButton(self.mainFrame, text="OK", command=self.onOk).pack(side=tk.RIGHT)
            
        self.button = CTkButton(self.mainFrame, text="Cancel",command=self.onError,
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato").pack(side=tk.RIGHT)
        self.mainFrame.pack(fill=tk.BOTH, ipadx=10, ipady=10, expand=1)
        try:
            self.wait_visibility()
            self.transient(self.parent)
            self.focus_force()
            self.grab_set()
            self.lift()
        except tk.TclError:
            pass
    
    def onError(self, _event=None):
        self.rvalue = None
        self.destroy()

    def onOk(self, _event=None):
        """
        Called when the user clicked the validation button.
        launch parsing with selected parser on selected file/directory.
        Close the window.

        Args:
            _event: not used but mandatory
        """
        res = {}
        for item in self.tv.infos:
            command_name = item
            line_info = self.tv.infos[item]
            res[command_name] = line_info["values"][0]
        self.rvalue = res
        self.destroy()
        return