import multiprocessing
import threading
import socketio
from bson import ObjectId
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.models.tool import Tool
from pollenisatorgui.autoscanworker import executeTool
from pollenisatorgui.core.components.logger_config import logger

class ScanWorker:

    def __init__(self, settings):
        self.settings = settings
        self.sio = socketio.Client()
        self.timer = None
        self.local_scans = dict()

    def wait(self):
        self.sio.wait() 
        
    def connect(self, name):
        self.name = name
        apiclient = APIClient.getInstance()
        self.sio.connect(apiclient.api_url)
        plugins = list(set(self.settings.local_settings.get("my_commands",{}).keys()))
        print("REGISTER "+str(self.name))
        print("supported plugins "+str(plugins))
        self.sio.emit("register", {"name":self.name, "supported_plugins":plugins})
        self.timer = threading.Timer(5.0, self.beacon)
        self.timer.start()
        @self.sio.event
        def executeCommand(data):
            print("GOT EXECUTE "+str(data))
            workerToken = data.get("workerToken")
            pentest = data.get("pentest", "")
            apiclient = APIClient.getInstance()
            apiclient.setConnection(workerToken, pentest)
            toolId = data.get("toolId")
            infos = data.get("infos")
            tool = Tool.fetchObject({"_id":ObjectId(toolId)})
            if tool is None:
                print("Local worker scan was requested but tool not found : "+str(toolId))
                return
            print("Local worker launch task: tool  "+str(toolId))
            self.launchTask(tool, True, self.name, infos=infos)

        @self.sio.event
        def stopCommand(data):
            print("Got stop "+str(data))
            toolId = data.get("tool_iid")
            self.stopTask(toolId)

        @self.sio.event
        def getProgress(data): 
            print("get progress "+str(data))
            toolId = data.get("tool_iid")
            msg = self.getToolProgress(toolId)
            print(msg)
            self.sio.emit("getProgressResult", {"result":msg})

        @self.sio.event
        def deleteWorker(data=None):
            i = 0
            for running in self.local_scans.values():
                running[0].terminate()
                running[0].join()
                break
            self.sio.disconnect()
            if self.timer:
                self.timer.cancel()

    def beacon(self):
        if self.sio.connected:
            self.sio.emit("keepalive", {"name":self.name, "running_tasks":[str(x) for x in self.local_scans]})
            self.timer = threading.Timer(5.0, self.beacon)
            self.timer.start()
            
    def onClosing(self):
        if self.timer:
            self.timer.cancel()
            i = 0
            for running in self.local_scans.values():
                running[0].terminate()
                running[0].join()
                break
            self.sio.disconnect()
            if self.timer:
                self.timer.cancel()

    def launchTask(self, toolModel, checks=True, worker="", infos={}):
        apiclient = APIClient.getInstance()
        launchableToolId = toolModel.getId()
        for item in list(self.local_scans.keys()):
            process_info = self.local_scans.get(item, None)
            if process_info is not None and not process_info[0].is_alive():
                print("Proc finished : "+str(self.local_scans[item]))
                try:
                    del self.local_scans[item]
                except KeyError as e:
                    pass

        #if worker == "" or worker == "localhost" or worker == apiclient.getUser():
        scan = self.local_scans.get(str(launchableToolId), None)
        if scan is not None:
            if scan[0].is_alive() and str(scan[0].pid) != "":
                return
            else:
                del self.local_scans[str(launchableToolId)]
                scan = None

        print("Launch task (start process) , local worker , for tool "+str(toolModel.getId()))
        thread = None
        queue = multiprocessing.Queue()
        queueResponse = multiprocessing.Queue()
        thread = multiprocessing.Process(target=executeTool, args=(queue, queueResponse, apiclient, str(launchableToolId), True, False, (worker == apiclient.getUser()), infos, logger,worker))
        thread.start()
        self.local_scans[str(launchableToolId)] = (thread, queue, queueResponse, toolModel)
        print('Local tool launched '+str(toolModel.getId()))
        # else:
        #     print('laucnh task, send remote tool launch '+str(toolModel.getId()))
        #     apiclient.sendQueueTasks(toolModel.getId())

    def stopTask(self, toolId):
        thread, queue, queueResponse, toolModel = self.local_scans.get(str(toolId), (None, None, None, None))
        if thread is None:
            return False
        try:
            thread.terminate()
        except:
            pass
        try:
            del self.local_scans[str(toolId)]
        except KeyError:
            toolModel.markAsNotDone()
        return True
    
    def getToolProgress(self, toolId):
        thread, queue, queueResponse, toolModel = self.local_scans.get(str(toolId), (None, None,None,None))
        if thread is None or queue is None:
            return ""
        progress = ""
        if not queueResponse.empty():
            progress = queueResponse.get()
            return progress
        if not thread.is_alive():
            return True
        return False
    
    
    def is_local_launched(self, toolId):
        return self.local_scans.get(str(toolId), None) is not None