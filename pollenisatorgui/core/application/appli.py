"""
Pollenisator client GUI window.
"""
import traceback
import tkinter.filedialog
import tkinter as tk
import tkinter.messagebox
import tkinter.simpledialog
import tkinter.ttk as ttk
from customtkinter import *
import sys
import os
from tkinter import TclError
import datetime
import json
import re
from PIL import ImageTk, Image
import importlib
import pkgutil
import socketio
from pollenisatorgui.core.application.scrollableframexplateform import ScrollableFrameXPlateform
from pollenisatorgui.core.components.datamanager import DataManager
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.treeviews.PentestTreeview import PentestTreeview
from pollenisatorgui.core.application.treeviews.CommandsTreeview import CommandsTreeview
from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.application.dialogs.ChildDialogConnect import ChildDialogConnect
from pollenisatorgui.core.application.dialogs.ChildDialogPentests import ChildDialogPentests
from pollenisatorgui.core.application.dialogs.ChildDialogException import ChildDialogException
from pollenisatorgui.core.application.dialogs.ChildDialogFileParser import ChildDialogFileParser
from pollenisatorgui.core.application.dialogs.ChildDialogEditPassword import ChildDialogEditPassword
from pollenisatorgui.core.application.statusbar import StatusBar
from pollenisatorgui.core.components.apiclient import APIClient, ErrorHTTP
from pollenisatorgui.core.components.scanmanager import ScanManager
from pollenisatorgui.core.components.admin import AdminView
from pollenisatorgui.core.components.scriptmanager import ScriptManager
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.components.filter import Filter
from pollenisatorgui.core.forms.formpanel import FormPanel
from pollenisatorgui.core.models.port import Port
from pollenisatorgui.core.views.checkinstanceview import CheckInstanceView
from pollenisatorgui.core.views.checkitemview import CheckItemView
from pollenisatorgui.core.views.ipview import IpView
import pollenisatorgui.modules
import customtkinter
import tkinterDnD
from ttkwidgets import tooltips

from pollenisatorgui.modules.module import Module

class FloatingHelpWindow(CTkToplevel):
    """floating basic window with helping text inside
    Inherit tkinter TopLevel
    Found on the internet (stackoverflow) but did not keep link sorry...
    """

    def __init__(self, w, h, posx, posy, *args, **kwargs):
        CTkToplevel.__init__(self, *args, **kwargs)
        self.title('Help: search')
        self.x = posx
        self.y = posy
        self.geometry(str(w)+"x"+str(h)+"+"+str(posx)+"+"+str(posy))
        self.resizable(0, 0)
        self.configure(bg='light yellow')
        self.grip = tk.Label(self, bitmap="gray25")
        self.grip.pack(side="left", fill="y")
        label = tk.Label(self, bg='light yellow', fg='black',
                         justify=tk.LEFT, text=Filter.help())
        label.pack()
        self.overrideredirect(True)
        self.grip.bind("<ButtonPress-1>", self.startMove)
        self.grip.bind("<ButtonRelease-1>", self.stopMove)
        self.grip.bind("<B1-Motion>", self.onMotion)

    def startMove(self, event):
        """ Floating window dragging started
            Args:
                event: event.x and event.y hold the new position of the window
        """
        self.x = event.x
        self.y = event.y

    def stopMove(self, _event):
        """ Floating window dragging stopped
            Args:
                _event: Not used but mandatory
        """
        self.x = None
        self.y = None

    def onMotion(self, event):
        """ Floating window dragging ongoing
            Args:
                event: event.x and event.y hold the new position of the window
        """
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry("+%s+%s" % (x, y))


class AutocompleteEntry(CTkEntry):
    """Inherit CTkEntry.
    An entry with an autocompletion ability.
    Found on the internet : http://code.activestate.com/recipes/578253-an-entry-with-autocompletion-for-the-tkinter-gui/
    But a bit modified.
    """

    def __init__(self, settings, *args, **kwargs):
        """Constructor
        Args:
            settings: a dict of Settings:
                * histo_filters: number of history search to display
            args: not used
            kwargs: 
                * width: default to 100
        """
        CTkEntry.__init__(self, *args, **kwargs)
        self.width = kwargs.get("width",100)
        self.lista = set()
        self.var = self.cget("textvariable")
        if self.var is None:
            self.var = tk.StringVar()
            self.configure(textvariable=self.var)
        self.var.trace('w', self.changed)
        
        self.bind("<Right>", self.selection)
        self.bind("<Up>", self.upArrow)
        self.bind("<Down>", self.downArrow)
        self.settings = settings
        self.server_time = None
        self.lb = None
        self.lb_up = False
        

    def changed(self, _name=None, _index=None, _mode=None):
        """
        Called when the entry is modified. Perform autocompletion.
        Args:
            _name: not used but mandatory for tk.StringVar.trace
            _index: not used but mandatory for tk.StringVar.trace
            _mode: not used but mandatory for tk.StringVar.trace
        """
        words = self.comparison()
        if words:
            if not self.lb_up:
                self.lb = tk.Listbox(width=self.width, fg=utils.getTextColor(), bg=utils.getBackgroundColor())
                self.lb.bind("<Double-Button-1>", self.selection)
                self.lb.bind("<Right>", self.selection)
                self.lb.bind("<Leave>", self.quit)
                self.bind("<Escape>", self.quit)
                self.lb.place(x=self.winfo_x()+133,
                                y=self.winfo_y()+self.winfo_height()+20)
                self.lb_up = True
            self.lb.delete(0, tk.END)
            for w in words:
                self.lb.insert(tk.END, w)
        else:
            self.quit()

    def quit(self, _event=None):
        """
        Callback function to destroy the label shown
        Args:
            _event: not used but mandatory
        """
        if self.lb_up:
            self.lb.destroy()
            self.lb_up = False
    
    def reset(self):
        """
        quit and reset filter bar
        """
        self.quit()
        self.var.set("")

    def selection(self, _event):
        """
        Called when an autocompletion option is chosen. 
        Change entry content and close autocomplete.
        Args:
            _event: not used but mandatory
        """
        if self.lb_up:
            self.var.set(self.lb.get(tk.ACTIVE))
            self.lb.destroy()
            self.lb_up = False
            self.icursor(tk.END)
            #self.changed()

    def upArrow(self, _event):
        """
        Called when the up arrow is pressed. Navigate in autocompletion options
        Args:
            _event: not used but mandatory
        """
        if self.lb_up:
            if self.lb.curselection() == ():
                index = '0'
            else:
                index = self.lb.curselection()[0]
            if index != '0':
                self.lb.selection_clear(first=index)
                index = str(int(index)-1)
                self.lb.selection_set(first=index)
                self.lb.activate(index)

    def downArrow(self, _event):
        """
        Called when the down arrow is pressed. Navigate in autocompletion options
        Args:
            _event: not used but mandatory
        """
        if self.lb_up:
            if self.lb.curselection() == ():
                index = '0'
            else:
                index = self.lb.curselection()[0]
            if index != tk.END:
                self.lb.selection_clear(first=index)
                index = str(int(index)+1)
                self.lb.selection_set(first=index)
                self.lb.activate(index)

    def comparison(self):
        """
        Search suggestions in regard of what is in the entry
        """
        values = set(self.settings.local_settings.get("histo_filters", []))
        self.lista = values
        content = self.var.get().strip()
        if content == "":
            return []
        pattern = re.compile('.*' + re.escape(content) + '.*')
        return [w for w in self.lista if re.match(pattern, w)]

