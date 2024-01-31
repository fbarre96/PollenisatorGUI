"""Hold functions to interact form the scan tab in the notebook"""
from pollenisatorgui.core.application.dialogs.ChildDialogAutoScanParams import ChildDialogAutoScanParams
from pollenisatorgui.core.application.dialogs.ChildDialogScanHistory import ChildDialogScanHistory
from pollenisatorgui.core.application.dialogs.ChildDialogToolsInstalled import ChildDialogToolsInstalled
from pollenisatorgui.core.application.scrollableframexplateform import ScrollableFrameXPlateform
from pollenisatorgui.core.application.scrollabletreeview import ScrollableTreeview
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.datamanager import DataManager
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
import threading
import time
from pollenisatorgui.core.components.scanworker import ScanWorker
from pollenisatorgui.core.controllers.toolcontroller import ToolController
from pollenisatorgui.core.forms.formpanel import FormPanel
from pollenisatorgui.core.models.tool import Tool
from pollenisatorgui.core.application.dialogs.ChildDialogFileParser import ChildDialogFileParser
from pollenisatorgui.core.application.dialogs.ChildDialogProgress import ChildDialogProgress
from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.models.checkinstance import CheckInstance
from PIL import Image
import pollenisatorgui.core.components.utils as utils
import os
import docker
from bson import ObjectId
from pollenisatorgui.core.components.logger_config import logger

import shutil


def start_docker(dialog, force_reinstall):
    dialog.update(msg="Building worker docker could take a while (1~10 minutes depending on internet connection speed)...")
    try:
        client = docker.from_env()
        clientAPI = docker.APIClient()
    except Exception as e:
        dialog.destroy()
        tk.messagebox.showerror("Unable to launch docker", e)
        return
    try:
        log_generator = clientAPI.pull("algosecure/pollenisator-worker:latest",stream=True,decode=True)
        change_max = None
        for byte_log in log_generator:
            log_line = byte_log["status"].strip()
            dialog.update(log=log_line+"\n")
    except docker.errors.APIError as e:
        dialog.destroy()
        tk.messagebox.showerror("APIError docker error", "Pulling error:\n"+str(e))
        return
    image = client.images.list("algosecure/pollenisator-worker")
    if len(image) == 0:
        tk.messagebox.showerror("Pulling docker failed", "The docker pull command failed, try to install manually...")
        return
    dialog.update(2, msg="Starting worker docker ...")
    clientCfg = utils.loadClientConfig()
    if clientCfg["host"] == "localhost" or clientCfg["host"] == "127.0.0.1":
        network_mode = "host"
    else:
        network_mode = None
    container = client.containers.run(image=image[0], network_mode=network_mode, volumes={os.path.join(utils.getConfigFolder()):{'bind':'/root/.config/pollenisator-gui/', 'mode':'rw'}}, detach=True)
    dialog.update(3, msg="Checking if worker is running")
    print(container.id)
    if container.logs() != b"":
        print(container.logs())
    dialog.destroy()
    
