import tkinter as tk
import tkinter.ttk as ttk
import os
import pollenisatorgui.core.Components.Utils as Utils
from pollenisatorgui.core.Components.apiclient import APIClient
from PIL import Image, ImageTk
from ttkwidgets import CheckboxTreeview, tooltips
import importlib
import multiprocessing
from shutil import which

class ScriptManager:
    """
    Open the scripts window manager
    """
    folder_icon = None
    def __init__(self, parent):
        """
            parent: the tkinter parent view to use for this window construction.
        """
        self.parent = parent
        self.app = tk.Toplevel(parent)
        self.app.title("Scripts Manager")
        self.app.resizable(True, True)
        self.rvalue = None
        appFrame = ttk.Frame(self.app)
         #PANED PART
        self.paned = tk.PanedWindow(appFrame, height=300)
        #RIGHT PANE : TAble
        self.viewframe = ttk.Frame(self.paned)
        self.file_tree = CheckboxTreeview(self.viewframe)
        self.file_tree['columns'] = ('name', 'category')
        self.file_tree.heading('#0', text='Name')
        self.file_tree.column("#0", stretch=tk.YES, minwidth=300, width=300)
        self.file_tree.heading('#1', text='Category')
        self.file_tree.column("#1", stretch=tk.YES, minwidth=300, width=300)
        self.file_tree.pack(fill=tk.BOTH, expand=True)
        btn_pane = ttk.Frame(self.viewframe)
        self.execute_icone = tk.PhotoImage(file = Utils.getIcon("execute.png"))
        btn_execute = ttk.Button(btn_pane, text="Execute", image=self.execute_icone, command=self.executedSelectedScripts, tooltip="Execute all selected scripts", style="icon.TButton")        
        btn_execute.pack(side=tk.RIGHT, padx=3, pady=5)
        self.open_folder_icone = tk.PhotoImage(file = Utils.getIcon("folder.png"))
        btn_openFolder = ttk.Button(btn_pane, text="Execute", image=self.open_folder_icone, command=self.openFolder, tooltip="Open scripts folder", style="icon.TButton")        
        btn_openFolder.pack(side=tk.RIGHT, padx=3, pady=5)
        
        btn_pane.pack(fill=tk.X, side=tk.BOTTOM, anchor=tk.E)
        #LEFT PANE : Treeview
        self.frameTw = ttk.Frame(self.paned)
        self.treevw = ttk.Treeview(self.frameTw)
        self.treevw.pack()
        scbVSel = ttk.Scrollbar(self.frameTw,
                                orient=tk.VERTICAL,
                                command=self.treevw.yview)
        self.treevw.configure(yscrollcommand=scbVSel.set)
        self.treevw.grid(row=0, column=0, sticky=tk.NSEW)
        scbVSel.grid(row=0, column=1, sticky=tk.NS)
        self.treevw.grid(row=0, column=0, sticky=tk.NSEW)
        scbVSel.grid(row=0, column=1, sticky=tk.NS)
        self.paned.add(self.frameTw)
        self.paned.add(self.viewframe)
        self.paned.pack(fill=tk.BOTH, expand=1)
        self.frameTw.rowconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        self.frameTw.columnconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize

        appFrame.pack(fill=tk.BOTH, ipady=10, ipadx=10, expand=True)

        self.treevw.bind("<<TreeviewSelect>>", self.onTreeviewSelect)
        try:
            self.app.wait_visibility()
            self.app.focus_force()
            self.app.lift()
        except tk.TclError:
            pass
        self.refreshUI()

    def refreshUI(self):
        for widget in self.treevw.winfo_children():
            widget.destroy()
        script_dir = self.getScriptsDir()
        if self.__class__.folder_icon is None:
            self.__class__.folder_icon = ImageTk.PhotoImage(Image.open(Utils.getIcon("folder.png")))
        parent = self.treevw.insert("", "end", " ", text="Scripts", image=self.__class__.folder_icon, open=True)
        self.treevw.focus(parent)
        self.treevw.selection_set(parent)
        for root, subFolders, files in os.walk(script_dir):
            root_name = root.replace(script_dir, "")
            for folder in subFolders:
                if folder.startswith("__") or folder.endswith("__"):
                    continue
                folder_iid = os.path.join(root_name, folder)
                parent_node = parent if root_name == "" else root_name
                self.treevw.insert(parent_node, "end", folder_iid, text=folder, image=self.__class__.folder_icon)
        self.openScriptFolderView()
        
    def getScriptsDir(self):
        return os.path.join(Utils.getMainDir(), "scripts/")

    def onTreeviewSelect(self, _event=None):
        
        selec = self.treevw.selection()
        if len(selec) == 0:
            return None
        item = selec[0]
        self.openScriptFolderView(str(item))

    def openScriptFolderView(self, script_folder=""):
        full_script_path = os.path.join(self.getScriptsDir(), script_folder.strip())
        script_shown = set()
        self.file_tree.delete(*self.file_tree.get_children())

        for root, _, files in os.walk(full_script_path):
            for file in files:
                filepath = root + '/' + file
                if file.endswith(".py"):
                    script_shown.add(filepath)
        scripts_list = sorted(script_shown)
        script_dir = self.getScriptsDir()
        for script in scripts_list:
            scriptName = os.path.basename(script)
            category_name = os.path.dirname(script.replace(script_dir, ""))
            self.file_tree.insert("", "end", script, text=scriptName, values=(category_name))
        

    def executedSelectedScripts(self):
        for selected in self.file_tree.get_checked():
            self.executeScript(selected)

    def executeScript(self, script_path):
        script_dir = self.getScriptsDir()
        category_name = os.path.dirname(script_path.replace(script_dir, ""))
        script_name = ".".join(os.path.splitext(os.path.basename(script_path))[:-1])
        module = os.path.join("pollenisatorgui/scripts/",category_name, script_name).replace("/", '.')
        imported = importlib.import_module(module)
        success, res = imported.main(APIClient.getInstance())
        if success:
            tk.messagebox.showinfo("Script finished", f"Script {script_name} finished.\n{res}")
        else:
            tk.messagebox.showwarning("Script failed", f"Script {script_name} failed.\n{res}")

    def openFolder(self):
        selection = self.treevw.selection()
        if selection:
            folder = os.path.join(self.getScriptsDir(), selection[0])
        else:
            folder = self.getScriptsDir()
        if which("xdg-open") is not None:
            os.system("xdg-open "+str(folder))
