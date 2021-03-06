"""Hold functions to interact form the scan tab in the notebook"""
from core.Components.apiclient import APIClient
import tkinter as tk
import tkinter.ttk as ttk
import multiprocessing
from core.Models.Command import Command
from core.Models.Tool import Tool
from core.Application.Dialogs.ChildDialogFileParser import ChildDialogFileParser
from core.Application.Dialogs.ChildDialogEditCommandSettings import ChildDialogEditCommandSettings
from AutoScanWorker import executeCommand
from PIL import Image, ImageTk
import os




class ScanManager:
    """Scan model class"""

    def __init__(self, nbk, linkedTreeview, calendarToScan, settings):
        self.calendarToScan = calendarToScan
        self.nbk = nbk
        self.settings = settings
        self.btn_autoscan = None
        
        self.parent = None
        self.workerTv = None
        self.linkTw = linkedTreeview
        abs_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(abs_path, "../../icon/")
        self.tool_icon = ImageTk.PhotoImage(Image.open(path+"tool.png"))
        self.nok_icon = ImageTk.PhotoImage(Image.open(path+"cross.png"))
        self.ok_icon = ImageTk.PhotoImage(Image.open(path+"done_tool.png"))
        self.running_icon = ImageTk.PhotoImage(Image.open(path+"running.png"))

    def startAutoscan(self):
        """Start an automatic scan. Will try to launch all undone tools."""
        apiclient = APIClient.getInstance()
        workers = apiclient.getWorkers({"pentests":apiclient.getCurrentPentest()})
        workers = [w for w in workers]
        if len(workers) == 0:
            tk.messagebox.showwarning("No selected worker found", "Check worker treeview to see if there are workers registered and double click on the disabled one to enable them")
            return
        if self.settings.db_settings.get("include_all_domains", False):
            answer = tk.messagebox.askyesno(
                "Autoscan warning", "The current settings will add every domain found in attack's scope. Are you sure ?")
            if not answer:
                return
        self.btn_autoscan.configure(text="Stop Scanning", command=self.stopAutoscan)
        apiclient.sendStartAutoScan()
    
    def stop(self):
        """Stop an automatic scan. Will try to stop running tools."""
        apiclient = APIClient.getInstance()
        apiclient.sendStopAutoScan()

    def refreshUI(self):
        """Reload informations and renew widgets"""
        apiclient = APIClient.getInstance()
        workers = apiclient.getWorkers()
        running_scans = Tool.fetchObjects({"status":"running"})
        for children in self.scanTv.get_children():
            self.scanTv.delete(children)
        for running_scan in running_scans:
            self.scanTv.insert('','end', running_scan.getId(), text=running_scan.name, values=(running_scan.dated), image=self.running_icon)
        for children in self.workerTv.get_children():
            self.workerTv.delete(children)
        registeredCommands = set()
        for worker in workers:
            workername = worker["name"]
            try:
                if apiclient.getCurrentPentest() in worker.get("pentests", []):
                    worker_node = self.workerTv.insert(
                        '', 'end', workername, text=workername, image=self.ok_icon)
                else:
                    worker_node = self.workerTv.insert(
                        '', 'end', workername, text=workername, image=self.nok_icon)
            except tk.TclError:
                worker_node = self.workerTv.item(workername)
            worker_registered = apiclient.getWorker({"name":workername})
            commands_registered = worker_registered["registeredCommands"]
            for command in commands_registered:
                try:
                    self.workerTv.insert(
                        worker_node, 'end', 'registered|'+command, text=command, image=self.tool_icon)
                except tk.TclError:
                    pass
                registeredCommands.add(str(command))
            allCommands = Command.getList(None, apiclient.getCurrentPentest())
            for command in allCommands:
                if command not in registeredCommands:
                    try:
                        self.workerTv.insert(
                            worker_node, '0', 'notRegistered|'+command, text=command, image=self.nok_icon)
                    except tk.TclError:
                        pass
                else:
                    try:
                        self.workerTv.delete('notRegistered|'+command)
                    except tk.TclError:
                        pass
        if len(registeredCommands) > 0 and self.btn_autoscan is None:
            if apiclient.getAutoScanStatus():
                self.btn_autoscan = ttk.Button(
                    self.parent, text="Stop Scanning", command=self.stopAutoscan)
                self.btn_autoscan.pack()
            else:
                self.btn_autoscan = ttk.Button(
                    self.parent, text="Start Scanning", command=self.startAutoscan)
                self.btn_autoscan.pack()

    def initUI(self, parent):
        """Create widgets and initialize them
        Args:
            parent: the parent tkinter widget container."""
        if self.workerTv is not None:
            self.refreshUI()
            return
        apiclient = APIClient.getInstance()
        self.parent = parent
        ### WORKER TREEVIEW : Which worker knows which commands
        lblworker = ttk.Label(self.parent, text="Workers:")
        lblworker.pack(side=tk.TOP, padx=10, pady=5, fill=tk.X)
        self.workerTv = ttk.Treeview(self.parent)
        self.workerTv['columns'] = ('workers')
        self.workerTv.heading("#0", text='Workers', anchor=tk.W)
        self.workerTv.column("#0", anchor=tk.W)
        self.workerTv.pack(side=tk.TOP, padx=10, pady=10, fill=tk.X)
        self.workerTv.bind("<Double-Button-1>", self.OnWorkerDoubleClick)
        self.workerTv.bind("<Delete>", self.OnWorkerDelete)
        workers = apiclient.getWorkers()
        total_registered_commands = 0
        registeredCommands = set()
        for worker in workers:
            workername = worker["name"]
            try:
                if apiclient.getCurrentPentest() in worker.get("pentests", []):
                    worker_node = self.workerTv.insert(
                        '', 'end', workername, text=workername, image=self.ok_icon)
                else:
                    worker_node = self.workerTv.insert(
                        '', 'end', workername, text=workername, image=self.nok_icon)
            except tk.TclError:
                pass
            commands_registered = apiclient.getRegisteredCommands(
                workername)
            for command in commands_registered:
                try:
                    self.workerTv.insert(worker_node, 'end', 'registered|'+str(command),
                                    text=command, image=self.tool_icon)
                except tk.TclError:
                    pass
                registeredCommands.add(str(command))
            allCommands = Command.getList(None, apiclient.getCurrentPentest())
            for command in allCommands:
                if command not in registeredCommands:
                    try:
                        self.workerTv.insert(worker_node, '0', 'notRegistered|' +
                                        str(command), text=str(command), image=self.nok_icon)
                    except tk.TclError:
                        pass
            total_registered_commands += len(registeredCommands)
        #### TREEVIEW SCANS : overview of ongoing auto scan####
        lblscan = ttk.Label(self.parent, text="Scan overview:")
        lblscan.pack(side=tk.TOP, padx=10, pady=5, fill=tk.X)
        self.scanTv = ttk.Treeview(self.parent)
        self.scanTv['columns'] = ('Started at')
        self.scanTv.heading("#0", text='Scans', anchor=tk.W)
        self.scanTv.column("#0", anchor=tk.W)
        self.scanTv.pack(side=tk.TOP, padx=10, pady=10, fill=tk.X)
        self.scanTv.bind("<Double-Button-1>", self.OnDoubleClick)
        running_scans = Tool.fetchObjects({"status":"running"})
        for running_scan in running_scans:
            self.scanTv.insert('','end', running_scan.getId(), text=running_scan.name, values=(running_scan.dated), image=self.running_icon)
        #### BUTTONS FOR AUTO SCANNING ####
        if total_registered_commands > 0:
            if apiclient.getAutoScanStatus():
                self.btn_autoscan = ttk.Button(
                    self.parent, text="Stop Scanning", command=self.stopAutoscan)
                self.btn_autoscan.pack()
            else:
                self.btn_autoscan = ttk.Button(
                    self.parent, text="Start Scanning", command=self.startAutoscan)
                self.btn_autoscan.pack()
        btn_parse_scans = ttk.Button(
            self.parent, text="Parse existing files", command=self.parseFiles)
        btn_parse_scans.pack()

    def OnDoubleClick(self, event):
        """Callback for a double click on ongoing scan tool treeview. Open the clicked tool in main view and focus on it.
        Args:
            event: Automatically filled when event is triggered. Holds info about which line was double clicked
        """
        if self.scanTv is not None:
            self.nbk.select(0)
            tv = event.widget
            item = tv.identify("item", event.x, event.y)
            self.linkTw.see(item)
            self.linkTw.selection_set(item)
            self.linkTw.focus(item)


    def stopAutoscan(self):
        """
        Stop an automatic scan. Will terminate celery running tasks.
        """
        try:
            if self.btn_autoscan is not None:
                self.btn_autoscan.configure(
                    text="Start Scanning", command=self.startAutoscan)
        except tk.TclError:
            pass
        print("Stopping auto... ")
        apiclient = APIClient.getInstance()
        apiclient.sendStopAutoScan()

    def parseFiles(self):
        """
        Ask user to import existing files to import.
        """
        dialog = ChildDialogFileParser(self.parent)
        self.parent.wait_window(dialog.app)

    def notify(self, _iid, _action):
        """
        Reload UI when notified
        """
        if self.workerTv is not None:
            self.refreshUI()

    def sendEditToolConfig(self, worker, command_name, remote_bin, plugin):
        apiclient = APIClient.getInstance()
        apiclient.sendEditToolConfig(worker, command_name, remote_bin, plugin)

    def OnWorkerDoubleClick(self, event):
        """Callback for treeview double click.
        If a link treeview is defined, open mainview and focus on the item with same iid clicked.
        Args:
            event: used to identified which link was clicked. Auto filled
        """
        if self.workerTv is not None:
            tv = event.widget
            item = tv.identify("item", event.x, event.y)
            parent = self.workerTv.parent(item)
            if str(parent) != "": # child node = tool
                command_name = item.split("|")[1]
                dialog = ChildDialogEditCommandSettings(self.parent, "Edit worker tools config")
                self.parent.wait_window(dialog.app)
                if isinstance(dialog.rvalue, tuple):
                    self.sendEditToolConfig(parent, command_name, dialog.rvalue[0], dialog.rvalue[1])
            else: # no parent node = worker node
                self.setUseForPentest(item)
    
    def setUseForPentest(self, worker_hostname):
        apiclient = APIClient.getInstance()
        worker = apiclient.getWorker({"name":worker_hostname})
        if worker is not None:
            isIncluded = apiclient.getCurrentPentest() in worker.get("pentests", [])
            apiclient.setWorkerInclusion(worker_hostname, not (isIncluded))

    def launchTask(self, toolModel, parser="", checks=True, worker=""):
        apiclient = APIClient.getInstance()
        launchableToolId = toolModel.getId()
        if worker == "" or worker == "localhost":
            thread = None
            thread = multiprocessing.Process(target=executeCommand, args=(
                apiclient, str(launchableToolId), parser, True))
            thread.start()
            toolModel.markAsRunning(worker)

        else:
            apiclient.sendLaunchTask(toolModel.getId(), parser, checks, worker)


    def OnWorkerDelete(self, event):
        """Callback for a delete key press on a worker.
        Force deletion of worker
        Args:
            event: Auto filled
        """
        apiclient = APIClient.getInstance()
        if "@" in str(self.workerTv.selection()[0]):
            apiclient.deleteWorker(self.workerTv.selection()[0]) 