"""
Pollenisator client GUI window.
"""
import traceback
import tkinter.filedialog
import tkinter as tk
import tkinter.messagebox
import tkinter.simpledialog
import tkinter.ttk as ttk
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
import pollenisatorgui.core.Components.Utils as Utils
from pollenisatorgui.core.Application.Treeviews.CalendarTreeview import CalendarTreeview
from pollenisatorgui.core.Application.Treeviews.CommandsTreeview import CommandsTreeview
from pollenisatorgui.core.Application.Dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.Application.Dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.Application.Dialogs.ChildDialogConnect import ChildDialogConnect
from pollenisatorgui.core.Application.Dialogs.ChildDialogNewCalendar import ChildDialogNewCalendar
from pollenisatorgui.core.Application.Dialogs.ChildDialogException import ChildDialogException
from pollenisatorgui.core.Application.Dialogs.ChildDialogInfo import ChildDialogInfo
from pollenisatorgui.core.Application.Dialogs.ChildDialogFileParser import ChildDialogFileParser
from pollenisatorgui.core.Application.Dialogs.ChildDialogEditPassword import ChildDialogEditPassword
from pollenisatorgui.core.Application.StatusBar import StatusBar
from pollenisatorgui.core.Components.apiclient import APIClient, ErrorHTTP
from pollenisatorgui.core.Components.ScanManager import ScanManager
from pollenisatorgui.core.Components.Admin import AdminView
from pollenisatorgui.core.Components.ScriptManager import ScriptManager
from pollenisatorgui.core.Components.Settings import Settings
from pollenisatorgui.core.Components.Filter import Filter
from pollenisatorgui.core.Models.Port import Port
import pollenisatorgui.core.Components.Modules