class ScanManager:
    """Scan model class"""

    def __init__(self, mainApp, nbk, linkedTreeview, pentestToScan, settings):
        self.pentestToScan = pentestToScan
        self.mainApp = mainApp
        self.nbk = nbk
        self.settings = settings
        self.btn_autoscan = None
        self.workers = None
        self.btn_docker_worker = None
        self.parent = None
        self.sio = None
        self.workerTv = None
        self.linkTw = linkedTreeview
        self.scan_worker = ScanWorker(self.settings)
        self.tool_icon = tk.PhotoImage(file=utils.getIcon("tool.png"))
        self.nok_icon = tk.PhotoImage(file=utils.getIcon("cross.png"))
        self.waiting_icon = tk.PhotoImage(file=utils.getIcon("waiting.png"))
        self.ok_icon = tk.PhotoImage(file=utils.getIcon("done_tool.png"))
        self.running_icon = tk.PhotoImage(file=utils.getIcon("running.png"))
        DataManager.getInstance().attach(self)

    def startAutoscan(self):
        """Start an automatic scan. Will try to launch all undone tools."""
        apiclient = APIClient.getInstance()
        if len(self.workerTv.get_children()) == 0:
            if not self.ask_start_worker():
                return
        workers = apiclient.getWorkers({"pentest":apiclient.getCurrentPentest()})
        workers = [w for w in workers]
        if len(workers) == 0:
            tk.messagebox.showwarning("No selected worker found", "A worker exist but is not registered for this pentest. You might want to register it by double clicking on it or using the Use button.")
            return False
        dialog = ChildDialogAutoScanParams(self.parent)
        dialog.wait_window()
        params = dialog.rvalue
        if params is None:
            return
        if self.settings.db_settings.get("include_all_domains", False):
            answer = tk.messagebox.askyesno(
                "Autoscan warning", "The current settings will add every domain found in attack's scope. Are you sure ?")
            if not answer:
                return False
        self.btn_autoscan.configure(text="Stop Scanning", command=self.stopAutoscan)
        apiclient.sendStartAutoScan(command_iids=params["commands"], autoqueue=params["autoqueue"])
        return True
    
    def stop(self):
        """Stop an automatic scan. Will try to stop running tools."""
        apiclient = APIClient.getInstance()
        apiclient.sendStopAutoScan()
        logger.debug('Ask stop autoscan')
        return True

    def refreshRunningScans(self):
        running_scans = list(Tool.fetchObjects({"status":"running"}))
        checks = CheckInstance.fetchObjects([str(ObjectId(running_scan.check_iid)) for running_scan in running_scans if running_scan.check_iid != ""])
        mapping = {}
        for check in checks:
            mapping[str(check._id)] = check
        try:
            for children in self.scanTv.get_children():
                self.scanTv.delete(children)
        except tk.TclError:
            pass
        except RuntimeError:
            return
        for running_scan in running_scans:
            check = mapping.get(str(running_scan.check_iid), None)
            group_name = "" if check is None else check.check_m.title
            try:
                self.scanTv.insert('','end', running_scan.getId(), text=group_name, values=(running_scan.name, running_scan.dated), image=self.running_icon)
            except tk.TclError:
                pass

    def refreshQueuedScans(self):
        apiclient = APIClient.getInstance()
        queued_scans = apiclient.getQueue()
        if queued_scans is None:
            return 
        checks = CheckInstance.fetchObjects([str(ObjectId(queued_scan["check_iid"])) for queued_scan in queued_scans if queued_scan["check_iid"] != ""])
        mapping = {}
        for check in checks:
            mapping[str(check._id)] = check
        try:
            for children in self.queueTv.get_children():
                self.queueTv.delete(children)
        except tk.TclError:
            pass
        except RuntimeError:
            return
        for queued_scan in queued_scans:
            check = mapping.get(str(queued_scan["check_iid"]), None)
            group_name = "" if check is None else check.check_m.title
            try:
                self.queueTv.insert('','end', str(queued_scan["_id"]), text=group_name, values=(queued_scan["name"], queued_scan["text"]), image=self.waiting_icon, auto_update_pagination=False)
            except tk.TclError:
                pass
        self.queueTv.setPaginationPanel()

    def is_worker_valid_for_pentest(self, worker_data):
        apiclient = APIClient.getInstance()
        return worker_data.get("pentest", "") == apiclient.getCurrentPentest()


    def refreshWorkers(self):
        apiclient = APIClient.getInstance()
        workers = apiclient.getWorkers()
        self.workers = workers
        try:
            for children in self.workerTv.get_children():
                self.workerTv.delete(children)
        except:
            pass
        registeredCommands = set()
        for worker in workers:
            workername = worker["name"]
            try:
                if self.is_worker_valid_for_pentest(worker):
                    worker_node = self.workerTv.insert(
                        '', 'end', workername, text=workername, image=self.ok_icon)
                else:
                    worker_node = self.workerTv.insert(
                        '', 'end', workername, text=workername, image=self.nok_icon)
            except tk.TclError as err:
                try:
                    worker_node = self.workerTv.item(workername)["text"]
                except Exception as e:
                    print(str(err)+" occured")
                    print("Then:"+str(e))
            except RuntimeError:
                pass
        return len(workers)
    
    def is_already_queued(self, tool_iid):
        try:
            children = self.queueTv.get_children()
            return tool_iid in children
        except tk.TclError:
            return False


    def _check_worker(self):
        foundValidWorker = False
        
        if self.workers:
            for worker in self.workers:
                if self.is_worker_valid_for_pentest(worker):
                    foundValidWorker = True
                    break
        if not foundValidWorker:
            return False, "No worker available yet."
        return True, ""
    
    def is_ready_to_queue(self, tool_iid=None):
        apiclient = APIClient.getInstance()
        res, msg = self._check_worker()
        if not res:
            return res, msg
        if not apiclient.getAutoScanStatus():
            return False, "No autoscan running."
        if tool_iid is not None:
            if self.is_already_queued(tool_iid):
                return False, "Tool already queued."
        return True, ""
    
    def is_ready_to_run_tasks(self):
        res, msg = self._check_worker()
        if not res:
            return res, msg
        return True, ""

    def slider_event(self, event):
        val = self.autoscan_slider.get()
        val = int(val)
        self.autoscan_threads_lbl.configure(text=str(val) + " thread"+("s" if val > 1 else ""))
        self.settings.setPentestSetting("autoscan_threads", val)

    def update_thread_label(self, event):
        val = self.autoscan_slider.get()
        val = int(round(val)) 
        self.autoscan_threads_lbl.configure(text=str(val) + " thread"+("s" if val > 1 else ""))

    def refreshUI(self):
        """Reload informations and renew widgets"""
        apiclient = APIClient.getInstance()
        self.refreshRunningScans()
        self.refreshQueuedScans()
        self.settings._reloadDbSettings()
        v = int(self.settings.db_settings.get("autoscan_threads", 4))
        self.autoscan_slider.set(v)
        self.update_thread_label(v)
        
        nb_workers = self.refreshWorkers()
        
        if self.btn_autoscan is None:
            if apiclient.getAutoScanStatus():
                self.btn_autoscan = CTkButton(
                    self.parent, text="Stop Scanning", image=self.image_auto, command=self.stopAutoscan, fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
            else:
                self.btn_autoscan = CTkButton(
                    self.parent, text="Start Scanning", command=self.startAutoscan)
        
        if nb_workers == 0:
            self.ask_start_worker()
        logger.debug('Refresh scan manager UI')

    def ask_start_worker(self):
        options = ["Use this computer", "Run a preconfigured Docker on server"]
        options.append("Run a preconfigured Docker locally")
        options.append("Cancel")
        dialog = ChildDialogQuestion(self.parent, "Register worker ?", "There is no running scanning clients. What do you want to do ?", options)
        self.parent.wait_window(dialog.app)
        if dialog.rvalue is not None:
            rep = options.index(dialog.rvalue)
            if rep == 1:
                self.runWorkerOnServer()
            elif rep == 0:
                self.registerAsWorker()
            elif rep == 2:
                self.launchDockerWorker()
            return True
        return False

    def initUI(self, parent):
        """Create widgets and initialize them
        Args:
            parent: the parent tkinter widget container."""
        if self.parent is not None:
            self.refreshUI()
            return
        apiclient = APIClient.getInstance()
        self.parent = parent
        parentScrollableFrame = ScrollableFrameXPlateform(self.parent)
        parentFrame = ttk.Frame(parentScrollableFrame)
        parentFrame.columnconfigure(0, weight=1)
        parentFrame.columnconfigure(1, weight=1)
        parentFrame.rowconfigure(0, weight=1)
        parentFrame.configure(onfiledrop=self.dropFile)
        ### WORKER TREEVIEW : Which worker knows which commands
        workerScanFrame = CTkFrame(parentFrame)
        workerFrame = CTkFrame(workerScanFrame)
        workerFrame.columnconfigure(0, weight=1)
        self.workerTv = ttk.Treeview(workerFrame, height=3)
        self.workerTv['columns'] = ('workers')
        self.workerTv.heading("#0", text='Workers', anchor=tk.W)
        self.workerTv.column("#0", anchor=tk.W)
        self.workerTv.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=10)
        self.workerTv.bind("<Double-Button-1>", self.OnWorkerDoubleClick)
        self.workerTv.bind("<Delete>", self.OnWorkerDelete)
        btn_pane = FormPanel(row=0, column=1, sticky=tk.W+tk.E, grid=True)
        pane = btn_pane.addFormPanel(row=0,column=0)
        pane.addFormButton("Use/Stop using selected worker", callback=self.setWorkerInclusion, side=tk.LEFT)
        pane.addFormHelper("Give / Remove the right for a worker to work for the current pentest", side=tk.LEFT)
        pane = btn_pane.addFormPanel(row=1,column=0)
        pane.addFormButton("Start remote worker",  callback=self.runWorkerOnServer, side=tk.LEFT)
        pane.addFormHelper("Start a docker worker on the remote server", side=tk.LEFT)
        
        pane = btn_pane.addFormPanel(row=2,column=0)
        pane.addFormButton("Start worker locally", callback=self.launchDockerWorker, side=tk.LEFT)
        pane.addFormHelper("Require Docker, pull and run the worker docker locally", side=tk.LEFT)
        pane = btn_pane.addFormPanel(row=3,column=0)
        pane.addFormButton("Use this computer", callback=self.registerAsWorker, side=tk.LEFT)
        pane.addFormHelper("Use this computer as a worker", side=tk.LEFT)
        btn_pane.constructView(workerFrame)
        workerFrame.pack(side=tk.TOP, pady=5)
        self.image_auto = CTkImage(Image.open(utils.getIcon("auto.png")))
        self.image_import = CTkImage(Image.open(utils.getIcon("import.png")))
        if apiclient.getAutoScanStatus():
            self.btn_autoscan = CTkButton(
                workerScanFrame, text="Stop Scanning", image=self.image_auto, command=self.stopAutoscan)
            self.btn_autoscan.pack()
        else:
            self.btn_autoscan = CTkButton(
                workerScanFrame, text="Start Scanning", image=self.image_auto, command=self.startAutoscan)
            self.btn_autoscan.pack()
        frame_settings = CTkFrame(workerScanFrame)
        self.autoscan_slider = CTkSlider(frame_settings, from_=1, to=10, number_of_steps=10, command=self.update_thread_label)
        self.autoscan_slider.bind("<ButtonRelease-1>", self.slider_event)
        self.autoscan_slider.pack(side=tk.LEFT, padx=5)
        threads = int(self.settings.db_settings.get("autoscan_threads", 4))
        self.autoscan_slider.set(threads)
        self.autoscan_threads_lbl = CTkLabel(frame_settings, text=str(threads)+" thread"+("s" if threads > 1 else ""))
        self.autoscan_threads_lbl.pack(side=tk.LEFT, padx=5)
        frame_settings.pack()
        workerScanFrame.grid(row=0, column=0, sticky=tk.NSEW)
        importScanFrame = CTkFrame(parentFrame)
        sep = ttk.Separator(importScanFrame, orient="vertical")
        sep.pack(side="left", fill="y" , padx=10, pady=10)
        btn_parse_scans = CTkButton(
            importScanFrame, text="Parse existing files", image=self.image_import, command=self.parseFiles)
        btn_parse_scans.place(relx=0.5, rely=0.5, anchor=CENTER)
        info = CTkLabel(importScanFrame, text="You can also drop your files / folder here")
        info.pack(side=tk.BOTTOM, pady=10)
        importScanFrame.grid(row=0, column=1, padx=10, sticky=tk.NSEW)
        ####### RUNNING SCANS
        scansInfoFrame = CTkFrame(parentFrame)
        
        self.scanTv = ttk.Treeview(scansInfoFrame)
        self.scanTv['columns'] = ('Tool', 'Started at')
        self.scanTv.heading("#0", text='Running scans', anchor=tk.W)
        self.scanTv.column("#0", anchor=tk.W)
        self.scanTv.pack(side=tk.TOP, padx=10, pady=10, fill=tk.X)
        self.scanTv.bind("<Double-Button-1>", self.OnDoubleClick)
        panelActions = CTkFrame(scansInfoFrame)
        refresh_button = CTkButton(panelActions, text="Refresh scans", command=self.refreshRunningScans)
        refresh_button.pack(side=tk.LEFT, pady=2, padx=10)
        self.show_history = CTkButton(panelActions, text="Show history", command=self.showHistory)
        self.show_history.pack(side=tk.LEFT, pady=2, padx=10)
        panelActions.pack(side=tk.BOTTOM, pady=2, padx=10)
        scansInfoFrame.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)
        ###### QUEUED
        queuedScansFrame = CTkFrame(parentFrame)
        
        self.queueTv = ScrollableTreeview(queuedScansFrame,  ("Check type", 'Tool', 'options'))
        self.queueTv.pack(side=tk.TOP, padx=10, pady=10, fill=tk.X)
        self.queueTv.bind("<Delete>", self.remove__selected_tasks)
        clear_queue_btn = CTkButton(queuedScansFrame, text="Clear queue", command=self.clear_queue)
        clear_queue_btn.pack(side=tk.BOTTOM, pady=2, padx=10)
        queuedScansFrame.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW)

        ######
        parentFrame.pack(expand=1, fill=tk.BOTH)
        parentScrollableFrame.pack(expand=1, fill=tk.BOTH)

    def clear_queue(self, event=None):
        apiclient = APIClient.getInstance()
        apiclient.clear_queue()

    def remove__selected_tasks(self, _event=None):
        items = self.queueTv.selection()
        if items:
            apiclient = APIClient.getInstance()
            apiclient.sendRemoveTasks(items)

    def showHistory(self, event=None):
        dialog = ChildDialogScanHistory(self.parent)

    def dropFile(self, event):
        # This function is called, when stuff is dropped into a widget
        data = utils.drop_file_event_parser(event)
        self.parseFiles(data)

    def OnDoubleClick(self, event):
        """Callback for a double click on ongoing scan tool treeview. Open the clicked tool in main view and focus on it.
        Args:
            event: Automatically filled when event is triggered. Holds info about which line was double clicked
        """
        if self.scanTv is not None:
            tv = event.widget
            item = tv.identify("item", event.x, event.y)
        self.openInTerminalView(item)
        self.openInMainView(item)

    def openInMainView(self, item):
        self.nbk.select("Main View")
        self.mainApp.search("id == \""+str(item)+"\"")
    
    def openInTerminalView(self, item):
        datamanager = DataManager.getInstance()
        tool = datamanager.get("tools", str(item))
        if tool:
            tool_controller = ToolController(tool)
            self.mainApp.open_any_terminal(str(tool.check_iid)+"|"+str(tool_controller.getDbId()), tool_controller.getDetailedString(), tool_controller, self)
    
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
        logger.debug('Ask stop autoscan from UI')

    def parseFiles(self, default_path=""):
        """
        Ask user to import existing files to import.
        """
        dialog = ChildDialogFileParser(self.mainApp, default_path)
        self.parent.wait_window(dialog.app)

    def update_received(self, dataManager, notif, obj, old_obj):
        """
        Reload UI when notified
        """
        if notif["db"] == "pollenisator":
            if notif["collection"] == "workers":
                if self.workerTv is not None:
                    self.refreshWorkers() 
        # elif notif["collection"] == "tools" and notif["action"] == "update":
        #     if dataManager.currentPentest == notif["db"]:
        #         self.refreshRunningScans()
        #         self.refreshQueuedScans()
        

    def OnWorkerDoubleClick(self, event):
        """Callback for treeview double click.
        If a link treeview is defined, open mainview and focus on the item with same iid clicked.
        Args:
            event: used to identified which link was clicked. Auto filled
        """
        if self.workerTv is not None:
            if event:
                tv = event.widget
                item = tv.identify("item", event.x, event.y)
            parent = self.workerTv.parent(item)
            self.setUseForPentest(item)
    
    def setWorkerInclusion(self, _event=None):
        items = self.workerTv.selection()
        for item in items:
            if "|" not in self.workerTv.item(item)["text"]: # exclude tools and keep worker nodes
                self.setUseForPentest(item)

    def setUseForPentest(self, worker_hostname):
        apiclient = APIClient.getInstance()
        worker = apiclient.getWorker({"name":worker_hostname})
        if worker is not None:
            isIncluded = apiclient.getCurrentPentest() == worker.get("pentest", "")
            apiclient.setWorkerInclusion(worker_hostname, not (isIncluded))

    def getToolProgress(self, toolId):
        return self.scan_worker.getToolProgress(toolId)

    def stopTask(self, toolId):
        return self.scan_worker.stopTask(toolId)

    def launchTask(self, toolModel, checks=True, worker="", infos={}):
        return self.scan_worker.launchTask(toolModel, checks=checks, worker=worker, infos=infos)


    def OnWorkerDelete(self, event):
        """Callback for a delete key press on a worker.
        Force deletion of worker
        Args:
            event: Auto filled
        """
        apiclient = APIClient.getInstance()
        dialog = ChildDialogProgress(self.parent, "Docker delete", "Waiting for worker to stop", progress_mode="indeterminate")
        dialog.show()
        apiclient.deleteWorker(self.workerTv.selection()[0]) 
        dialog.destroy()
    

    def launchDockerWorker(self, event=None):
        dialog = ChildDialogProgress(self.parent, "Starting worker docker", "Initialisation ...",  progress_mode="indeterminate", show_logs=True)
        dialog.show(4)
        x = threading.Thread(target=start_docker, args=(dialog, True))
        x.start()
        return x


    def runWorkerOnServer(self, _event=None):
        apiclient = APIClient.getInstance()
        docker_name = apiclient.getDockerForPentest(apiclient.getCurrentPentest())
        dialog = ChildDialogProgress(self.parent, "Start docker", "Waiting for docker to boot 0/4", progress_mode="indeterminate")
        dialog.show()
        nb_try = 0
        max_try = 3
        while docker_name not in self.workerTv.get_children() and nb_try < max_try:
            dialog.update(msg=f"Waiting for docker to boot {nb_try+1}/{max_try+1}")
            time.sleep(3)
            nb_try += 1
        dialog.destroy()
        if docker_name not in self.workerTv.get_children():
            return False, "Worker did not boot in time, cannot add commands to wave"
        return True, ""

    def onClosing(self):
        logger.debug("Scan manager on closing state.")
        try:
            client = docker.from_env()
            containers = client.containers.list()
            for container in containers:
                if container.image.tags[0].startswith("algosecure/pollenisator-worker"):
                    
                    dialog = ChildDialogProgress(self.parent, "Stopping docker", "Waiting for docker to stop", progress_mode="indeterminate")
                    dialog.show()
                    logger.debug("Stopping running worker....")
                    container.stop()
                    container.remove()
                    logger.debug("done.")
                    dialog.destroy()
        except Exception as e:
            pass
        self.scan_worker.onClosing()
        apiclient = APIClient.getInstance()
        apiclient.deleteWorker(apiclient.getUser()) 
        if self.sio is not None:
            self.sio.disconnect()

    

    def is_local_launched(self, toolId):
        return self.scan_worker.is_local_launched(toolId)

    def registerAsWorker(self, _event=None):
        prog = ChildDialogProgress(self.parent, "Testing local tools", "Testing which tools will be available...", progress_mode="indeterminate")
        prog.show()
        prog.update()
        results = self.mainApp.testLocalTools()
        if len(results["failures"]) > 0:
            dialog = ChildDialogToolsInstalled(results)
            if dialog.rvalue is not None:
                self.settings.local_settings["my_commands"] = dialog.rvalue
                self.settings.saveLocalSettings()
        prog.destroy()

        self.settings.reloadLocalSettings()
        apiclient = APIClient.getInstance()
        name = apiclient.getUser()
        self.scan_worker.connect(name)
        dialog = ChildDialogProgress(self.parent, "Registering", "Waiting for register 0/4", progress_mode="indeterminate")
        dialog.show()
        nb_try = 0
        max_try = 3
        while name not in self.workerTv.get_children() and nb_try < max_try:
            dialog.update(msg=f"Waiting for registering {nb_try+1}/{max_try+1}")
            time.sleep(2)
            nb_try += 1
        dialog.destroy()
        if name not in self.workerTv.get_children():
            return False, "Worker did not boot in time, cannot add commands to wave"
        apiclient.setWorkerInclusion(name, True)