def iter_namespace(ns_pkg):
    # Specifying the second argument (prefix) to iter_modules makes the
    # returned name an absolute name instead of a relative one. This allows
    # import_module to work without having to do additional modification to
    # the name.
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")

class ButtonNotebook(CTkFrame):
    def __init__(self, parent, callbackSwitch, closeCallbackSwitch):
        super().__init__(parent)
        style = ttk.Style()
        self.frameButtons = CTkFrame(self, fg_color=('#113759'))
        self.callbackSwitch = callbackSwitch
        self.closeCallbackSwitch = closeCallbackSwitch
        self.tabs = {}
        self.current = None
        self.frameButtons.pack(side="left", anchor="nw", fill=tk.Y)
        self.btns = {}

    def add(self, widget, name, order, image):
        if name not in self.tabs:
            self.tabs[name] = {"widget":widget, "image":image, "order": order, "name":name}
            widget.pack_forget()
            btn = CTkButton(self.frameButtons, text=name, image=image,  fg_color='#113759' , hover_color=('#061b4e'), compound=tk.TOP)
            self.btns[name] = btn
            btn.bind("<Button-1>", self.clicked)
            self.redraw()

    def redraw(self):
        for btn in self.btns.values():
            btn.pack_forget()
        btns = sorted(self.tabs.values(), key=lambda x:x["order"])
        for btn in btns:
            
            self.btns[btn["name"]].pack(side="top", fill=tk.X, anchor="nw")

    def clicked(self, event):
        widget = event.widget.master
        name = widget.cget("text")
        self.select(name)

    def getOpenTabName(self):
        return self.current


    def delete(self, name):
        if name in self.tabs:
            del self.tabs[name]
            self.btns[name].pack_forget()

    def select(self, name):
        if self.current == name:
            return
        if self.current:
            self.tabs[self.current]["widget"].pack_forget()
            self.btns[self.current].configure(fg_color="#113759")

            self.closeCallbackSwitch(self.current, name)
        self.current = name
        self.btns[name].configure(fg_color="#061b4e")
        self.tabs[name]["widget"].pack(side="right", expand=True, anchor="center", fill=tk.BOTH)
        self.callbackSwitch(name)