class FloatingHelpWindow(tk.Toplevel):
    """floating basic window with helping text inside
    Inherit tkinter TopLevel
    Found on the internet (stackoverflow) but did not keep link sorry...
    """

    def __init__(self, w, h, posx, posy, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.title('Help: search')
        self.x = posx
        self.y = posy
        self.geometry(str(w)+"x"+str(h)+"+"+str(posx)+"+"+str(posy))
        self.resizable(0, 0)
        self.config(bg='light yellow')
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


class AutocompleteEntry(ttk.Entry):
    """Inherit ttk.Entry.
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
        ttk.Entry.__init__(self, *args, **kwargs)
        self.width = kwargs.get("width",100)
        self.lista = set()
        self.var = self["textvariable"]
        if self.var == '':
            self.var = self["textvariable"] = tk.StringVar()
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
                self.lb = tk.Listbox(width=self.width)
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

class Appli(tk.Tk):
    """
    Main tkinter graphical application object.
    """
    version_compatible = "1.1.*"
    def __init__(self):
        """
        Initialise the application

        """
        # Lexic:
        # view frame : the frame in the tab that will hold forms.
        # Tree view : the tree on the left of the window.
        # frame tree view : a frame around the tree view (useful to attach a scrollbar to a treeview)
        # canvas : a canvas object (useful to attach a scrollbar to a frame)
        # paned : a Paned widget is used to separate two other widgets and display a one over the other if desired
        #           Used to separate the treeview frame and view frame.
        super().__init__()
        self.quitting = False
        self.settingViewFrame = None
        self.scanManager = None  #  Loaded when clicking on it if linux only
        self.scanViewFrame = None
        self.admin = None
        self.nbk = None
        self.sio = None #socketio client
        self.initialized = False
        self.setStyle()
        self.main_tab_img = ImageTk.PhotoImage(
            Image.open(Utils.getIconDir()+"tab_main.png"))
        self.commands_tab_img = ImageTk.PhotoImage(
            Image.open(Utils.getIconDir()+"tab_commands.png"))
        self.scan_tab_img = ImageTk.PhotoImage(
            Image.open(Utils.getIconDir()+"tab_scan.png"))
        self.settings_tab_img = ImageTk.PhotoImage(
            Image.open(Utils.getIconDir()+"tab_settings.png"))
        self.admin_tab_img = ImageTk.PhotoImage(
            Image.open(Utils.getIconDir()+"tab_admin.png"))
        # HISTORY : Main view and command where historically in the same view;
        # This results in lots of widget here with a confusing naming style
        #### core components (Tab menu on the left objects)####
        #### MAIN VIEW ####
        self.openedViewFrameId = None
        self.mainPageFrame = None
        self.paned = None
        self.canvasMain = None
        self.viewframe = None
        self.frameTw = None
        self.treevw = None
        self.myscrollbarMain = None
        #### COMMAND VIEW ####
        self.commandsPageFrame = None
        self.commandPaned = None
        self.commandsFrameTw = None
        self.canvas = None
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
        dir_path = os.path.dirname(os.path.realpath(__file__))
        dir_path = os.path.join(dir_path, "../../icon/favicon.png")
    
        img = tk.PhotoImage(file=dir_path)
        self.resizable(True, True)
        self.iconphoto(True, img)
        self.minsize(width=400, height=400)
        self.resizable(True, True)
        self.title("Pollenisator")
        self.geometry("1220x830")
        self.protocol("WM_DELETE_WINDOW", self.onClosing)
        self.settings = Settings()
        self.initModules()
        apiclient = APIClient.getInstance()
        apiclient.appli = self
        opened = self.openConnectionDialog()
        if not opened:
            self.wait_visibility()
            self.openConnectionDialog(force=True)
            self.promptCalendarName()
            
    # OVERRIDE tk.Tk.report_callback_exception
    def report_callback_exception(self, exc, val, tb):
        self.show_error(exc, val, tb)
        
    def quit(self):
        super().quit()
        self.quitting = True
        return

    def forceUpdate(self):
        tkinter.messagebox.showwarning("Update necessary", "You have to update this client to use this API.")

    def openConnectionDialog(self, force=False):
        # Connect to database and choose database to open
        apiclient = APIClient.getInstance()
        abandon = False
        if force:
            apiclient.disconnect()
        while (not apiclient.tryConnection(force=force) or not apiclient.isConnected()) and not abandon:
            abandon = self.promptForConnection() is None
        if not abandon:
            apiclient = APIClient.getInstance()
            apiclient.attach(self)
            srv_version = apiclient.getVersion()
            if int(Appli.version_compatible.split(".")[0]) != int(srv_version.split(".")[0]):
                self.forceUpdate()
                self.onClosing()
                return
            if int(Appli.version_compatible.split(".")[1]) != int(srv_version.split(".")[1]):
                self.forceUpdate()
                self.onClosing()
                return
            if self.sio is not None:
                self.sio.disconnect()
            self.sio = socketio.Client()
            @self.sio.event
            def notif(data):
                self.handleNotif(json.loads(data, cls=Utils.JSONDecoder))
            
            self.sio.connect(apiclient.api_url)
            self.initUI()
            pentests = apiclient.getPentestList()
            if pentests is None:
                pentests = []
            else:
                pentests = [x["nom"] for x in pentests][::-1]
            if apiclient.getCurrentPentest() != "" and apiclient.getCurrentPentest() in pentests:
                self.openCalendar(apiclient.getCurrentPentest())
            self.initialized = True
            # self.promptCalendarName(), called beacause tabSwitch is called
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
            in iter_namespace(pollenisatorgui.core.Components.Modules)
        }
        self.modules = []
        for name, module in discovered_plugins.items():
            module_class = getattr(module, name.split(".")[-1])
            module_obj = module_class(self, self.settings)
            self.modules.append({"name": module_obj.tabName, "object":module_obj, "view":None, "img":ImageTk.PhotoImage(Image.open(Utils.getIconDir()+module_obj.iconName))})

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
        print("GOT NOTIF : " +str(notification))
        if notification["db"] == "pollenisator":
            if notification["collection"] == "workers":
                self.scanManager.notify(notification["iid"], notification["action"])
            elif "commands" in notification["collection"]:
                self.commandsTreevw.notify(notification["db"], notification["collection"], notification["iid"], notification["action"], notification.get("parent", ""))
            elif "settings" in notification["collection"]:
                self.settings.notify(notification["db"], notification["iid"], notification["action"])
                self.treevw.notify(notification["db"],  notification["collection"], notification["iid"], notification["action"], "")
                self.statusbar.refreshTags(Settings.getTags(ignoreCache=True))
                self.treevw.configureTags()
        else:
            if notification["collection"] == "settings":
                self.settings.notify(notification["db"], notification["iid"], notification["action"])
                
                self.statusbar.refreshUI()
            else:
                print("NOTIFY")
                self.treevw.notify(notification["db"], notification["collection"],
                            notification["iid"], notification["action"], notification.get("parent", ""))
            for module in self.modules:
                if callable(getattr(module["object"], "notify", None)):
                    module["object"].notify(notification["db"], notification["collection"],
                            notification["iid"], notification["action"], notification.get("parent", ""))

   

    def onClosing(self):
        """
        Close the application properly.
        """
        apiclient = APIClient.getInstance()
        apiclient.dettach(self)
        print("Stopping application...")
        if self.sio is not None:
            self.sio.disconnect()
        for module in self.modules:
            if callable(getattr(module["object"], "onClosing", None)):
                module["object"].onClosing()
        self.quit()

    def _initMenuBar(self):
        """
        Create the bar menu on top of the screen.
        """
        menubar = tk.Menu(self, tearoff=0, bd=0, background='#73B723', foreground='white', activebackground='#73B723', activeforeground='white')
        self.config(menu=menubar)

        self.bind('<F5>', self.refreshView)
        self.bind('<Control-o>', self.promptCalendarName)
        fileMenu = tk.Menu(menubar, tearoff=0, background='#73B723', foreground='white', activebackground='#73B723', activeforeground='white')
        fileMenu.add_command(label="New", command=self.selectNewCalendar)
        fileMenu.add_command(label="Open (Ctrl+o)",
                             command=self.promptCalendarName)
        fileMenu.add_command(label="Connect to server", command=self.promptForConnection)
        fileMenu.add_command(label="Copy", command=self.wrapCopyDb)
        fileMenu.add_command(label="Delete a database",
                             command=self.deleteACalendar)
        fileMenu.add_command(label="Export database",
                             command=self.exportCalendar)
        fileMenu.add_command(label="Import database",
                             command=self.importCalendar)
        fileMenu.add_command(label="Export commands",
                             command=self.exportCommands)
        fileMenu.add_command(label="Import commands",
                             command=self.importCommands)

        fileMenu.add_command(label="Exit", command=self.onExit)
        fileMenu2 = tk.Menu(menubar, tearoff=0, background='#73B723', foreground='white', activebackground='#73B723', activeforeground='white')
        fileMenu2.add_command(label="Import existing tools results ...",
                              command=self.importExistingTools)
        fileMenu2.add_command(label="Reset unfinished tools",
                              command=self.resetUnfinishedTools)
        fileMenu2.add_command(label="Refresh (F5)",
                              command=self.refreshView)
        fileMenuUser = tk.Menu(menubar, tearoff=0, background='#73B723', foreground='white', activebackground='#73B723', activeforeground='white')
        fileMenuUser.add_command(label="Change your password",
                              command=self.changeMyPassword)
        fileMenuUser.add_command(label="Disconnect", command=self.disconnect)
        fileMenu3 = tk.Menu(menubar, tearoff=0, background='#73B723', foreground='white', activebackground='#73B723', activeforeground='white')
        fileMenu3.add_command(label="Submit a bug or feature",
                              command=self.submitIssue)
        menubar.add_cascade(label="Database", menu=fileMenu)
        menubar.add_cascade(label="Scans", menu=fileMenu2)
        menubar.add_command(label="Scripts...", command=self.openScriptModule)
        menubar.add_cascade(label="User", menu=fileMenuUser)
        menubar.add_cascade(label="Help", menu=fileMenu3)

    def setStyle(self, _event=None):
        """
        Set the pollenisator window widget style using ttk.Style
        Args:
            _event: not used but mandatory
        """
        style = ttk.Style(self)
        style.theme_use("clam")
        try:
            style.element_create('Plain.Notebook.tab', "from", 'default')
        except TclError:
            pass # ALready exists
        style.configure("Treeview.Heading", background="#73B723",
                        foreground="white", relief="flat")
        style.map('Treeview.Heading', background=[('active', '#73B723')])
        style.configure("TLabelframe", background="white",
                        labeloutside=False, bordercolor="#73B723")
        style.configure('TLabelframe.Label', background="#73B723",
                        foreground="white", font=('Sans', '10', 'bold'))
        style.configure("TProgressbar",
                        background="#73D723", foreground="#73D723", troughcolor="white", darkcolor="#73D723", lightcolor="#73D723")
        style.configure("Important.TFrame", background="#73B723")
        style.configure("TFrame", background="white")
        style.configure("Important.TLabel", background="#73B723", foreground="white")
        style.configure("TLabel", background="white")
        style.configure("TCombobox", background="white")
        
        style.configure("TCheckbutton", background="white",
                        font=('Sans', '10', 'bold'))
        style.configure("TButton", background="#73B723",
                        foreground="white", font=('Sans', '10', 'bold'), borderwidth=1)
        style.configure("icon.TButton", background="white", borderwidth=0)
        style.configure("TNotebook", background="#73B723", foreground="white", font=(
            'Sans', '10', 'bold'), tabposition='wn', borderwidth=0, width=100)

        style.configure("TNotebook.Tab", background="#73B723", borderwidth=0,
                        foreground="white", font=('Sans', '10', 'bold'), padding=20, bordercolor="#73B723")
        style.map('TNotebook.Tab', background=[('active', '#73C723'), ("selected", '#73D723')], foreground=[("active", "white")], font=[("active", (
            'Sans', '10', 'bold'))], padding=[('active', 20)])
        style.map('TButton', background=[('active', '#73D723')])
        #  FIX tkinter tag_configure not showing colors   https://bugs.python.org/issue36468
        style.map('Treeview', foreground=Appli.fixedMap('foreground', style),
                  background=Appli.fixedMap('background', style))
        # Removed dashed line https://stackoverflow.com/questions/23354303/removing-ttk-notebook-tab-dashed-line/23399786
        style.layout("TNotebook.Tab",
                     [('Plain.Notebook.tab',
                       {'children':[('Notebook.padding', {'side': 'top', 'children': [('Notebook.label', {
                           'side': 'top', 'sticky': ''})], 'sticky': 'nswe'})],
                        'sticky': 'nswe'})])

    @staticmethod
    def fixedMap(option, style):
        """
        Fix color tag in treeview not appearing under some linux distros
        Args:
            option: the string option you want to affect on treeview ("background" for example)
            strle: the style object of ttk
        """
        # Fix for setting text colour for Tkinter 8.6.9
        # From: https://core.tcl.tk/tk/info/509cafafae
        #  FIX tkinter tag_configure not showing colors   https://bugs.python.org/issue36468
        # Returns the style map for 'option' with any styles starting with
        # ('!disabled', '!selected', ...) filtered out.

        # style.map() returns an empty list for missing options, so this
        # should be future-safe.
        return [elm for elm in style.map('Treeview', query_opt=option) if
                elm[:2] != ('!disabled', '!selected')]


    def initMainView(self):
        """
        Fill the main view tab menu
        """
        self.mainPageFrame = ttk.Frame(self.nbk)
        searchFrame = ttk.Frame(self.mainPageFrame)
        lblSearch = ttk.Label(searchFrame, text="Filter bar:")
        lblSearch.pack(side="left", fill=tk.NONE)
        self.searchBar = AutocompleteEntry(self.settings, searchFrame)
        #self.searchBar = ttk.Entry(searchFrame, width=108)
        self.searchBar.bind('<Return>', self.newSearch)
        self.searchBar.bind('<KP_Enter>', self.newSearch)
        self.searchBar.bind('<Control-a>', self.searchbarSelectAll)
        # searchBar.bind("<Button-3>", self.do_popup)
        self.searchBar.pack(side="left", fill="x", expand=True)
        btnSearchBar = ttk.Button(searchFrame, style="icon.TButton")
        self.search_icon = tk.PhotoImage(file=Utils.getIcon("search.png"))
        btnSearchBar.config(image=self.search_icon, command=self.newSearch)
        btnSearchBar.pack(side="left", fill="x")
        self.reset_icon = tk.PhotoImage(file=Utils.getIcon("delete.png"))
        btnReset = ttk.Button(searchFrame, image=self.reset_icon, command=self.resetButtonClicked, style="icon.TButton")
        btnReset.pack(side="left", fill="x")
        self.btnHelp = ttk.Button(searchFrame, style="icon.TButton")
        self.photo = tk.PhotoImage(file=Utils.getHelpIconPath())
        self.helpFrame = None
        self.btnHelp.config(image=self.photo, command=self.showSearchHelp)
        self.btnHelp.pack(side="left")
        searchFrame.pack(side="top", fill="x")
        #PANED PART
        self.paned = tk.PanedWindow(self.mainPageFrame, height=800)
        #RIGHT PANE : Canvas + frame
        self.canvasMain = tk.Canvas(self.paned, bg="white")
        self.viewframe = ttk.Frame(self.canvasMain)
        #LEFT PANE : Treeview
        self.frameTw = ttk.Frame(self.paned)
        self.treevw = CalendarTreeview(self, self.frameTw)
        self.treevw.initUI()
        scbVSel = ttk.Scrollbar(self.frameTw,
                                orient=tk.VERTICAL,
                                command=self.treevw.yview)
        self.treevw.configure(yscrollcommand=scbVSel.set)
        self.treevw.grid(row=0, column=0, sticky=tk.NSEW)
        scbVSel.grid(row=0, column=1, sticky=tk.NS)
        self.paned.add(self.frameTw)
        self.myscrollbarMain = tk.Scrollbar(self.paned, orient="vertical", command=self.canvasMain.yview)
        self.myscrollbarMain.pack(side="right", fill=tk.BOTH)
        self.canvasMain.bind('<Enter>', self.boundToMousewheelMain)
        self.canvasMain.bind('<Leave>', self.unboundToMousewheelMain)
        self.canvasMain.pack(side="left")
        self.canvasMain.bind('<Configure>', self.resizeCanvasMainFrame)
        self.canvas_main_frame = self.canvasMain.create_window((0, 0), window=self.viewframe, anchor='nw')
        self.viewframe.bind("<Configure>", self.scrollFrameMainFunc)
        self.canvasMain.configure(yscrollcommand=self.myscrollbarMain.set)
        self.paned.add(self.canvasMain)
        self.paned.pack(fill=tk.BOTH, expand=1)
        self.frameTw.rowconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        self.frameTw.columnconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        self.nbk.add(self.mainPageFrame, text="  Main View ", image=self.main_tab_img, compound=tk.TOP, sticky='nsew')
    
    def searchbarSelectAll(self, _event):
        """
        Callback to select all the text in searchbar
        Args:
            _event: not used but mandatory
        """
        self.searchBar.select_range(0, 'end')
        self.searchBar.icursor('end')
        return "break"

    def boundToMousewheel(self, _event):
        """Called when the **command canvas** is on focus.
        Bind the command scrollbar button on linux to the command canvas
        Args:
            _event: not used but mandatory
        """
        if self.canvas is None:
            return
        self.canvas.bind_all("<Button-4>", self._onMousewheelCommand)
        self.canvas.bind_all("<Button-5>", self._onMousewheelCommand)

    def unboundToMousewheel(self, _event):
        """Called when the **command canvas** is unfocused.
        Unbind the command scrollbar button on linux to the command canvas
        Args:
            _event: not used but mandatory"""
        if self.canvas is None:
            return
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def boundToMousewheelMain(self, _event):
        """Called when the **main view canvas** is focused.
        Bind the main view scrollbar button on linux to the main view canvas
        Args:
            _event: not used but mandatory"""
        if self.canvas is None:
            return
        self.canvas.bind_all("<Button-4>", self._onMousewheelMain)
        self.canvas.bind_all("<Button-5>", self._onMousewheelMain)

    def unboundToMousewheelMain(self, _event):
        """Called when the **main view canvas** is unfocused.
        Unbind the main view scrollbar button on linux to the main view canvas
        Args:
            _event: not used but mandatory"""
        self.canvasMain.unbind_all("<Button-4>")
        self.canvasMain.unbind_all("<Button-5>")

    def _onMousewheelMain(self, event):
        """Called when a scroll occurs. boundToMousewheelMain must be called first.
        Performs the scroll on the main canvas.
        Args:
            event: Holds info on scroll within event.delta and event.num"""
        if event.num == 5 or event.delta == -120:
            count = 1
        if event.num == 4 or event.delta == 120:
            count = -1
        self.canvasMain.yview_scroll(count, "units")

    def _onMousewheelCommand(self, event):
        """Called when a scroll occurs. boundToMousewheel must be called first.
        Performs the scroll on the command canvas.
        Args:
            event: Holds info on scroll within event.delta and event.num"""
        if event.num == 5 or event.delta == -120:
            count = 1
        if event.num == 4 or event.delta == 120:
            count = -1
        if self.canvas is None:
            return
        self.canvas.yview_scroll(count, "units")

    def scrollFrameMainFunc(self, _event):
        """make the main canvas scrollable"""
        self.canvasMain.configure(scrollregion=self.canvasMain.bbox("all"), width=20, height=200)

    def scrollFrameFunc(self, _event):
        """make the command canvas scrollable"""
        if self.canvas is None:
            return
        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=20, height=200)

    def initCommandsView(self):
        """Populate the command tab menu view frame with cool widgets"""
        self.commandsPageFrame = ttk.Frame(self.nbk)
        self.commandPaned = tk.PanedWindow(self.commandsPageFrame, height=800)
        self.commandsFrameTw = ttk.Frame(self.commandPaned)
        self.canvas = tk.Canvas(self.commandPaned, bg="white")
        self.commandsFrameTw.pack(expand=True)
        self.commandsViewFrame = ttk.Frame(self.canvas)
        self.myscrollbarCommand = tk.Scrollbar(self.commandPaned, orient="vertical", command=self.canvas.yview)
        self.myscrollbarCommand.pack(side="right", fill=tk.BOTH)
        self.canvas.bind('<Enter>', self.boundToMousewheel)
        self.canvas.bind('<Leave>', self.unboundToMousewheel)
        self.canvas.bind('<Configure>', self.resizeCanvasFrame)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.commandsViewFrame, anchor='nw')
        self.commandsViewFrame.bind("<Configure>", self.scrollFrameFunc)
        self.canvas.configure(yscrollcommand=self.myscrollbarCommand.set)
        self.commandsTreevw = CommandsTreeview(self, self.commandsFrameTw)
        scbVSel = ttk.Scrollbar(self.commandsFrameTw,
                                orient=tk.VERTICAL,
                                command=self.commandsTreevw.yview)
        self.commandsTreevw.configure(yscrollcommand=scbVSel.set)
        self.commandsTreevw.grid(row=0, column=0, sticky=tk.NSEW)
        scbVSel.grid(row=0, column=1, sticky=tk.NS)
        self.commandPaned.add(self.commandsFrameTw)
        self.commandPaned.add(self.canvas)
        self.commandPaned.pack(fill=tk.BOTH, expand=1)
        self.commandsFrameTw.rowconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        self.commandsFrameTw.columnconfigure(0, weight=1) # Weight 1 sur un layout grid, sans ça le composant ne changera pas de taille en cas de resize
        self.nbk.bind("<<NotebookTabChanged>>", self.tabSwitch)
        self.nbk.add(self.commandsPageFrame, text=" Commands", image=self.commands_tab_img, compound=tk.TOP)

    def resizeCanvasFrame(self, event):
        if self.canvas is None:
            return
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)

    def resizeCanvasMainFrame(self, event):
        canvas_width = event.width
        self.canvasMain.itemconfig(self.canvas_main_frame, width=canvas_width)


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

    def tabSwitch(self, event):
        """Called when the user click on the tab menu to switch tab. Add a behaviour before the tab switches.
        Args:
            event : hold informations to identify which tab was clicked.
        """
        apiclient = APIClient.getInstance()
        tabName = self.nbk.tab(self.nbk.select(), "text").strip()
        self.searchBar.quit()
        if tabName == "Commands":
            self.commandsTreevw.initUI()
        if apiclient.getCurrentPentest() is None or apiclient.getCurrentPentest() == "":
            opened = self.promptCalendarName()
            if opened is None:
                return
        if tabName == "Scan":
            if apiclient.getCurrentPentest() != "":
                self.scanManager.initUI(self.scanViewFrame)
        elif tabName == "Settings":
            self.settings.reloadUI()
        elif tabName == "Admin":
            self.admin.initUI(self.adminViewFrame)
        else:
            for module in self.modules:
                if tabName.strip().lower() == module["name"].strip().lower():
                    module["object"].open()
        event.widget.winfo_children()[event.widget.index("current")].update()

    def initSettingsView(self):
        """Add the settings view frame to the notebook widget and initialize its UI."""
        self.settingViewFrame = ttk.Frame(self.nbk)
        self.settings.initUI(self.settingViewFrame)
        self.settingViewFrame.pack(fill=tk.BOTH, expand=1)
        self.nbk.add(self.settingViewFrame, text="   Settings   ", image=self.settings_tab_img, compound=tk.TOP)

    def initScanView(self):
        """Add the scan view frame to the notebook widget. This does not initialize it as it needs a database to be opened."""
        self.scanViewFrame = ttk.Frame(self.nbk)
        self.nbk.add(self.scanViewFrame, text="     Scan      ", image=self.scan_tab_img, compound=tk.TOP)

    def initAdminView(self):
        """Add the admin button to the notebook"""
        self.admin = AdminView(self.nbk)
        self.adminViewFrame = ttk.Frame(self.nbk)
        self.nbk.add(self.adminViewFrame, text= "    Admin    ", image=self.admin_tab_img, compound=tk.TOP)

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
        self.nbk = ttk.Notebook(self)
        self.statusbar = StatusBar(self, self)
        self.statusbar.pack(fill=tk.X)
        self.nbk.enable_traversal()
        self.initMainView()
        self.initAdminView()
        self.initCommandsView()
        self.initScanView()
        self.initSettingsView()
        for module in self.modules:
            module["view"] = ttk.Frame(self.nbk)
            self.nbk.add(module["view"], text=module["name"],image=module["img"],compound=tk.TOP)
        self._initMenuBar()
        self.nbk.pack(fill=tk.BOTH, expand=1)
        self.refreshUI()

    def refreshUI(self):
        apiclient = APIClient.getInstance()
        tab_names = [self.nbk.tab(i, option="text").strip() for i in self.nbk.tabs()]

        if apiclient.isAdmin():
            self.nbk.add(self.adminViewFrame, text= "    Admin    ", image=self.admin_tab_img, compound=tk.TOP)
        else:
            self.nbk.hide(tab_names.index("Admin"))
    
    def newSearch(self, _event=None):
        """Called when the searchbar is validated (click on search button or enter key pressed).
        Perform a filter on the main treeview.
        Args:
            _event: not used but mandatory"""
        filterStr = self.searchBar.get()
        self.settings.reloadSettings()
        success = self.treevw.filterTreeview(filterStr, self.settings)
        self.searchMode = (success and filterStr.strip() != "")
        if success:
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
        self.nbk.select(0)
        self.searchMode = True
        self.treevw.filterTreeview("\""+name+"\" in tags")

    def resetButtonClicked(self):
        """
        Called when the reset button of the status bar is clicked.
        """
        self.searchMode = False
        self.searchBar.reset()
        self.treevw.unfilter()

    def refreshView(self, _event=None):
        """
        Reload the currently opened tab
        Args:
            _event: not used but mandatory
        """
        setViewOn = None
        nbkOpenedTab = self.nbk.tab(self.nbk.select(), "text").strip()
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
                    module["object"].open()
        if activeTw is not None:
            if len(activeTw.selection()) == 1:
                setViewOn = activeTw.selection()[0]
            activeTw.refresh()
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
            Utils.resetUnfinishedTools()
            self.statusbar.reset()
            self.treevw.load()

    def exportCalendar(self):
        """
        Dump a pentest database to an archive file gunzip.
        """
        apiclient = APIClient.getInstance()
        pentests = apiclient.getPentestList()
        if pentests is None:
            pentests = []
        else:
            pentests = [x["nom"] for x in pentests][::-1]
        dialog = ChildDialogCombo(self, pentests, "Choose a pentest to dump:")
        self.wait_window(dialog.app)
        if isinstance(dialog.rvalue, str):
            success, msg = apiclient.dumpDb(dialog.rvalue)
            if not success:
                tkinter.messagebox.showerror("Database export error", msg)
            else:
                tkinter.messagebox.showinfo("Database export completed", msg)

    def exportCommands(self):
        """
        Dump pollenisator from database to an archive file gunzip.
        """
        dialog = ChildDialogQuestion(self, "Ask question", "Do you want to export your commands or Worker's commands.", ["My commands", "Worker"])
        self.wait_window(dialog.app)
        apiclient = APIClient.getInstance()
        res, msg = apiclient.exportCommands(forWorker=dialog.rvalue == "Worker")
        if res:
            tkinter.messagebox.showinfo(
                "Export pollenisator database", "Export completed in "+str(msg))
        else:
            tkinter.messagebox.showinfo(msg)

    def importCalendar(self, name=None):
        """
        Import a calendar archive file gunzip to database.
        Args:
            name: The filename of the gunzip database exported previously
        """
        apiclient = APIClient.getInstance()
        filename = ""
        if name is None:
            f = tkinter.filedialog.askopenfilename(defaultextension=".gz")
            if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
                return
            filename = str(f)
        else:
            filename = name
        success = apiclient.importDb(filename)
        if success:
            tkinter.messagebox.showinfo("Database import ", "Database import suceeded")
        else:
            tkinter.messagebox.showerror("Database import ", "Database import failed")

    def findUnscannedPorts(self):
        ports = Port.fetchObjects({})
        apiclient = APIClient.getInstance()
        for port in ports:
            port_key = port.getDbKey()
            res = apiclient.find("tools", port_key, False)
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
            f = tkinter.filedialog.askopenfilename(defaultextension=".json")
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

    def onExit(self):
        """
        Exit the application
        """
        self.onClosing()

    def promptCalendarName(self, _event=None):
        """
        Ask a user to select an pentest database including a New database option.
        Args:
            _event: Not used but mandatory
        Returns:
            None if no database were selected
            datababase name otherwise
        """
        apiclient = APIClient.getInstance()
        pentests = apiclient.getPentestList()
        if pentests is None:
            pentests = []
        else:
            pentests = [x["nom"] for x in pentests][::-1]
        dialog = ChildDialogCombo(self, ["New database"]+pentests, "Select a database")
        self.wait_window(dialog.app)
        if dialog.rvalue is None:
            return None
        if isinstance(dialog.rvalue, str):
            if dialog.rvalue == "New database":
                self.selectNewCalendar()
            else:
                self.openCalendar(dialog.rvalue)
            return dialog.rvalue

    def deleteACalendar(self):
        """
        Ask a user a calendar name then delete it.
        """
        apiclient = APIClient.getInstance()
        pentests = apiclient.getPentestList()
        if pentests is None:
            pentests = []
        else:
            pentests = [x["nom"] for x in pentests][::-1]
        dialog = ChildDialogCombo(
            self, pentests, "Choose a database to delete:")
        self.wait_window(dialog.app)
        if isinstance(dialog.rvalue, str):
            calendarName = dialog.rvalue
            dialog = ChildDialogQuestion(
                self, "Pentest deletion confirmation", "You are going to delete permanently the database \""+calendarName+"\". Are you sure ?")
            self.wait_window(dialog.app)
            if dialog.rvalue == "Yes":
                apiclient.doDeletePentest(calendarName)
                self.treevw.deleteState(calendarName)

    def newCalendar(self, calendarName, pentest_type, start_date, end_date, scope, settings, pentesters):
        """
        Register the given calendar name into database and opens it.

        Args:
            calendarName: The pentest database name to register in database.
        """
        succeed = False
        if calendarName is not None:
            apiclient = APIClient.getInstance()
            succeed, msg = apiclient.registerPentest(calendarName, pentest_type, start_date, end_date, scope, settings, pentesters)
            if not succeed:
                tkinter.messagebox.showinfo("Forbidden", msg)
        return succeed

    def selectNewCalendar(self):
        """
        Ask a user for a new calendar name. Then creates it.
        """
        validCalendar = False
        default = {}
        while not validCalendar:
            dialog = ChildDialogNewCalendar(self, default)
            self.wait_window(dialog.app)
            if isinstance(dialog.rvalue, dict):
                default = dialog.rvalue
                dbName = dialog.rvalue["name"]
                pentest_type = dialog.rvalue["type"]
                start_date = dialog.rvalue["start"]
                end_date = dialog.rvalue["end"]
                scope = dialog.rvalue["scope"]
                settings = dialog.rvalue["settings"]
                pentesters = dialog.rvalue["pentesters"]
                validCalendar = self.newCalendar(dbName, pentest_type, start_date, end_date, scope, settings, pentesters)
                if validCalendar:
                    self.lastNotifReadTime = datetime.datetime.now()
                    self.openCalendar(dbName)
            else:
                return
    
    def openCalendar(self, filename=""):
        """
        Open the given database name. Loads it in treeview.

        Args:
            filename: the pentest database name to load in application. If "" is given (default), will refresh the already opened database if there is one.
        """
        calendarName = None
        apiclient = APIClient.getInstance()
        if filename == "" and apiclient.getCurrentPentest() != "":
            calendarName = apiclient.getCurrentPentest()
        elif filename != "":
            calendarName = filename.split(".")[0].split("/")[-1]
        if calendarName is not None:
            res = apiclient.setCurrentPentest(calendarName)
            if not res:
                tk.messagebox.showerror("Connection failed", "Could not connect to "+str(calendarName))
                return
            for widget in self.viewframe.winfo_children():
                widget.destroy()
            for module in self.modules:
                module["object"].initUI(module["view"], self.nbk, self.treevw)
            self.statusbar.refreshTags(Settings.getTags(ignoreCache=True))
            self.statusbar.reset()
            self.treevw.refresh()
            self.scanManager = ScanManager(self.nbk, self.treevw, apiclient.getCurrentPentest(), self.settings)
            self.sio.emit("registerForNotifications", {"token":apiclient.getToken(), "pentest":calendarName})

    def wrapCopyDb(self, _event=None):
        """
        Call default copy database from a callback event.

        Args:
            _event: not used but mandatory
        """
        apiclient = APIClient.getInstance()
        toCopyName = tkinter.simpledialog.askstring(
                "Copy name", "New copy of "+apiclient.getCurrentPentest()+" database name :")
        apiclient.copyDb(apiclient.getCurrentPentest(), toCopyName)

    def importExistingTools(self, _event=None):
        """
        Ask user to import existing files to import.
        """
        dialog = ChildDialogFileParser(self)
        self.wait_window(dialog.app)