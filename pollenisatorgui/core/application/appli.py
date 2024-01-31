"""
Pollenisator client GUI window.
"""
import threading
import traceback
import tkinter.filedialog
import tkinter as tk
import tkinter.messagebox
import tkinter.simpledialog
import tkinter.ttk as ttk
import uuid
from customtkinter import *
import sys
import os
from tkinter import TclError
import json
import re
from PIL import ImageTk, Image
import importlib
import pkgutil
import socketio
from pollenisatorgui.core.application.dialogs.ChildDialogToolsInstalled import ChildDialogToolsInstalled
from pollenisatorgui.core.application.scrollableframexplateform import ScrollableFrameXPlateform
from pollenisatorgui.core.application.terminalswidget import TerminalsWidget
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.components.tag import TagInfos
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
from pollenisatorgui.core.controllers.toolcontroller import ToolController
from pollenisatorgui.core.forms.formpanel import FormPanel
from pollenisatorgui.core.models.port import Port
from pollenisatorgui.core.views.checkinstanceview import CheckInstanceView
from pollenisatorgui.core.views.checkitemview import CheckItemView
from pollenisatorgui.core.views.ipview import IpView
import pollenisatorgui.modules
import customtkinter
import tkinterDnD
from ttkwidgets import tooltips
from pollenisatorgui.core.application.pollenisatorentry import PopoEntry
from pollenisatorgui.core.components.logger_config import logger
from pollenisatorgui.modules.module import Module

class FloatingHelpWindow(CTkToplevel):
    """floating basic window with helping text inside
    Inherit tkinter TopLevel
    Found on the internet (stackoverflow) but did not keep link sorry...
    """

    def __init__(self, w, h, posx, posy, *args, **kwargs):
        CTkToplevel.__init__(self, *args, **kwargs)
        self.attributes("-type", "dialog")
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

    def stopMove(self, _event=None):
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


