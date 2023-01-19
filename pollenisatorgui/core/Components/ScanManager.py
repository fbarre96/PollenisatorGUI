"""Hold functions to interact form the scan tab in the notebook"""
from pollenisatorgui.core.Components.apiclient import APIClient
import tkinter as tk
import tkinter.ttk as ttk
import multiprocessing
import threading
import time
from pollenisatorgui.core.Models.Wave import Wave
from pollenisatorgui.core.Models.Tool import Tool
from pollenisatorgui.core.Application.Dialogs.ChildDialogFileParser import ChildDialogFileParser
from pollenisatorgui.core.Application.Dialogs.ChildDialogProgress import ChildDialogProgress
from pollenisatorgui.core.Application.Dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.Application.Dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.Models.CheckInstance import CheckInstance
from pollenisatorgui.AutoScanWorker import executeTool
from PIL import Image, ImageTk
import pollenisatorgui.core.Components.Utils as Utils
import os
import docker
import re
import socketio
from bson import ObjectId
from pollenisatorgui.core.Components.logger_config import logger

try:
    import git
    git_available = True
except:
    git_available = False
import shutil


def start_docker(dialog, force_reinstall):
    worker_subdir = os.path.join(Utils.getMainDir(), "PollenisatorWorker")
    if os.path.isdir(worker_subdir) and force_reinstall:
        try:
            shutil.rmtree(worker_subdir)
        except:
            pass
    if not os.path.isdir(worker_subdir):
        git.Git(Utils.getMainDir()).clone("https://github.com/fbarre96/PollenisatorWorker.git")
    shutil.copyfile(os.path.join(Utils.getConfigFolder(), "client.cfg"), os.path.join(Utils.getMainDir(), "PollenisatorWorker/config/client.cfg"))
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
    clientCfg = Utils.loadClientConfig()
    if clientCfg["host"] == "localhost" or clientCfg["host"] == "127.0.0.1":
        network_mode = "host"
    else:
        network_mode = None
    container = client.containers.run(image=image[0], network_mode=network_mode, volumes={os.path.join(Utils.getMainDir(), "PollenisatorWorker"):{'bind':'/home/Pollenisator', 'mode':'rw'}}, detach=True)
    dialog.update(3, msg="Checking if worker is running")
    print(container.id)
    if container.logs() != b"":
        print(container.logs())
    dialog.destroy()
    