class Appli(customtkinter.CTk, tkinterDnD.tk.DnDWrapper):#HACK to make work tkdnd with CTk
    """
    Main tkinter graphical application object.
    """
    version_compatible = "1.5.*"

    
    def _init_tkdnd(master: tk.Tk) -> None: #HACK to make work tkdnd with CTk
        """Add the tkdnd package to the auto_path, and import it"""
        #HACK Copied from directory with a package_dir updated
        platform = master.tk.call("tk", "windowingsystem")

        if platform == "win32":
            folder = "windows"
        elif platform == "x11":
            folder = "linux"
        elif platform == "aqua":
            folder = "mac"
        package_dir = os.path.join(os.path.dirname(os.path.abspath(tkinterDnD.tk.__file__)), folder)
        master.tk.call('lappend', 'auto_path', package_dir)
        TkDnDVersion = master.tk.call('package', 'require', 'tkdnd')
        return TkDnDVersion

    def __init__(self):
        """
        Initialise the application

        """
        # Lexic:
        # view frame : the frame in the tab that will hold forms.
        # Tree view : the tree on the left of the window.
        # frame tree view : a frame around the tree view (useful to attach a scrollbar to a treeview)
        # paned : a Paned widget is used to separate two other widgets and display a one over the other if desired
        #           Used to separate the treeview frame and view frame.
        super().__init__()
        self.TkDnDVersion = self._init_tkdnd()  #HACK to make work tkdnd with CTk
        self.quitting = False
        self.settingViewFrame = None
        self.scanManager = None  #  Loaded when clicking on it if linux only
        self.scanViewFrame = None
        self.admin = None
        self.nbk = None
        self.sio = None #socketio client
        self.initialized = False
        self.settings = Settings()

        utils.setStyle(self, self.settings.local_settings.get("dark_mode", False))
        self.main_tab_img = CTkImage(
            Image.open(utils.getIconDir()+"tab_main.png"), size=(30, 30))
        self.commands_tab_img = CTkImage(
            Image.open(utils.getIconDir()+"tab_commands.png"), size=(30, 30))
        self.scan_tab_img = CTkImage(
            Image.open(utils.getIconDir()+"tab_scan.png"), size=(30, 30))
        self.settings_tab_img = CTkImage(
            Image.open(utils.getIconDir()+"tab_settings.png"), size=(30, 30))
        self.admin_tab_img = CTkImage(
            Image.open(utils.getIconDir()+"tab_admin.png"), size=(30, 30))
        # HISTORY : Main view and command where historically in the same view;
        # This results in lots of widget here with a confusing naming style
        #### core components (Tab menu on the left objects)####
        #### MAIN VIEW ####
        self.openedViewFrameId = None
        self.mainPageFrame = None
        self.paned = None
        self.proxyFrameMain = None
        self.viewframe = None
        self.frameTw = None
        self.treevw = None
        self.datamanager = None
        self.myscrollbarMain = None
        #### COMMAND VIEW ####
        self.commandsPageFrame = None
        self.commandPaned = None
        self.commandsFrameTw = None
        self.commandsViewFrame = None
        self.myscrollbarCommand = None
        self.commandsTreevw = None
        #### SEARCH BAR ####
        # boolean set to true when the main tree view is displaying search results
        self.searchMode = False
        self.searchBar = None  # the search bar component
        self.btnHelp = None  # help button on the right of the search bar
        self.photo = None  # the ? image
        self.helpFrame = None  # the floating help frame poping when the button is pressed
        dir_path = utils.getIconDir() +"favicon.png"
        img = tk.PhotoImage(file=dir_path)
        self.resizable(True, True)
        self.iconphoto(True, img)
        self.minsize(width=400, height=400)
        self.resizable(True, True)
        self.title("Pollenisator")
        self.geometry("1400x830")
        self.protocol("WM_DELETE_WINDOW", self.onClosing)
        self.datamanager = DataManager.getInstance()
        self.initModules()
        apiclient = APIClient.getInstance()
        self.scanManager = ScanManager(self, self.nbk, self.treevw, apiclient.getCurrentPentest(), self.settings)

        apiclient.appli = self
        opened = self.openConnectionDialog()

        if not opened:
            try:
                self.wait_visibility()
            except tk.TclError: #closed dialog
                return
            self.openConnectionDialog(force=True)
            self.openPentestsWindow()
        self.loadModulesInfos() 
        self.scanManager.nbk = self.nbk #FIXME ORDER, INITIALISATION of SCAN MANAGERis too early
        self.scanManager.linkTw = self.treevw

    def start_autoscan(self):
        return self.scanManager.startAutoscan()

    def stop_autoscan(self):
        return self.scanManager.stop()

    # OVERRIDE tk.Tk.report_callback_exception
    def report_callback_exception(self, exc, val, tb):
        self.show_error(exc, val, tb)
        
    def quit(self):
        super().quit()
        self.quitting = True
        return

    def forceUpdate(self, api_version, my_version):
        tkinter.messagebox.showwarning("Update necessary", f"Clash of version. Expecting API {api_version} and you are compatible with {my_version}. Please reinstall following the instructions in README. (git pull; pip install .)")

    def openConnectionDialog(self, force=False):
        # Connect to database and choose database to open
        apiclient = APIClient.getInstance()
        abandon = False
        connectionTest = apiclient.tryConnection(force=force)
        if force:
            apiclient.disconnect()
        res = apiclient.tryAuth()
        if not res: 
            apiclient.disconnect()
        while (not connectionTest or not apiclient.isConnected()) and not abandon:
            abandon = self.promptForConnection() is None
            connectionTest = apiclient.tryConnection(force=force)
        if not abandon:
            apiclient = APIClient.getInstance()
            apiclient.attach(self)
            srv_version = apiclient.getVersion()
            if int(Appli.version_compatible.split(".")[0]) != int(srv_version.split(".")[0]):
                self.forceUpdate(".".join(srv_version.split(".")[:-1]), Appli.version_compatible)
                self.onClosing()
                return False
            if int(Appli.version_compatible.split(".")[1]) != int(srv_version.split(".")[1]):
                self.forceUpdate(".".join(srv_version.split(".")[:-1]), Appli.version_compatible)
                self.onClosing()
                return False
            if self.sio is not None:
                self.sio.disconnect()
            self.sio = socketio.Client()
            @self.sio.event
            def notif(data):
                self.handleNotif(json.loads(data, cls=utils.JSONDecoder))
            
            @self.sio.event
            def test(data):
                tk.messagebox.showinfo("test", "test socket working received data : "+str(data))
           
            self.sio.connect(apiclient.api_url)
            pentests = apiclient.getPentestList()
            if pentests is None:
                pentests = []
            else:
                pentests = [x["nom"] for x in pentests][::-1]
            if apiclient.getCurrentPentest() != "" and apiclient.getCurrentPentest() in pentests:
                self.openPentest(apiclient.getCurrentPentest())
            else:
                self.openPentestsWindow()
            self.initialized = True
        else:
            self.onClosing()
            try:
                self.destroy()
            except tk.TclError:
                pass
        return apiclient.isConnected()
    
    def initModules(self):
        discovered_plugins = {
            name: importlib.import_module(name)
            for finder, name, ispkg
            in iter_namespace(pollenisatorgui.modules) if not name.endswith(".Module")
        }
        self.modules = []
        from pollenisatorgui.modules.module import REGISTRY
        for name, module_class in REGISTRY.items():
            if name != "Module":
                module_obj = module_class(self, self.settings)
                self.modules.append({"name": module_obj.tabName, "object":module_obj, "view":None, "img":CTkImage(Image.open(utils.getIconDir()+module_obj.iconName), size=(30, 30))})
        
    def loadModulesInfos(self):
        for module in self.modules:
            if callable(getattr(module["object"], "loadModuleInfo", False)):
                module["object"].loadModuleInfo()

    def show_error(self, *args):
        """Callback for tk.Tk.report_callback_exception.
        Open a window to display exception with some actions possible

        Args:
            args: 3 args are required for tk.Tk.report_callback_exception event to be given to traceback.format_exception(args[0], args[1], args[2])
        
        Raises:
            If an exception occurs in this handler thread, will print it and exit with exit code 1
        """
        try:
            err = traceback.format_exception(args[0], args[1], args[2])
            err = "\n".join(err)
            if args[0] is ErrorHTTP: # args[0] is class of ecx
                if args[1].response.status_code == 401:
                    tk.messagebox.showerror("Disconnected", "You are not connected.")
                    self.openConnectionDialog(force=True)
                    return
            dialog = ChildDialogException(self, 'Exception occured', err)
            apiclient = APIClient.getInstance()
            apiclient.reportError(err)
            try:
                self.wait_window(dialog.app)
            except tk.TclError:
                sys.exit(1)
        except Exception as e:
            print("Exception in error handler "+str(e))
            sys.exit(1)

    def promptForConnection(self):
        """Close current database connection and open connection form for the user
        
        Returns: 
            The number of pollenisator database found, 0 if the connection failed."""
        apiclient = APIClient.getInstance()
        apiclient.reinitConnection()
        connectDialog = ChildDialogConnect(self)
        self.wait_window(connectDialog.app)
        return connectDialog.rvalue

    def changeMyPassword(self):
        """Allows the current user to change its password"""
        apiclient = APIClient.getInstance()
        connected_user = apiclient.getUser()
        if connected_user is None:
            tk.messagebox.showerror("Change password", "You are not connected")
            return 
        dialog = ChildDialogEditPassword(self, connected_user)
        self.wait_window(dialog.app)
        
    def disconnect(self):
        """Remove the session cookie"""
        APIClient.getInstance().disconnect()
        
        self.openConnectionDialog(force=True)

    def submitIssue(self):
        """Open git issues in browser"""
        import webbrowser
        webbrowser.open_new_tab("https://github.com/AlgoSecure/Pollenisator/issues")

    def handleNotif(self, notification):
        self.datamanager.handleNotification(notification)
        

   

    def onClosing(self):
        """
        Close the application properly.
        """
        apiclient = APIClient.getInstance()
        apiclient.dettach(self)
        print("Stopping application...")
        if self.sio is not None:
            self.sio.disconnect()
            self.sio.eio.disconnect()
        if self.scanManager is not None:
            self.scanManager.onClosing()
        for module in self.modules:
            if callable(getattr(module["object"], "onClosing", None)):
                module["object"].onClosing()
        self.quit()

    def _initMenuBar(self):
        """
        Create the bar menu on top of the screen.
        """
        menubar = utils.craftMenuWithStyle(self)
        self.configure(menu=menubar)

        self.bind('<F5>', self.refreshView)
        self.bind('<Control-o>', self.openPentestsWindow)
        fileMenu =  utils.craftMenuWithStyle(menubar)
        fileMenu.add_command(label="Pentests management (Ctrl+o)",
                             command=self.openPentestsWindow)
        fileMenu.add_command(label="Connect to server", command=self.promptForConnection)
        
        fileMenu.add_command(label="Export commands",
                             command=self.exportCommands)
        fileMenu.add_command(label="Import commands",
                             command=self.importCommands)
        fileMenu.add_command(label="Export cheatsheet",
                             command=self.exportCheatsheet)
        fileMenu.add_command(label="Import cheatsheet",
                             command=self.importCheatsheet)
        fileMenu.add_command(label="Import defect templates",
                             command=self.importDefectTemplates)                     

        fileMenu.add_command(label="Exit", command=self.onExit)
        fileMenu2 = utils.craftMenuWithStyle(menubar)
        fileMenu2.add_command(label="Import existing tools results ...",
                              command=self.importExistingTools)
        fileMenu2.add_command(label="Reset unfinished tools",
                              command=self.resetUnfinishedTools)
        fileMenu2.add_command(label="Test local tools",
                              command=self.testLocalTools)
        fileMenu2.add_command(label="Refresh (F5)",
                              command=self.refreshView)
        fileMenuUser = utils.craftMenuWithStyle(menubar)
        fileMenuUser.add_command(label="Change your password",
                              command=self.changeMyPassword)
        fileMenuUser.add_command(label="Disconnect", command=self.disconnect)
        fileMenu3 = utils.craftMenuWithStyle(menubar)
        fileMenu3.add_command(label="Submit a bug or feature",
                              command=self.submitIssue)
        fileMenuDebug = utils.craftMenuWithStyle(menubar)
        fileMenuDebug.add_command(label="Socket test", command=self.socketTest)
        menubar.add_cascade(label="Database", menu=fileMenu)
        menubar.add_cascade(label="Scans", menu=fileMenu2)
        menubar.add_command(label="Scripts...", command=self.openScriptModule)
        menubar.add_cascade(label="User", menu=fileMenuUser)
        menubar.add_cascade(label="Help", menu=fileMenu3)
        menubar.add_cascade(label="Debug", menu=fileMenuDebug)
        
    def socketTest(self):
        print("EMIT TEST")
        self.sio.emit("test", {"pentest": APIClient.getInstance().getCurrentPentest()})
        print("TEST SENT, WAITING FOR RESPONSE")

    def initMainView(self):
        """
        Fill the main view tab menu
        """
        self.mainPageFrame = CTkFrame(self.nbk)
        searchFrame = CTkFrame(self.mainPageFrame, fg_color=utils.getBackgroundSecondColor())
        filterbar_frame = CTkFrame(searchFrame, fg_color="transparent")
        self.image_filter = CTkImage(Image.open(utils.getIcon("filter.png")))
        lblSearch = CTkLabel(filterbar_frame, text="Filter bar:", image=self.image_filter, compound = "left")
        lblSearch.pack(side="left", fill=tk.NONE)
        self.searchBar = AutocompleteEntry(self.settings, filterbar_frame)
        #self.searchBar = CTkEntry(filterbar_frame, width=108)
        self.searchBar.bind('<Return>', self.newSearch)
        self.searchBar.bind('<KP_Enter>', self.newSearch)
        self.searchBar.bind('<Control-a>', self.searchbarSelectAll)
        # searchBar.bind("<Button-3>", self.do_popup)
        self.searchBar.pack(side="left", fill="x", expand=True)
        self.quickSearchVal = tk.BooleanVar()
        self.quickSearchVal.set(self.settings.local_settings.get("quicksearch", False))
        
        checkbox_quick_search = CTkSwitch(filterbar_frame, text="Quick search", variable=self.quickSearchVal, command=self.quickSearchChanged)
        checkbox_quick_search.pack(side="left", padx=5)
        self.keep_parents_val = tk.BooleanVar()
        self.keep_parents_val.set(self.settings.local_settings.get("keep_parents", True))
        checkbox_keep_parent = CTkSwitch(filterbar_frame, text="Keep parents", variable=self.keep_parents_val, command=self.keepParentsChanged)
        checkbox_keep_parent.pack(side="left", padx=5)
        self.search_icon = tk.PhotoImage(file=utils.getIcon("search.png"))
        btnSearchBar = ttk.Button(filterbar_frame, text="", image=self.search_icon, style="iconbis.TButton", tooltip="Filter elements based of complex query or only text if quicksearch is selected", width=10, command=self.newSearch)
        btnSearchBar.pack(side="left", fill="x")
        image=Image.open(utils.getIcon("reset.png"))
        img=image.resize((16, 16))
        self.reset_icon = ImageTk.PhotoImage(img)
        btnReset = ttk.Button(filterbar_frame, image=self.reset_icon, text="",  style="iconbis.TButton", tooltip="Reset search bar filter", width=10, command=self.resetButtonClicked)
        btnReset.pack(side="left", fill="x")
        self.photo = CTkImage(Image.open(utils.getHelpIconPath()))
        self.helpFrame = None
        self.btnHelp = CTkButton(filterbar_frame, text="",image=self.photo,  fg_color="transparent", width=10, command=self.showSearchHelp)

        self.btnHelp.pack(side="left")
        filterbar_frame.pack(side=tk.TOP,fill=tk.X)
        self.statusbar = StatusBar(searchFrame, self)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        searchFrame.pack(side="top", fill="x")
        #PANED PART
        self.paned = tk.PanedWindow(self.mainPageFrame, orient="horizontal")
        #RIGHT PANE : Canvas + frame
        self.proxyFrameMain = CTkFrame(self.paned)
        self.viewframe = ScrollableFrameXPlateform(self.proxyFrameMain)
        #LEFT PANE : Treeview
        self.left_pane = CTkFrame(self.paned)
        self.frameTw = CTkFrame(self.left_pane)
        self.frameTw.rowconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        self.frameTw.columnconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        
        self.treevw = PentestTreeview(self, self.frameTw)
        self.treevw.initUI()
        self.scbVSel = CTkScrollbar(self.frameTw,
                                orientation=tk.VERTICAL,
                                command=self.treevw.yview)
        self.treevw.configure(yscrollcommand=self.scbVSel.set)
        self.treevw.grid(row=0, column=0, sticky=tk.NSEW)
        self.scbVSel.grid(row=0, column=1, sticky=tk.NS)
        # FILTER PANE:
        # self.filtersFrame = CTkFrame(self.left_pane)
        # self.initFiltersFrame(self.filtersFrame)
        # self.filtersFrame.pack(side="bottom", fill="x")
        # END PANE PREP
        self.frameTw.pack(side="top", fill=tk.BOTH, expand=True)
        
        self.left_pane.pack(side="left", fill=tk.BOTH, expand=True)
        self.paned.add(self.left_pane)
        self.proxyFrameMain.pack(side="left")
        self.viewframe.pack(side="left", expand=1, fill=tk.BOTH)
        self.paned.add(self.proxyFrameMain)
        self.paned.pack(fill=tk.BOTH, expand=1)
        self.mainPageFrame.pack(fill="both", expand=True)
        self.nbk.add(self.mainPageFrame, "Main View", order=Module.HIGH_PRIORITY, image=self.main_tab_img)

    def searchbarSelectAll(self, _event):
        """
        Callback to select all the text in searchbar
        Args:
            _event: not used but mandatory
        """
        self.searchBar.select_range(0, 'end')
        self.searchBar.icursor('end')
        return "break"

   

   


    def initCommandsView(self):
        """Populate the command tab menu view frame with cool widgets"""
        self.commandsPageFrame = CTkFrame(self.nbk)
        self.commandPaned = tk.PanedWindow(self.commandsPageFrame, height=800)
        self.commandsFrameTw = CTkFrame(self.commandPaned)
        self.proxyFrameCommand = CTkFrame(self.commandPaned)
        self.commandsFrameTw.pack(expand=True)
        self.commandsViewFrame = ScrollableFrameXPlateform(self.proxyFrameCommand)
        self.commandsTreevw = CommandsTreeview(self, self.commandsFrameTw)
        scbVSel = CTkScrollbar(self.commandsFrameTw,
                                orientation=tk.VERTICAL,
                                command=self.commandsTreevw.yview)
        self.commandsTreevw.configure(yscrollcommand=scbVSel.set)
        self.commandsTreevw.grid(row=0, column=0, sticky=tk.NSEW)
        scbVSel.grid(row=0, column=1, sticky=tk.NS)
        self.commandPaned.add(self.commandsFrameTw)
        self.commandsViewFrame.pack(fill=tk.BOTH, expand=1)
        self.commandPaned.add(self.proxyFrameCommand)
        self.commandPaned.pack(fill=tk.BOTH, expand=1)
        self.commandsFrameTw.rowconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        self.commandsFrameTw.columnconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        self.nbk.add(self.commandsPageFrame, "Commands", order=Module.LOW_PRIORITY, image=self.commands_tab_img)


    def showSearchHelp(self, _event=None):
        """Called when the searchbar help button is clicked. Display a floating help window with examples
        Args:
            _event: not used but mandatory
        """
        if self.helpFrame is None:
            x, y = self.btnHelp.winfo_rootx(), self.btnHelp.winfo_rooty()
            self.helpFrame = FloatingHelpWindow(410, 400, x-380, y+40, self)
        else:
            self.helpFrame.destroy()
            self.helpFrame = None

    def beforeTabSwitch(self, current, new):
        if current is None:
            return
        for module in self.modules:
            if current.strip().lower() == module["name"].strip().lower():
                if hasattr(module["object"], "close"):
                    module["object"].close()

    def tabSwitch(self, tabName):
        """Called when the user click on the tab menu to switch tab. Add a behaviour before the tab switches.
        Args:
            tabName: the opened tab
        """
        apiclient = APIClient.getInstance()
        self.searchBar.quit()
        if tabName == "Main View":
            self.refreshUI()
        if tabName == "Commands":
            self.commandsTreevw.initUI()
        if apiclient.getCurrentPentest() is None or apiclient.getCurrentPentest() == "":
            opened = self.openPentestsWindow()
            if opened is None:
                return
        if tabName == "Scan":
            if apiclient.getCurrentPentest() != "":
                self.scanManager.refreshUI()
        elif tabName == "Settings":
            self.settings.reloadUI()
        elif tabName == "Admin":
            self.admin.refreshUI()
        else:
            for module in self.modules:
                if tabName.strip().lower() == module["name"].strip().lower():
                    module["object"].open()

    def initSettingsView(self):
        """Add the settings view frame to the notebook widget and initialize its UI."""
        self.settingViewFrame = CTkFrame(self.nbk)
        self.settings.initUI(self.settingViewFrame)
        self.nbk.add(self.settingViewFrame, "Settings", order=Module.LAST_PRIORITY, image=self.settings_tab_img)

    def initScanView(self):
        """Add the scan view frame to the notebook widget. This does not initialize it as it needs a database to be opened."""
        self.scanViewFrame = CTkFrame(self.nbk)
        self.scanManager.initUI(self.scanViewFrame)
        self.nbk.add(self.scanViewFrame, "Scan", order=Module.HIGH_PRIORITY, image=self.scan_tab_img)

    def initAdminView(self):
        """Add the admin button to the notebook"""
        self.admin = AdminView(self.nbk)
        self.adminViewFrame = CTkFrame(self.nbk)
        self.admin.initUI(self.adminViewFrame)
        self.nbk.add(self.adminViewFrame, "Admin", order=Module.LOW_PRIORITY, image=self.admin_tab_img)

    def openScriptModule(self):
        """Open the script window"""
        self.scriptManager = ScriptManager(self)

    def initUI(self):
        """
        initialize all the main windows objects. (Bar Menu, contextual menu, treeview, editing pane)
        """
        if self.nbk is not None:
            self.refreshUI()
            return
        self.nbk = ButtonNotebook(self, self.tabSwitch, self.beforeTabSwitch)
        

        
        self.initMainView()
        self.initAdminView()
        self.initCommandsView()
        self.initScanView()
        self.initSettingsView()
        for module in self.modules:
            module["view"] = CTkFrame(self.nbk)
            module["object"].initUI(module["view"], self.nbk, self.treevw, tkApp=self)
        for module in self.modules:
            self.nbk.add(module["view"], module["name"].strip(), order=module["object"].__class__.order_priority, image=module["img"])

        
        self._initMenuBar()
        self.nbk.pack(fill=tk.BOTH, expand=1)

    def refreshUI(self):
        for widget in self.viewframe.winfo_children():
            widget.destroy()
        self.left_pane.update()
        self.after(50, lambda: self.paned.paneconfigure(self.left_pane, height=self.left_pane.winfo_reqheight()))
        self.treevw.refresh()
        self.treevw.filter_empty_nodes()
        self.statusbar.refreshTags(Settings.getTags(ignoreCache=True))
        # self.nbk.select("Main View")

    def quickSearchChanged(self, event=None):
        """Called when the quick search bar is modified. Change settings
        Args:
            event: not used but mandatory
        """
        self.settings.local_settings["quicksearch"] = int(self.quickSearchVal.get())
        self.settings.saveLocalSettings()

    def keepParentsChanged(self, event=None):
        """Called when the keep parent switch is modified. Change settings
        Args:
            event: not used but mandatory
        """
        self.settings.local_settings["keep_parents"] = int(self.keep_parents_val.get())
        self.settings.saveLocalSettings()
    
    def newSearch(self, _event=None, histo=True, quick_search_allowed=True):
        """Called when the searchbar is validated (click on search button or enter key pressed).
        Perform a filter on the main treeview.
        Args:
            _event: not used but mandatory"""
        filterStr = self.searchBar.get()
        if filterStr.strip() == "":
            self.resetButtonClicked()
            return
        self.settings.reloadSettings()
        success = self.treevw.filterTreeview(filterStr, self.settings, quick_search_allowed)
        self.searchMode = (success and filterStr.strip() != "")
        if success:
            if histo:
                histo_filters = self.settings.local_settings.get("histo_filters", [])
                if filterStr.strip() != "":
                    histo_filters.insert(0, filterStr)
                    if len(histo_filters) > 10:
                        histo_filters = histo_filters[:10]
                    self.settings.local_settings["histo_filters"] = histo_filters
                    self.settings.saveLocalSettings()
            if self.helpFrame is not None:
                self.helpFrame.destroy()
                self.helpFrame = None

    def statusbarClicked(self, name):
        """Called when a button in the statusbar tag is clicked.
        filter the treeview to match the status bar tag clicked and enforce select of main view
        Args:
            name: not used but mandatory"""
        # get the index of the mouse click
        import cProfile
        profiler = cProfile.Profile()
        profiler.enable()
        self.nbk.select("Main View")
        self.search("\""+name+"\" in tags")
        profiler.disable()
        profiler.dump_stats("profiles.stats")

    def search(self, filter_str):
        self.searchMode = True
        self.searchBar.delete(0, tk.END)
        self.searchBar.insert(tk.END, filter_str)
        self.newSearch(histo=False, quick_search_allowed=False)

    def resetButtonClicked(self):
        """
        Called when the reset button of the status bar is clicked.
        """
        self.searchMode = False
        self.searchBar.reset()
        self.treevw.unfilterAll()

    def refreshView(self, _event=None):
        """
        Reload the currently opened tab
        Args:
            _event: not used but mandatory
        """
        print(f"REFRESH VIEW ")
        setViewOn = None
        nbkOpenedTab = self.nbk.getOpenTabName()
        activeTw = None
        if nbkOpenedTab == "Main View":
            activeTw = self.treevw
        elif nbkOpenedTab == "Commands":
            activeTw = self.commandsTreevw
        elif nbkOpenedTab == "Scan":
            self.scanManager.initUI(self.scanViewFrame)
        elif nbkOpenedTab == "Settings":
            self.settings.reloadUI()
        else:
            for module in self.modules:
                if nbkOpenedTab.strip().lower() == module["name"].strip().lower():
                    print(f"REFRESH VIEW Opening module {module['name']}")
                    module["object"].open()
        if activeTw is not None:
            if len(activeTw.selection()) == 1:
                setViewOn = activeTw.selection()[0]
            activeTw.refresh(force=True)
            activeTw.filter_empty_nodes()
        if setViewOn is not None:
            try:
                activeTw.see(setViewOn)
                activeTw.focus(setViewOn)
                activeTw.selection_set(setViewOn)
                activeTw.openModifyWindowOf(setViewOn)
            except tk.TclError:
                pass

    def resetUnfinishedTools(self):
        """
        Reset all running tools to a ready state.
        """
        apiclient = APIClient.getInstance()
        if apiclient.getCurrentPentest() != "":
            utils.resetUnfinishedTools()
            self.treevw.load()

    def testLocalTools(self):
        """ test local binary path with which"""
        datamanager = DataManager.getInstance()
        apiclient = APIClient.getInstance()
        self.settings._reloadLocalSettings()
        commands = datamanager.find("commands", {"owners":apiclient.getUser()})
        for command in commands:
            bin_path = self.settings.local_settings.get("my_commands", {}).get(command["name"])
            if bin_path is None:
                tk.messagebox.showerror("Missing a binary path", f"The local settings for {command['name']} is not set. Missing local binary path.")
                return False
            if not utils.which_expand_alias(bin_path):
                tk.messagebox.showerror("Invalid binary path", f"The local settings for {command['name']} is not recognized. ({bin_path}).")
        tk.messagebox.showinfo("Test local tools success", "All binary path exists")
        return True
    

    def exportCommands(self):
        """
        Dump pollenisator from database to an archive file gunzip.
        """
        dialog = ChildDialogQuestion(self, "Ask question", "Do you want to export your commands or Worker's commands.", ["My commands", "Worker"])
        self.wait_window(dialog.app)
        apiclient = APIClient.getInstance()
        res, msg = apiclient.exportCommands(self)
        if res:
            tkinter.messagebox.showinfo(
                "Export pollenisator database", "Export completed in "+str(msg))
        else:
            tkinter.messagebox.showinfo(msg)
    
    def exportCheatsheet(self):
        """
        Dump pollenisator from database to an archive file gunzip.
        """
        apiclient = APIClient.getInstance()
        res, msg = apiclient.exportCheatsheet(self)
        if res:
            tkinter.messagebox.showinfo(
                "Export cheatsheet database", "Export completed in "+str(msg))
        else:
            tkinter.messagebox.showinfo(msg)

   

    def findUnscannedPorts(self):
        ports = Port.fetchObjects({})
        datamanager = DataManager.getInstance()
        for port in ports:
            port_key = port.getDbKey()
            res = datamanager.find("tools", port_key, multi=False)
            if res is None:
                port.setTags(["unscanned"])

    def importCommands(self, name=None):
        """
        Import a pollenisator archive file gunzip to database.
        Args:
            name: The filename of the gunzip command table exported previously
        Returns:
            None if name is None and filedialog is closed
            True if commands successfully are imported
            False otherwise.
        """
        filename = ""
        if name is None:
            f = tkinter.filedialog.askopenfilename(self, defaultextension=".json")
            if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
                return
            filename = str(f)
        else:
            filename = name
        try:
            dialog = ChildDialogQuestion(self, "Ask question", "Do you want to import these commands for you or the worker.", ["Me", "Worker"])
            self.wait_window(dialog.app)
            apiclient = APIClient.getInstance()
            success = apiclient.importCommands(filename, forWorker=dialog.rvalue == "Worker")
            self.commandsTreevw.refresh()
        except IOError:
            tkinter.messagebox.showerror(
                "Import commands", "Import failed. "+str(filename)+" was not found or is not a file.")
            return False
        if not success:
            tkinter.messagebox.showerror("Command import", "Command import failed")
        else:
            tkinter.messagebox.showinfo("Command import", "Command import completed")
        return success

    def importCheatsheet(self, name=None):
        """
        Import a pollenisator cheatsheet file json to database.
        Args:
            name: The filename of the json command table exported previously
        Returns:
            None if name is None and filedialog is closed
            True if commands successfully are imported
            False otherwise.
        """
        filename = ""
        if name is None:
            f = tkinter.filedialog.askopenfilename(self, defaultextension=".json")
            if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
                return
            filename = str(f)
        else:
            filename = name
        try:
            apiclient = APIClient.getInstance()
            success = apiclient.importCheatsheet(filename)
        except IOError:
            tkinter.messagebox.showerror(
                "Import Cheatsheet", "Import failed. "+str(filename)+" was not found or is not a file.")
            return False
        if not success:
            tkinter.messagebox.showerror("Cheatsheet import", "Cheatsheet import failed")
        else:
            tkinter.messagebox.showinfo("Cheatsheet import", "Cheatsheet import completed")
        return success

    def importDefectTemplates(self, name=None):
        """
        Import defect templates from a json
        Args:
            name: The filename of the json containing defect templates
        Returns:
            None if name is None and filedialog is closed
            True if defects successfully are imported
            False otherwise.
        """
        filename = ""
        if name is None:
            f = tkinter.filedialog.askopenfilename(self, defaultextension=".json")
            if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
                return
            filename = str(f)
        else:
            filename = name
        try:
            apiclient = APIClient.getInstance()
            success = apiclient.importDefectTemplates(filename)
        except IOError:
            tkinter.messagebox.showerror(
                "Import defects templates", "Import failed. "+str(filename)+" was not found or is not a file.")
            return False
        if not success:
            tkinter.messagebox.showerror("Defects templates import", "Defects templatest failed")
        else:
            tkinter.messagebox.showinfo("Defects templates import", "Defects templates completed")
        return success

    def onExit(self):
        """
        Exit the application
        """
        self.onClosing()

    def openPentestsWindow(self, _event=None):
        """
        Open Pentest dialog window
        Args:
            _event: Not used but mandatory
        Returns:
            None if no database were selected
            datababase name otherwise
        """
        dialog = ChildDialogPentests(None)
        try:
            dialog.wait_window()
        except tk.TclError:
            pass
        if dialog.rvalue is not None:
            self.openPentest(dialog.rvalue)
        return dialog.rvalue

       

    

    def newPentest(self, pentestName, pentest_type, start_date, end_date, scope, settings, pentesters):
        """
        Register the given pentest name into database and opens it.

        Args:
            pentestName: The pentest database name to register in database.
        """
        succeed = False
        if pentestName is not None:
            apiclient = APIClient.getInstance()
            succeed, msg = apiclient.registerPentest(pentestName, pentest_type, start_date, end_date, scope, settings, pentesters)
            if not succeed:
                tkinter.messagebox.showinfo("Forbidden", msg)
        return succeed

    
    def openPentest(self, filename=""):
        """
        Open the given database name. Loads it in treeview.

        Args:
            filename: the pentest database name to load in application. If "" is given (default), will refresh the already opened database if there is one.
        """
        pentestName = None
        apiclient = APIClient.getInstance()

        if filename == "" and apiclient.getCurrentPentest() != "":
            pentestName = apiclient.getCurrentPentest()
        elif filename != "":
            pentestName = filename.split(".")[0].split("/")[-1]
        if pentestName is not None:
            first_use_detected = self.detectFirstUse()
            res = apiclient.setCurrentPentest(pentestName, first_use_detected)
            if not res:
                tk.messagebox.showerror("Connection failed", "Could not connect to "+str(pentestName))
                return
            DataManager.getInstance().load()
            self.initUI()
            self.statusbar.refreshTags(Settings.getTags(ignoreCache=True))
            self.sio.emit("registerForNotifications", {"token":apiclient.getToken(), "pentest":pentestName})
            self.settings.reloadSettings()
            self.refresh_tabs()
            
            self.nbk.select("Dashboard")

    def refresh_tabs(self):
        apiclient = APIClient.getInstance()
        if apiclient.isAdmin():
            self.nbk.add(self.adminViewFrame, "Admin", order=Module.LAST_PRIORITY, image=self.admin_tab_img)
        else:
            self.nbk.delete("Admin")
        pentest_type = self.settings.getPentestType()
        for module in self.modules:
            pentest_type_allowed = pentest_type.lower() in module["object"].__class__.pentest_types
            all_are_authorized = "all" in module["object"].__class__.pentest_types
            module_need_admin = module["object"].__class__.need_admin
            is_admin = apiclient.isAdmin()
            if (pentest_type_allowed or all_are_authorized) and (is_admin or not module_need_admin):
                self.nbk.add(module["view"], module["name"].strip(), order=module["object"].__class__.order_priority, image=module["img"])
            else:    
                self.nbk.delete(module["name"])

   
    def importExistingTools(self, _event=None):
        """
        Ask user to import existing files to import.
        """
        dialog = ChildDialogFileParser(self)
        self.wait_window(dialog.app)

    def detectFirstUse(self):
        detector = os.path.join(utils.getConfigFolder(),".first_use")
        if os.path.exists(detector):
            return False
        with open(detector, mode="w") as f:
            f.write("")
        return True