class AutocompleteEntry(PopoEntry):
    """Inherit PopoEntry.
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
        PopoEntry.__init__(self, *args, **kwargs)
        self.width = kwargs.get("width",100)
        self.lista = set()
        self.var = self.cget("textvariable")
        if self.var is None:
            self.var = tk.StringVar()
            self.configure(textvariable=self.var)
        self.var.trace('w', self.changed)
        self.bind("<Tab>", self.selection)
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

    def selection(self, _event=None):
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
            self.focus_set()
            self.focus()
            #self.changed()
            return 'break'

    def upArrow(self, _event=None):
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

    def downArrow(self, _event=None):
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
        self.frameButtons = CTkFrame(self, fg_color=utils.getStrongColor())
        self.callbackSwitch = callbackSwitch
        self.closeCallbackSwitch = closeCallbackSwitch
        self.tabs = {}
        self.current = None
        self.frameButtons.pack(side="left", anchor="nw", fill=tk.Y)
        self.btns = {}
        self.lbl = None

    def add(self, widget, name, order, image):
        if name not in self.tabs:
            self.tabs[name] = {"widget":widget, "image":image, "order": order, "name":name}
            widget.pack_forget()
            btn = CTkButton(self.frameButtons, text=name, image=image,  fg_color=utils.getStrongColor() , hover_color=utils.getStrongActiveColor(), compound=tk.TOP)
            self.btns[name] = btn
            btn.bind("<Button-1>", self.clicked)
            self.redraw()
            

    def redraw(self):
        for btn in self.btns.values():
            btn.pack_forget()
        if self.lbl:
            self.lbl.pack_forget()
        btns = sorted(self.tabs.values(), key=lambda x:x["order"])
        for btn in btns:
            
            self.btns[btn["name"]].pack(side="top", fill=tk.X, anchor="nw")
        self.image = Image.open(utils.getIcon("LogoPollenisator.png"))
        img = CTkImage(light_image=self.image, dark_image=self.image, size=(100, 123))
        self.lbl = CTkLabel(self.frameButtons, text="", image=img)
        self.lbl.pack(side="bottom", fill=tk.X, pady=5,anchor="sw")

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
            self.btns[self.current].configure(fg_color=utils.getStrongColor())

            self.closeCallbackSwitch(self.current, name)
        self.current = name
        self.btns[name].configure(fg_color=utils.getStrongActiveColor())
        self.tabs[name]["widget"].pack(side="right", expand=True, anchor="center", fill=tk.BOTH)
        self.callbackSwitch(name)


class Appli(customtkinter.CTk, tkinterDnD.tk.DnDWrapper):#HACK to make work tkdnd with CTk
    """
    Main tkinter graphical application object.
    """
    version_compatible = "2.7.*"

    
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
        self.notif_handlers = []
        self.sio = None #socketio client
        self.initialized = False
        self.settings = Settings()
        self.notif_processing_timer = None

        utils.setStyle(self, self.settings.local_settings.get("dark_mode", False))
        self.main_tab_img = CTkImage(
            Image.open(utils.getIcon("tab_main.png")), size=(30, 30))
        self.commands_tab_img = CTkImage(
            Image.open(utils.getIcon("tab_commands.png")), size=(30, 30))
        self.scan_tab_img = CTkImage(
            Image.open(utils.getIcon("tab_scan.png")), size=(30, 30))
        self.settings_tab_img = CTkImage(
            Image.open(utils.getIcon("tab_settings.png")), size=(30, 30))
        self.admin_tab_img = CTkImage(
            Image.open(utils.getIcon("tab_admin.png")), size=(30, 30))
        # HISTORY : Main view and command where historically in the same view;
        # This results in lots of widget here with a confusing naming style
        #### core components (Tab menu on the left objects)####
        #### MAIN VIEW ####
        self.mainPageFrame = None
        self.paned = None
        self.proxyFrameMain = None
        self.viewframe = None
        self.frameTw = None
        self.treevw = None
        self.datamanager = None
        self.terminals = None
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
        dir_path = utils.getIcon("favicon.png")
        img = tk.PhotoImage(file=dir_path)
        self.resizable(True, True)
        self.iconphoto(True, img)
        self.minsize(width=400, height=400)
        self.resizable(True, True)
        self.title("Pollenisator")
        monitor = utils.get_screen_where_widget(self)
        self.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
        self.protocol("WM_DELETE_WINDOW", self.onClosing)
        self.datamanager = DataManager.getInstance()
        self.initModules()
        apiclient = APIClient.getInstance()
        self.topviewframe = None
        self.scanManager = ScanManager(self, self.nbk, self.treevw, apiclient.getCurrentPentest(), self.settings)
        apiclient.appli = self
        opened, errored = self.openConnectionDialog()
        if errored:
            return
        if not opened:
            try:
                self.wait_visibility(self.tk)
            except tk.TclError: #closed dialog
                return
            except AttributeError:  # closed and destroyed
                return
            opened, errored = self.openConnectionDialog(force=True)
            if errored:
                return
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
                self.forceUpdate(srv_version, Appli.version_compatible)
                self.onClosing()
                return False, True
            if int(Appli.version_compatible.split(".")[1]) != int(srv_version.split(".")[1]):
                self.forceUpdate(srv_version, Appli.version_compatible)
                self.onClosing()
                return False, True
            if self.sio is not None:
                self.sio.disconnect()
            self.sio = socketio.Client()
            @self.sio.event
            def notif(data):
                self.handleNotif(data)
            
            @self.sio.event
            def test(data):
                tk.messagebox.showinfo("test", "test socket working received data : "+str(data))
           # Event handler for client disconnection
            @self.sio.event
            def disconnect():
                logger.debug(f"Client disconnected")
                t = threading.Timer(0.5, self.reconnect)
                t.start()
                return True
            try:
                self.sio.connect(apiclient.api_url)
            except RuntimeError:
                # tryto reconnect
                self.sio.connect(apiclient.api_url)
            pentests = apiclient.getPentestList()
            self._initMenuBar()

            if pentests is None:
                pentests = []
            else:
                pentests_names = [x["nom"] for x in pentests][::-1]
            if apiclient.getCurrentPentest() != "" and apiclient.getCurrentPentest() in pentests_names:
                self.openPentest(apiclient.getCurrentPentest())
            else:
                ret = self.openPentestsWindow(pentests=pentests)
                if ret is None:
                    pass
                    # self.onClosing()
                    # try:
                    #     self.destroy()
                    # except tk.TclError:
                    #     pass   
                    # return False, False
            self.initialized = True

        else:
            self.onClosing()
            try:
                self.destroy()
            except tk.TclError:
                pass
        return apiclient.isConnected(), False
    
    def reconnect(self):
        apiclient = APIClient.getInstance()
        if not apiclient.isConnected() or self.quitting:
            return
        logger.debug("SocketIO reconnection quiitng="+str(self.quitting))
        try:
            self.sio.connect(apiclient.api_url)
        except ConnectionError:
            logger.debug("SocketIO reconnection failed")
            t = threading.Timer(0.5, self.reconnect)
            t.start()
            return
        self.sio.emit("registerForNotifications", {"token":apiclient.getToken(), "pentest":apiclient.getCurrentPentest()})

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
                module_obj = module_class(self, self.settings, self)
                self.modules.append({"name": module_obj.tabName, "object":module_obj, "view":None, "img":CTkImage(Image.open(utils.getIcon(module_obj.iconName)), size=(30, 30))})
        
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
            if self.quitting:
                return
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

    def notify(self, notification):
        for notif_handler in self.notif_handlers:
            if notif_handler["pentest"] is not None and notif_handler["pentest"] != notification["db"]:
                continue
            if notif_handler["collection"] is not None and notif_handler["collection"] != notification["collection"]:
                continue
            if notif_handler["iid"] is not None and notif_handler["iid"] != str(notification["iid"]):
                continue
            if notif_handler["notif_name"] is not None and notif_handler["notif_name"] != notification["action"]:
                continue
            
            notif_handler["handler"](notification)
    
    def subscribe_notification(self, notif_name, handler, pentest=None, collection=None, iid=None):
        if handler is None:
            return
        self.notif_handlers.append({"pentest":pentest, "collection":collection, "iid":iid, "notif_name":notif_name, "handler":handler})
    
    def unsubscribe_notification(self, notif_name, pentest=None, collection=None, iid=None):
        i = 0
        while self.notif_handlers and i < len(self.notif_handlers):
            notif_handler = self.notif_handlers[i]
            if notif_handler["pentest"] == pentest and notif_handler["notif_name"] == notif_name \
                and notif_handler["collection"] == collection and str(notif_handler["iid"]) == str(iid): 
                del self.notif_handlers[i]
            else:
                i+=1

    def handleNotif(self, notification):
        notification = json.loads(notification, cls=utils.JSONDecoder)
        self.notify(notification)
        self.datamanager.handleNotification(notification)
        # self.notif_waiting.append(notification)
        # if self.notif_processing_timer is None and not self.quitting:
        #     self.notif_processing_timer = threading.Timer(1, self.notif_processing)
        #     self.notif_processing_timer.start()


    # def notif_processing(self):
    #     notif_treatments = deepcopy(self.notif_waiting)
    #     self.notif_waiting = []
    #     notif_treatments.sort(key=lambda x: x["time"])
    #     while notif_treatments:
    #         notification = notif_treatments.pop(0)
    #         self.datamanager.handleNotification(notification)
    #         self.notify(notification)
    #     self.notif_processing_timer = None
        
    def onClosing(self):
        """
        Close the application properly.
        """
        if self.quitting:
            return
        self.quitting = True
        self.closePentest()
        print("Stopping application...")
        if self.sio is not None:
            self.sio.disconnect()
            self.sio.eio.disconnect()
        self.quit()

    def reopen(self, event=None):
        self.treevw.reopen()

    def _initMenuBar(self):
        """
        Create the bar menu on top of the screen.
        """
        menubar = utils.craftMenuWithStyle(self)
        self.configure(menu=menubar)

        self.bind('<F5>', self.refreshView)
        self.bind('<F6>', self.reopen)
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

        fileMenu.add_command(label="Exit", command=self.onClosing)
        fileMenu2 = utils.craftMenuWithStyle(menubar)
        fileMenu2.add_command(label="Import existing tools results ...",
                              command=self.importExistingTools)
        fileMenu2.add_command(label="Reset unfinished tools",
                              command=self.resetUnfinishedTools)
        fileMenu2.add_command(label="Test local tools",
                              command=self.wrapperTestLocalTools)
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
        self.mainPageFrame = CTkFrame(self.topviewframe)
        searchFrame = CTkFrame(self.mainPageFrame, fg_color=utils.getBackgroundSecondColor())
        filterbar_frame = CTkFrame(searchFrame, fg_color="transparent")
        self.image_filter = CTkImage(Image.open(utils.getIcon("filter.png")))
        lblSearch = CTkLabel(filterbar_frame, text="Filter bar", image=self.image_filter, compound = "left")
        lblSearch.pack(side="left", fill=tk.NONE)
        self.searchBar = AutocompleteEntry(self.settings, filterbar_frame)
        #self.searchBar = PopoEntry(filterbar_frame, width=108)
        self.searchBar.bind('<Return>', self.newSearch)
        self.searchBar.bind('<KP_Enter>', self.newSearch)
        # searchBar.bind("<Button-3>", self.do_popup)
        self.searchBar.pack(side="left", fill="x", expand=True)
        self.textSearchVal = tk.BooleanVar()
        self.textSearchVal.set(self.settings.local_settings.get("textsearch", False))
        
        checkbox_text_search = CTkSwitch(filterbar_frame, text="Text search", variable=self.textSearchVal, command=self.textSearchChanged)
        checkbox_text_search.pack(side="left", padx=5)
        self.keep_parents_val = tk.BooleanVar()
        self.keep_parents_val.set(self.settings.local_settings.get("keep_parents", True))
        checkbox_keep_parent = CTkSwitch(filterbar_frame, text="Keep parents", variable=self.keep_parents_val, command=self.keepParentsChanged)
        checkbox_keep_parent.pack(side="left", padx=5)
        self.search_icon = tk.PhotoImage(file=utils.getIcon("search.png"))
        btnSearchBar = ttk.Button(filterbar_frame, text="", image=self.search_icon, style="iconbis.TButton", tooltip="Filter elements based of complex query or only text if textsearch is selected", width=10, command=self.newSearch)
        btnSearchBar.pack(side="left", fill="x")
        image=Image.open(utils.getIcon("reset_small.png"))
        self.reset_icon = ImageTk.PhotoImage(image)
        btnReset = ttk.Button(filterbar_frame, image=self.reset_icon, text="",  style="iconbis.TButton", tooltip="Reset search bar filter", width=10, command=self.endSearch)
        btnReset.pack(side="left", fill="x")
        self.photo = CTkImage(Image.open(utils.getHelpIconPath()))
        self.helpFrame = None
        self.btnHelp = CTkButton(filterbar_frame, text="",image=self.photo,  fg_color="transparent", width=10, command=self.showSearchHelp)

        self.btnHelp.pack(side="left")
        filterbar_frame.pack(side=tk.TOP,fill=tk.X)
        self.statusbar = StatusBar(searchFrame, self.statusbarClicked)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        searchFrame.pack(side="top", fill="x")
        #PANED PART
        self.paned = tk.PanedWindow(self.mainPageFrame, orient="horizontal")
        #RIGHT PANE : Canvas + frame
        
        self.proxyFrameMain = CTkFrame(self.paned)
        self.proxyFrameMain.rowconfigure(0, weight=1) 
        self.proxyFrameMain.columnconfigure(0, weight=1) 
        self.viewframe = ScrollableFrameXPlateform(self.proxyFrameMain)
        
        
        #LEFT PANE : Treeview
        self.left_pane = CTkFrame(self.paned)
        self.frameTw = CTkFrame(self.left_pane)
        self.frameTw.rowconfigure(1, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        self.frameTw.columnconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        self.treevw = PentestTreeview(self, self.frameTw)
        frameContext = CTkFrame(self.frameTw)
        self.btn_context = CTkSegmentedButton(frameContext, values=["Hosts", "Checklist"], width=200, height=45, command=self.checklistViewSwap)
        self.btn_context.set("Check" if self.settings.is_checklist_view() else "Hosts")
        self.btn_context.pack(side="left")
        frameContext.grid(row=0, column=0)
        self.treevw.initUI()
        self.scbVSel = CTkScrollbar(self.frameTw,
                                orientation=tk.VERTICAL,
                                command=self.treevw.yview)
        self.treevw.configure(yscrollcommand=self.scbVSel.set)
        self.treevw.grid(row=1, column=0, sticky=tk.NSEW)
        self.scbVSel.grid(row=1, column=1, sticky=tk.NS)
        # FILTER PANE:
        # self.filtersFrame = CTkFrame(self.left_pane)
        # self.initFiltersFrame(self.filtersFrame)
        # self.filtersFrame.pack(side="bottom", fill="x")
        # END PANE PREP
        self.frameTw.pack(side="top", fill=tk.BOTH, expand=True)
        
        self.left_pane.pack(side="left", fill=tk.BOTH, expand=True)
        self.paned.add(self.left_pane)
        self.proxyFrameMain.pack(side="right", fill=tk.BOTH, expand=True)
        self.viewframe.pack(fill=tk.BOTH, expand=1)
        
        self.paned.add(self.proxyFrameMain)

        self.paned.pack(fill=tk.BOTH, expand=1)
        self.mainPageFrame.pack(fill="both", expand=True)
        self.nbk.add(self.mainPageFrame, "Main View", order=Module.HIGH_PRIORITY, image=self.main_tab_img)
        
        self.nbk
    def searchbarSelectAll(self, _event=None):
        """
        Callback to select all the text in searchbar
        Args:
            _event: not used but mandatory
        """
        self.searchBar.select_range(0, 'end')
        self.searchBar.icursor('end')
        return "break"

   
    def checklistViewSwap(self, _event=None):
        is_checklist_view = "Check" in self.btn_context.get()
        settings = Settings()
        settings.local_settings["checklist_view"] = is_checklist_view
        settings.saveLocalSettings()
        self.treevw.checklistViewSwap()

    def initCommandsView(self):
        """Populate the command tab menu view frame with cool widgets"""
        self.commandsPageFrame = CTkFrame(self.topviewframe)
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
                    module["object"].open(module["view"], self.topviewframe, self.treevw)

    def initSettingsView(self):
        """Add the settings view frame to the notebook widget and initialize its UI."""
        self.settingViewFrame = CTkFrame(self.topviewframe)
        self.settings.initUI(self.settingViewFrame)
        self.nbk.add(self.settingViewFrame, "Settings", order=Module.LAST_PRIORITY, image=self.settings_tab_img)

    def initScanView(self):
        """Add the scan view frame to the notebook widget. This does not initialize it as it needs a database to be opened."""
        self.scanViewFrame = CTkFrame(self.topviewframe)
        self.scanManager.initUI(self.scanViewFrame)
        self.nbk.add(self.scanViewFrame, "Scan", order=Module.HIGH_PRIORITY, image=self.scan_tab_img)

    def initAdminView(self):
        """Add the admin button to the notebook"""
        self.admin = AdminView(self.topviewframe)
        self.adminViewFrame = CTkFrame(self.topviewframe)
        self.admin.initUI(self.adminViewFrame)
        self.nbk.add(self.adminViewFrame, "Admin", order=Module.LOW_PRIORITY, image=self.admin_tab_img)

    def openScriptModule(self):
        """Open the script window"""
        self.scriptManager = ScriptManager()
        self.scriptManager.initUI(self)
        self.wait_window(self.scriptManager.app)

    def initUI(self):
        """
        initialize all the main windows objects. (Bar Menu, contextual menu, treeview, editing pane)
        """
        if self.nbk is not None:
            self.refreshUI()
            return
        self.nbk = ButtonNotebook(self, self.tabSwitch, self.beforeTabSwitch)
        self.panedTerminals = ttk.PanedWindow(self.nbk, orient="vertical")
        self.topviewframe = CTkFrame(self.panedTerminals)
        self.terminals = TerminalsWidget(self.panedTerminals, self,  height=200)
        
        self.initMainView()
        self.initAdminView()
        self.initCommandsView()
        self.initScanView()
        self.initSettingsView()

        for module in self.modules:
            module["view"] = CTkFrame(self.topviewframe)
        for module in self.modules:
            self.nbk.add(module["view"], module["name"].strip(), order=module["object"].__class__.order_priority, image=module["img"])
        self.terminals.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=1)
        self.topviewframe.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.panedTerminals.add(self.topviewframe, weight=1)
        self.panedTerminals.add(self.terminals, weight=0)
        
        self.panedTerminals.pack(fill=tk.BOTH, expand=True)
        

        
        self.nbk.pack(fill=tk.BOTH, expand=1)
        self.terminals.open_terminal()


    def refreshUI(self):
        for widget in self.viewframe.winfo_children():
            widget.destroy()
        
        self.left_pane.update()
        self.after(50, lambda: self.paned.paneconfigure(self.left_pane, height=self.left_pane.winfo_reqheight()))
        
        self.treevw.refresh()
        self.treevw.filter_empty_nodes()
        self.statusbar.refreshTags(Settings.getTags(ignoreCache=True))
        #self.terminals.open_terminal()
        # self.nbk.select("Main View")

    def open_terminal(self, iid, title):
        self.terminals.open_terminal(iid, title)

    def execute_in_terminal(self, title, commandline):
        iid = str(uuid.uuid4())
        self.terminals.open_terminal(iid, title, enable_trap=False)
        self.terminals.launch_in_terminal(iid, commandline, use_pollex=False)

    def launch_in_terminal(self, iid, title, commandline, use_pollex=True):
        if iid is None:
            iid = str(uuid.uuid4())
        self.terminals.open_terminal(iid, title, enable_trap=use_pollex)
        self.terminals.launch_in_terminal(iid, commandline, use_pollex=use_pollex)
        return iid

    def launch_tool_in_terminal(self, tool_model, command):
        self.terminals.open_terminal(str(tool_model.check_iid)+"|"+str(tool_model.getId()), ToolController(tool_model).getDetailedString())
        self.terminals.launch_in_terminal(str(tool_model.check_iid)+"|"+str(tool_model.getId()), command)

    def open_ro_terminal(self, check_iid, title, tool_controller, scanManager):
        self.terminals.open_ro_terminal(check_iid, title, tool_controller, scanManager)

    def open_any_terminal(self, iid, title, tool_controller, scanManager):
        self.terminals.open_any_terminal(iid, title, tool_controller, scanManager)
        
    def textSearchChanged(self, event=None):
        """Called when the textual search bar is modified. Change settings
        Args:
            event: not used but mandatory
        """
        self.settings.local_settings["textsearch"] = int(self.textSearchVal.get())
        self.settings.saveLocalSettings()

    def keepParentsChanged(self, event=None):
        """Called when the keep parent switch is modified. Change settings
        Args:
            event: not used but mandatory
        """
        self.settings.local_settings["keep_parents"] = int(self.keep_parents_val.get())
        self.settings.saveLocalSettings()
    
    def newSearch(self, _event=None, histo=True, text_search_allowed=True):
        """Called when the searchbar is validated (click on search button or enter key pressed).
        Perform a filter on the main treeview.
        Args:
            _event: not used but mandatory"""
        self.searchMode = True
        filterStr = self.searchBar.get()
        if filterStr.strip() == "":
            self.endSearch()
            return
        self.settings.reloadSettings()
        success = self.treevw.filterTreeview(filterStr, self.settings, text_search_allowed)
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
        datamanager = DataManager.getInstance()
        taggeds = datamanager.get("tags", "*")
        tagged_items = []
        tagged_types = set()
        for tagged in taggeds:
            for tag in tagged.tags:
                tag = TagInfos(tag)
                if tag.name == name:
                    tagged_items.append(tagged)
                    tagged_types.add(tagged.item_type)
        for module in self.modules:
            for tagged_type in tagged_types:
                if tagged_type.lower() in getattr(module["object"], "classes", []):
                    if hasattr(module["object"], "statusbarClicked"):
                        self.nbk.select(module["name"].strip())
                        module["object"].statusbarClicked(name)
                    return
        # default 
        self.nbk.select("Main View")
        self.searchTaggedBy(name)

    def modelToView(self, collection, model):
        """Return the view of a model"""
        if collection.lower()[-1] != "s":
            collection = collection.lower() + "s"
        for module in self.modules:
            if collection.lower() == getattr(module["object"], "coll_name", "").lower() or collection.lower() in getattr(module["object"], "classes", ""):
                return module["object"].modelToView(collection, model)
        return self.treevw.modelToView(collection, model)
    
    def search(self, filter_str):
        self.nbk.select("Main View")
        
        self.searchBar.delete(0, tk.END)
        self.searchBar.insert(tk.END, filter_str)
        self.newSearch(histo=False, text_search_allowed=False)

    def searchTaggedBy(self, tag_name):
        self.nbk.select("Main View")
        apiclient = APIClient.getInstance()
        searcher = apiclient.searchTaggedBy(tag_name)
        if searcher.get("success", True):
            self.searchMode = True
            self.treevw.doFilterTreeview(searcher, True, keep_parents=self.settings.local_settings.get("keep_parents", True))
            
    def endSearch(self):
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
                    module["object"].open(module["view"], self.topviewframe, self.treevw)
        if activeTw is not None:
            if len(activeTw.selection()) == 1:
                setViewOn = activeTw.selection()[0]
            activeTw.refresh(force=True)
            self.statusbar.refreshTags(Settings.getTags(ignoreCache=True))

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

    def wrapperTestLocalTools(self):
        results = self.testLocalTools()
        dialog = ChildDialogToolsInstalled(results)
        if dialog.rvalue is not None:
            self.settings.local_settings["my_commands"] = dialog.rvalue
            self.settings.saveLocalSettings()

    def testLocalTools(self):
        """ test local binary path with which"""
        apiclient = APIClient.getInstance()
        self.settings.reloadLocalSettings()
        plugins = apiclient.getPlugins()
        results = {"successes":[], "failures":[]}
        expanded_bin_paths = []
        for plugin in plugins:
            if plugin["plugin"] == "Default":
                continue
            my_commands = self.settings.local_settings.get("my_commands", {})
            my_commands = {} if my_commands is None else my_commands
            bin_path = my_commands.get(plugin["plugin"])
            expanded_bin_paths.append(bin_path)
            expanded_bin_paths += plugin["default_bin_names"]
        expanded_paths = utils.which_expand_aliases(expanded_bin_paths)
        for plugin in plugins:
            if plugin["plugin"] == "Default":
                continue
            my_commands = self.settings.local_settings.get("my_commands", {})
            my_commands = {} if my_commands is None else my_commands
            bin_path = my_commands.get(plugin["plugin"])
            expanded_bin_path = expanded_paths.get(bin_path)
            if bin_path is None or bin_path == "" or expanded_bin_path is None:
                default_bin_names = plugin["default_bin_names"]
                found_matching = False
                for default_bin_name in default_bin_names:
                    if expanded_paths.get(default_bin_name):
                        plugin["bin_path"] = default_bin_name
                        bin_path = default_bin_name
                        my_commands[plugin["plugin"]] = default_bin_name
                        results["successes"].append({"title":"Success", "plugin":plugin, "bin_path":bin_path,  "default_bin":plugin["default_bin_names"], "msg":f"The local settings for {plugin['plugin']} is valid. ({bin_path})."})
                        found_matching = True
                        break
                if found_matching == False:
                    results["failures"].append({"title":"Invalid binary path", "plugin":plugin, "bin_path":bin_path,  "default_bin":plugin["default_bin_names"], "msg":f"The local settings for {plugin['plugin']} is not recognized. ({bin_path})."})
            elif expanded_bin_path is not None:
                results["successes"].append({"title":"Success", "plugin":plugin, "bin_path":bin_path,  "default_bin":plugin["default_bin_names"], "msg":f"The local settings for {plugin['plugin']} is valid. ({bin_path})."})
            else:
                results["failures"].append({"title":"Invalid binary path", "plugin":plugin, "bin_path":bin_path,  "default_bin":plugin["default_bin_names"], "msg":f"The local settings for {plugin['plugin']} is not recognized. ({bin_path})."})
        self.settings.local_settings["my_commands"] = my_commands
        self.settings.saveLocalSettings()
        return results
    

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
            f = tkinter.filedialog.askopenfilename(parent=self, defaultextension=".json")
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
            f = tkinter.filedialog.askopenfilename(parent=self, defaultextension=".json")
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
            f = tkinter.filedialog.askopenfilename(defaultextension=".json")
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

    def openPentestsWindow(self, _event=None, pentests=None):
        """
        Open Pentest dialog window
        Args:
            _event: Not used but mandatory
        Returns:
            None if no database were selected
            datababase name otherwise
        """
        dialog = ChildDialogPentests(self, pentests)
        try:
            dialog.wait_window(dialog)
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

    def closePentest(self, close_terminals=True):
        """
        Close the current pentest and refresh the treeview.
        """
        apiclient = APIClient.getInstance()
        apiclient.dettach(self)
        if self.terminals is not None and close_terminals:
            self.terminals.onClosing()
        
        if self.scanManager is not None:
            self.scanManager.onClosing()
        
            
        for module in self.modules:
            if callable(getattr(module["object"], "onClosing", None)):
                module["object"].onClosing()

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
            self.closePentest(close_terminals=False)
            first_use_detected = self.detectFirstUse()
            res = apiclient.setCurrentPentest(pentestName, first_use_detected)
            if not res:
                tk.messagebox.showerror("Connection failed", "Could not connect to "+str(pentestName))
                return
            DataManager.getInstance().openPentest(pentestName)
            self.initUI()
            self.settings.reloadSettings()
            self.statusbar.refreshTags(Settings.getTags(ignoreCache=True))
            self.sio.emit("registerForNotifications", {"token":apiclient.getToken(), "pentest":pentestName})
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