class ScanManager:
    """Scan model class"""

    def __init__(self, nbk, linkedTreeview, calendarToScan, settings):
        self.calendarToScan = calendarToScan
        self.nbk = nbk
        self.settings = settings
        self.btn_autoscan = None
        self.btn_docker_worker = None
        self.parent = None
        self.sio = None
        self.workerTv = None
        self.linkTw = linkedTreeview
        self.local_scans = dict()
        abs_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(abs_path, "../../icon/")
        self.tool_icon = ImageTk.PhotoImage(Image.open(path+"tool.png"))
        self.nok_icon = ImageTk.PhotoImage(Image.open(path+"cross.png"))
        self.ok_icon = ImageTk.PhotoImage(Image.open(path+"done_tool.png"))
        self.running_icon = ImageTk.PhotoImage(Image.open(path+"running.png"))

    def startAutoscan(self):
        """Start an automatic scan. Will try to launch all undone tools."""
        apiclient = APIClient.getInstance()
        workers = apiclient.getWorkers({"pentest":apiclient.getCurrentPentest()})
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
        logger.debug('Ask start autoscan')
    
    def stop(self):
        """Stop an automatic scan. Will try to stop running tools."""
        apiclient = APIClient.getInstance()
        apiclient.sendStopAutoScan()
        logger.debug('Ask stop autoscan')

    def refreshUI(self):
        """Reload informations and renew widgets"""
        apiclient = APIClient.getInstance()
        workers = apiclient.getWorkers()
        running_scans = Tool.fetchObjects({"status":"running"})
        try:
            for children in self.scanTv.get_children():
                self.scanTv.delete(children)
        except tk.TclError:
            pass
        except RuntimeError:
            return
        for running_scan in running_scans:
            check = CheckInstance.fetchObject({"_id":ObjectId(running_scan.check_iid)})
            group_name = "" if check is None else check.check_m.title
            try:
                self.scanTv.insert('','end', running_scan.getId(), text=group_name, values=(running_scan.name, running_scan.dated), image=self.running_icon)
            except tk.TclError:
                pass
        for children in self.workerTv.get_children():
            try:
                self.workerTv.delete(children)
            except:
                pass
        registeredCommands = set()
        for worker in workers:
            workername = worker["name"]
            try:
                if apiclient.getCurrentPentest() == worker.get("pentest", ""):
                    worker_node = self.workerTv.insert(
                        '', 'end', workername, text=workername, image=self.ok_icon)
                else:
                    worker_node = self.workerTv.insert(
                        '', 'end', workername, text=workername, image=self.nok_icon)
            except tk.TclError:
                try:
                    worker_node = self.workerTv.item(workername)["text"]
                except:
                    pass
        if self.btn_autoscan is None:
            if apiclient.getAutoScanStatus():
                self.btn_autoscan = ttk.Button(
                    self.parent, text="Stop Scanning", command=self.stopAutoscan)
            else:
                self.btn_autoscan = ttk.Button(
                    self.parent, text="Start Scanning", command=self.startAutoscan)
        if len(workers) == 0:
            options = ["Register this computer as worker", "Run a worker on server"]
            if git_available:
                options.append("Run worker locally")
            options.append("Cancel")
            dialog = ChildDialogQuestion(self.parent, "Register worker ?", "There is no running worker. What do you want to do ?", options)
            self.parent.wait_window(dialog.app)
            if dialog.rvalue is not None:
                if dialog.rvalue.endswith("server"):
                    self.runWorkerOnServer()
                elif dialog.rvalue.endswith("worker"):
                    self.registerAsWorker()
                elif dialog.rvalue.endswith("locally"):
                    self.launchDockerWorker()
        logger.debug('Refresh scan manager UI')

    def initUI(self, parent):
        """Create widgets and initialize them
        Args:
            parent: the parent tkinter widget container."""
        if self.parent is not None:
            self.refreshUI()
            return
        apiclient = APIClient.getInstance()
        self.parent = parent
        self.parent.configure(onfiledrop=self.dropFile)
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
        btn_pane = ttk.Frame(self.parent)
        self.btn_setInclusion = ttk.Button(btn_pane, text="Include/exclude selected worker", command=self.setWorkerInclusion)
        self.btn_setInclusion.pack(padx=5, side=tk.RIGHT)
        self.btn_ServerWorker = ttk.Button(btn_pane, command=self.runWorkerOnServer, text="Start remote worker")
        self.btn_ServerWorker.pack(padx=5, side=tk.RIGHT)
        
        if git_available:
            self.btn_docker_worker = ttk.Button(btn_pane, command=self.launchDockerWorker, text="Start worker locally")
            self.btn_docker_worker.pack(padx=5, side=tk.RIGHT)
        self.btn_ServerWorker = ttk.Button(btn_pane, command=self.registerAsWorker, text="Register as worker")
        self.btn_ServerWorker.pack(padx=5, side=tk.RIGHT)
        btn_pane.pack(side=tk.TOP, padx=10, pady=5)
        workers = apiclient.getWorkers()
        # for worker in workers:
        #     workername = worker["name"]
        #     try:
        #         if apiclient.getCurrentPentest() == worker.get("pentest", ""):
        #             worker_node = self.workerTv.insert(
        #                 '', 'end', workername, text=workername, image=self.ok_icon)
        #         else:
        #             worker_node = self.workerTv.insert(
        #                 '', 'end', workername, text=workername, image=self.nok_icon)
        #     except tk.TclError:
        #         pass
        #### TREEVIEW SCANS : overview of ongoing auto scan####
        lblscan = ttk.Label(self.parent, text="Scan overview:")
        lblscan.pack(side=tk.TOP, padx=10, pady=5, fill=tk.X)
        self.scanTv = ttk.Treeview(self.parent)
        self.scanTv['columns'] = ('Tool', 'Started at')
        self.scanTv.heading("#0", text='Scans', anchor=tk.W)
        self.scanTv.column("#0", anchor=tk.W)
        self.scanTv.pack(side=tk.TOP, padx=10, pady=10, fill=tk.X)
        self.scanTv.bind("<Double-Button-1>", self.OnDoubleClick)
        # running_scans = Tool.fetchObjects({"status":"running"})
        # for running_scan in running_scans:
        #     self.scanTv.insert('','end', running_scan.getId(), text=running_scan.name, values=(running_scan.dated), image=self.running_icon)
        #### BUTTONS FOR AUTO SCANNING ####
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
        btn_parse_scans.pack(side="top",pady=10)
        info = ttk.Label(self.parent, text="You can also drop your files / folder here")
        info.pack()

    def dropFile(self, event):
        # This function is called, when stuff is dropped into a widget
        data = Utils.drop_file_event_parser(event)
        self.parseFiles(data)

    def OnDoubleClick(self, event):
        """Callback for a double click on ongoing scan tool treeview. Open the clicked tool in main view and focus on it.
        Args:
            event: Automatically filled when event is triggered. Holds info about which line was double clicked
        """
        if self.scanTv is not None:
            self.nbk.select("Main View")
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
        logger.debug('Ask stop autoscan from UI')

    def parseFiles(self, default_path=""):
        """
        Ask user to import existing files to import.
        """
        dialog = ChildDialogFileParser(default_path)
        self.parent.wait_window(dialog.app)

    def notify(self, _iid, _action):
        """
        Reload UI when notified
        """
        if self.workerTv is not None:
            self.refreshUI()

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
    
    def setWorkerInclusion(self):
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
        thread, queue, queueResponse, toolModel = self.local_scans.get(str(toolId), (None, None,None,None))
        if thread is None or queue is None:
            return ""
        progress = ""
        if thread.is_alive():
            queue.put("\n")
            progress = queueResponse.get()
            return progress
        return ""

    def stopTask(self, toolId):
        thread, queue, queueResponse, toolModel = self.local_scans.get(str(toolId), (None, None, None, None))
        if thread is None:
            return False
        try:
            thread.terminate()
        except:
            pass
        del self.local_scans[str(toolId)]
        toolModel.markAsNotDone()
        return True

    def launchTask(self, toolModel, checks=True, worker="", infos={}):
        logger.debug("Launch task for tool "+str(toolModel.getId()))
        apiclient = APIClient.getInstance()
        launchableToolId = toolModel.getId()
        for item in list(self.local_scans.keys()):
            process_info = self.local_scans.get(item, None)
            if process_info is not None and not process_info[0].is_alive():
                logger.debug("Proc finished : "+str(self.local_scans[item]))
                try:
                    del self.local_scans[item]
                except KeyError:
                    pass

        if worker == "" or worker == "localhost" or worker == apiclient.getUser():
            scan = self.local_scans.get(str(launchableToolId), None)
            if scan is not None:
                if scan[0].is_alive() and str(scan[0].pid) != "":
                    return
                else:
                    del self.local_scans[str(launchableToolId)]
                    scan = None

            logger.debug("Launch task (start process) , local worker , for tool "+str(toolModel.getId()))
            thread = None
            queue = multiprocessing.Queue()
            queueResponse = multiprocessing.Queue()
            thread = multiprocessing.Process(target=executeTool, args=(queue, queueResponse, apiclient, str(launchableToolId), True, False, (worker == apiclient.getUser()), infos, logger))
            thread.start()
            self.local_scans[str(launchableToolId)] = (thread, queue, queueResponse, toolModel)
            logger.debug('Local tool launched '+str(toolModel.getId()))
        else:
            logger.debug('laucnh task, send remote tool launch '+str(toolModel.getId()))
            apiclient.sendLaunchTask(toolModel.getId(), checks, worker)


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
        dialog = ChildDialogProgress(self.parent, "Starting worker docker", "Cloning worker repository ...", length=200, progress_mode="indeterminate", show_logs=True)
        dialog.show(4)
        x = threading.Thread(target=start_docker, args=(dialog, True))
        x.start()
        return x


    def runWorkerOnServer(self):
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
        logger.debug("Scan manager on closing state")
        apiclient = APIClient.getInstance()
        apiclient.deleteWorker(apiclient.getUser()) 
        if self.sio is not None:
            self.sio.disconnect()

    def beacon(self):
        apiclient = APIClient.getInstance()
        try:
            self.sio.emit("keepalive", {"name":apiclient.getUser(), "running_tasks":[str(x) for x in self.local_scans]})
            timer = threading.Timer(5.0, self.beacon)
            timer.start()
        except socketio.exceptions.BadNamespaceError:
            pass

    def registerAsWorker(self):
        self.settings._reloadLocalSettings()
        self.sio = socketio.Client()
        apiclient = APIClient.getInstance()
        self.sio.connect(apiclient.api_url)
        name = apiclient.getUser()
        bins = list(set(self.settings.local_settings.get("my_commands",{}).values()))
        print("REGISTER "+str(name))
        print("KNOWNS BINS "+str(bins))
        self.sio.emit("register", {"name":name, "binaries":bins})
        @self.sio.event
        def executeCommand(data):
            print("GOT EXECUTE "+str(data))
            logger.debug("Got execute "+str(data))
            toolId = data.get("toolId")
            infos = data.get("infos")
            tool = Tool.fetchObject({"_id":ObjectId(toolId)})
            if tool is None:
                logger.debug("Local worker scan was requested but tool not found : "+str(toolId))
                return
            logger.debug("Local worker launch task: tool  "+str(toolId))
            self.launchTask(tool, True, apiclient.getUser(), infos=infos)

        @self.sio.event
        def stopCommand(data):
            logger.debug("Got stop "+str(data))
            toolId = data.get("toolId")
            self.stopTask(toolId)

        @self.sio.event
        def getProgress(data): 
            print("Get Progress "+str(data))
            logger.debug("get progress "+str(data))
            toolId = data.get("tool_iid")
            msg = self.getToolProgress(toolId)
            print(msg)
            self.sio.emit("getProgressResult", {"result":msg})
        
        
        timer = threading.Timer(5.0, self.beacon)
        timer.start()
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
            