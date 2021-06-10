import json
import requests
import os
import io
from datetime import datetime
import sys
import core.Components.Utils as Utils
from bson import ObjectId
from core.Components.Utils import JSONEncoder, JSONDecoder
from shutil import copyfile
from jose import jwt, JWTError

proxies = {"http":"http://127.0.0.1:8080", "https":"https://127.0.0.1:8080"}
proxies = {}
dir_path = os.path.dirname(os.path.realpath(__file__))  # fullpath to this file
config_dir = os.path.join(dir_path, "./../../config/")
if not os.path.isfile(os.path.join(config_dir, "client.cfg")):
    if os.path.isfile(os.path.join(config_dir, "clientSample.cfg")):
        copyfile(os.path.join(config_dir, "clientSample.cfg"), os.path.join(config_dir, "client.cfg"))
configClientPath = os.path.join(config_dir, "client.cfg")
if os.path.isfile(configClientPath):
    cfg = Utils.loadCfg(configClientPath)
else:
    print("No client config file found under "+str(config_dir))
    sys.exit(1)



class APIClient():
    __instances = dict()

    @staticmethod
    def getInstance():
        """ Singleton Static access method.
        """
        pid = os.getpid()  # HACK : One api client per process.
        instance = APIClient.__instances.get(pid, None)
        if instance is None:
            APIClient()
        return APIClient.__instances[pid]
    
    @staticmethod
    def setInstance(apiclient):
        """ Set singleton for current pid"""
        pid = os.getpid()
        APIClient.__instances[pid] = apiclient

    @staticmethod
    def searchDefect(searchTerms):
        apiclient = APIClient.getInstance()
        api_url = '{0}report/search'.format(apiclient.api_url_base)
        response = requests.get(api_url, params={"type":"defect", "q":searchTerms}, headers=apiclient.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder), ""
        elif response.status_code == 204:
            return None, "There is no external knowledge database to query. Check documentation if you have one ready."
        else:
            return None, "Unexpected server response "+str(response.status_code)+"\n"+response.text    

    @staticmethod
    def searchRemark(searchTerms):
        apiclient = APIClient.getInstance()
        api_url = '{0}report/search'.format(apiclient.api_url_base)
        response = requests.get(api_url, params={"type":"remark", "q":searchTerms}, headers=apiclient.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder), ""
        elif response.status_code == 204:
            return None, "There is no external knowledge database to query. Check documentation if you have one ready."
        else:
            return None, "Unexpected server response "+str(response.status_code)+"\n"+response.text    

    def __init__(self):
        pid = os.getpid()  # HACK : One mongo per process.
        if APIClient.__instances.get(pid, None) is not None:
            raise Exception("This class is a singleton!")
        self.currentPentest = None
        self._observers = []
        self.scope = []
        self.userConnected = None
        APIClient.__instances[pid] = self
        self.headers = {'Content-Type': 'application/json'}
        host = cfg.get("host")
        if host is None:
            raise KeyError("config/client.cfg : missing API host value")
        port = cfg.get("port")
        if port is None:
            raise KeyError("config/client.cfg : missing API port value")
        http_proto = "https" if cfg.get("https", True) else "http"
        self.api_url_base = http_proto+"://"+host+":"+str(port)+"/api/v1/"

    def tryConnection(self, config=None):
        if config is None:
            if os.path.isfile(configClientPath):
                config = Utils.loadCfg(configClientPath)
        if config is None:
            raise FileNotFoundError(str(configClientPath)+" does not exist")
        try:
            http_proto = "https" if cfg.get("https", True) else "http"
            host = config.get("host")
            port = config.get("port")
            self.api_url_base = http_proto+"://"+host+":"+str(port)+"/api/v1/"
            response = requests.get(self.api_url_base, headers=self.headers, proxies=proxies, verify=False)
        except requests.exceptions.RequestException as e:
            return False
        return response.status_code == 200
    
    def reportError(self, err):
        api_url = '{0}issue'.format(self.api_url_base)
        requests.post(api_url, headers=self.headers, data=json.dumps({"error":err}), proxies=proxies, verify=False)
        

    def isConnected(self):
        return self.headers.get("Authorization", "") != ""
    
    def isAdmin(self):
        return "admin" in self.scope

    def getUser(self):
        return self.userConnected
    
    def disconnect(self):
        self.scope = []
        self.userConnected = None
        try:
            del self.headers["Authorization"]
        except KeyError:
            pass

    def login(self, username, passwd):
        api_url = '{0}login'.format(self.api_url_base)
        data = {"username":username, "pwd":passwd}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            token = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            self.headers["Authorization"] = "Bearer "+token
            try:
                jwt_decoded = jwt.decode(token, "", options={"verify_signature":False})
                self.scope = jwt_decoded["scope"]
                self.userConnected = username
            except JWTError as e:
                return False
        return response.status_code == 200
    
    def setCurrentPentest(self, newCurrentPentest):
        if newCurrentPentest.strip() == "":
            self.headers["Authorization"] = ""
            self.scope = []
            self.currentPentest = ""
            return False
        api_url = '{0}login/{1}'.format(self.api_url_base, newCurrentPentest)
        response = requests.post(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            token = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            self.headers["Authorization"] = "Bearer "+token
            try:
                jwt_decoded = jwt.decode(token, "", options={"verify_signature":False})
                self.scope = jwt_decoded["scope"]
            except JWTError as e:
                return False
            self.currentPentest = newCurrentPentest
            return True
        return False
        

    def getCurrentPentest(self):
        return self.currentPentest

    def unregisterWorker(self, worker_name):
        api_url = '{0}workers/{1}/unregister'.format(self.api_url_base, worker_name)
        response = requests.post(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def setWorkerInclusion(self, worker_name, setInclusion):
        api_url = '{0}workers/{1}/setInclusion'.format(self.api_url_base, worker_name)
        data = {"db":self.getCurrentPentest(), "setInclusion":setInclusion}
        response = requests.put(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def getRegisteredCommands(self, workerName):
        api_url = '{0}workers/{1}/getRegisteredCommands'.format(self.api_url_base, workerName)
        response = requests.get(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def registeredCommands(self, workerName, commandNames):
        api_url = '{0}workers/{1}/registerCommands'.format(self.api_url_base, workerName)
        response = requests.put(api_url, headers=self.headers, data=json.dumps(commandNames, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def reinitConnection(self):
        self.setCurrentPentest("")

    def attach(self, observer):
        """
        Attach an observer to the database. All attached observers will be notified when a modication is done to a calendar through the methods presented below.

        Args:
            observer: the observer that implements a notify(collection, iid, action) function
        """
        self._observers.append(observer)

    def dettach(self, observer):
        """
        Dettach the given observer from the database.

        Args:
            observer: the observer to detach
        """
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def fetchNotifications(self, pentest, fromTime):
        api_url = '{0}notification/{1}'.format(self.api_url_base, pentest)
        response = requests.get(api_url, headers=self.headers, params={"fromTime":fromTime}, proxies=proxies, verify=False)
        if response.status_code == 200:
            notifications = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return notifications
        else:
            return []

    def getPentestList(self):
        api_url = '{0}pentests'.format(self.api_url_base)
        response = requests.get(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None
    
    def doDeletePentest(self, pentest):
        api_url = '{0}pentest/{1}/delete'.format(self.api_url_base, pentest)
        response = requests.delete(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def registerPentest(self, pentest, pentest_type, start_date, end_date, scope, settings, pentesters):
        api_url = '{0}pentest/{1}'.format(self.api_url_base, pentest)
        data = {"pentest_type":str(pentest_type), "start_date":start_date, "end_date":end_date, "scope":scope, "settings":settings, "pentesters":pentesters}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return True, "Success"
        else:
            return False, json.loads(response.content.decode('utf-8'), cls=JSONDecoder)

    def find(self, collection, pipeline=None, multi=True):
        return self.findInDb(self.getCurrentPentest(), collection, pipeline, multi)
        
    def findInDb(self, pentest, collection, pipeline=None, multi=True):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}find/{1}/{2}'.format(self.api_url_base, pentest, collection)
        data = {"pipeline":(json.dumps(pipeline, cls=JSONEncoder)), "many":multi}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder),  proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def insert(self, collection, data):
        api_url = '{0}{1}/{2}'.format(self.api_url_base, collection, self.getCurrentPentest())
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder),  proxies=proxies, verify=False)
        res = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return res["res"], res["iid"]
        
    def insertInDb(self, pentest, collection, pipeline=None, parent="", notify=False):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}insert/{1}/{2}'.format(self.api_url_base, pentest, collection)
        data = {"pipeline":json.dumps(pipeline, cls=JSONEncoder), "parent":parent, "notify":notify}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def update(self, collection, iid, updatePipeline):
        api_url = '{0}{1}/update/{2}/{3}'.format(self.api_url_base, collection, self.getCurrentPentest(), iid)
        response = requests.put(api_url, headers=self.headers,data=json.dumps(updatePipeline, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None
                
    def updateInDb(self, pentest, collection, pipeline, updatePipeline, many=False, notify=False):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}update/{1}/{2}'.format(self.api_url_base, pentest, collection)
        data = {"pipeline":json.dumps(pipeline, cls=JSONEncoder), "updatePipeline":json.dumps(updatePipeline, cls=JSONEncoder), "many":many, "notify":notify}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def delete(self, collection, iid):
        api_url = '{0}{1}/{2}/{3}'.format(self.api_url_base, collection, self.getCurrentPentest(), iid)
        response = requests.delete(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def bulkDelete(self, dictToDelete):
        api_url = '{0}delete/{1}/bulk'.format(self.api_url_base, self.getCurrentPentest())
        data = dictToDelete
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), verify=False, proxies=proxies)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None
        
    def deleteFromDb(self, pentest, collection, pipeline, many=False, notify=False):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}delete/{1}/{2}'.format(self.api_url_base, pentest, collection)
        data = {"pipeline":json.dumps(pipeline, cls=JSONEncoder), "many":many, "notify":notify}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def aggregate(self, collection, pipelines=None):
        pipelines = [] if pipelines is None else pipelines
        api_url = '{0}aggregate/{1}/{2}'.format(self.api_url_base, self.getCurrentPentest(), collection)
        data = pipelines
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def count(self, collection, pipeline=None):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}count/{1}/{2}'.format(self.api_url_base, self.getCurrentPentest(), collection)
        data = {"pipeline":json.dumps(pipeline, cls=JSONEncoder)}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return 0

    def getWorkers(self, pipeline=None):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}workers'.format(self.api_url_base)
        data = {"pipeline":json.dumps(pipeline, cls=JSONEncoder)}
        response = requests.get(api_url, headers=self.headers, params=data, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code == 204:
            return []
    
    def getWorker(self, pipeline=None):
        res = self.getWorkers(pipeline)
        if res is not None:
            if len(res) == 1:
                return res[0]
        return None

    def sendEditToolConfig(self, worker, command_name, remote_bin, plugin):
        api_url = '{0}workers/{1}/setCommandConfig'.format(self.api_url_base, worker)
        data = {"command_name":command_name, "remote_bin":remote_bin, "plugin":plugin}
        response = requests.put(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def getSettings(self, pipeline=None):
        if pipeline is None:
            api_url = '{0}settings'.format(self.api_url_base)
            params={}
        else:
            api_url = '{0}settings/search'.format(self.api_url_base)
            params = {"pipeline":json.dumps(pipeline, cls=JSONEncoder)}
        response = requests.get(api_url, headers=self.headers, params=params, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code == 404:
            return []
        else:
            return None

    def createSetting(self, key, value):
        api_url = '{0}settings/add'.format(self.api_url_base)
        data = {"key":key, "value":json.dumps(value)}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None
    
    def updateSetting(self, key, value):
        api_url = '{0}settings/update'.format(self.api_url_base)
        data = {"key":key, "value":json.dumps(value)}
        response = requests.put(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def sendStopTask(self, tool_iid, forceReset=False):
        api_url = '{0}tools/{1}/stopTask/{2}'.format(self.api_url_base, self.getCurrentPentest(), tool_iid)
        data = {"forceReset":forceReset}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return False

    def sendLaunchTask(self, tool_iid, plugin="", checks=True, worker=""):
        api_url = '{0}tools/{1}/launchTask/{2}'.format(self.api_url_base, self.getCurrentPentest(), tool_iid)
        data = {"checks":checks, "plugin":plugin}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def addCustomTool(self, port_iid, tool_name):
        api_url = '{0}ports/{1}/{2}/addCustomTool/'.format(self.api_url_base, self.getCurrentPentest(), port_iid)
        response = requests.post(api_url, headers=self.headers, data=json.dumps({"tool_name":tool_name}, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        else:
            return None

    def putProof(self, defect_iid, local_path):
        api_url = '{0}files/{1}/upload/proof/{2}'.format(self.api_url_base, self.getCurrentPentest(), defect_iid)
        with open(local_path,'rb') as f:
            h = self.headers
            del h["Content-Type"]
            response = requests.post(api_url, files={"upfile": (os.path.basename(local_path) ,f)}, headers=h, proxies=proxies, verify=False)
            if response.status_code == 200:
                return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return None

    def listProofs(self, defect_iid):
        api_url = '{0}files/{1}/download/proof/{2}'.format(self.api_url_base, self.getCurrentPentest(), defect_iid)
        response = requests.get(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return []

    def getResult(self, tool_iid, local_path):
        resultfile = self.getFileName("result", tool_iid)
        if resultfile is not None:
            return self._get("result", tool_iid, resultfile, local_path)
        return None
    

    def getProof(self, defect_iid, filename, local_path):
        return self._get("proof", defect_iid, filename, local_path)

    def getFileName(self, filetype, attached_iid):
        """Retrieve the list of filenames attached to a toolid
        Args:
            filetype: 'result' or 'proof' 
            attached_iid: tool or defect iid depending on filetype
        Returns : filename: remote file file name
        """
        api_url = '{0}files/{1}/download/{2}/{3}'.format(self.api_url_base, self.getCurrentPentest(), filetype, str(attached_iid))
        response = requests.get(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            ret = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            if isinstance(ret, list) and ret:
                return ret[0]
        return None

    def _get(self, filetype, attached_iid, filename, local_path):
        """Download file affiliated with given iid and place it at given path
        Args:
            filetype: 'result' or 'proof' 
            attached_iid: tool or defect iid depending on filetype
            filename: remote file file name
            local_path: local file path
        """
        api_url = '{0}files/{1}/download/{2}/{3}/{4}'.format(self.api_url_base, self.getCurrentPentest(), filetype, attached_iid, filename)
        response = requests.get(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            if not os.path.exists(local_path):
                os.makedirs(local_path)
            local_path = os.path.join(local_path, filename)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            return local_path
        return None

    def rmProof(self, defect_iid, filename):
        """Remove file affiliated with given iid 
        """
        api_url = '{0}files/{1}/{2}/{3}'.format(self.api_url_base, self.getCurrentPentest(), defect_iid, filename)
        response = requests.delete(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return None

    def getCommandline(self, toolId, parser=""):
        """Get full command line from toolid and choosen parser, a marker for |outputDir| is to be replaced
        """
        api_url = '{0}tools/{1}/craftCommandLine/{2}'.format(self.api_url_base, self.getCurrentPentest(), toolId)
        response = requests.get(api_url, headers=self.headers, params={"plugin":parser}, proxies=proxies, verify=False)
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return True, data["comm"], data["ext"], data["bin"]
        return False, response.content.decode('utf-8'), "", ""
    
    def importToolResult(self, tool_iid, parser, local_path):
        api_url = '{0}tools/{1}/importResult/{2}'.format(self.api_url_base, self.getCurrentPentest(), tool_iid)
        if not os.path.isfile(local_path):
            return "Failure to open provided file"
        with io.open(local_path, 'r', encoding='utf-8', errors="ignore") as f:
            h = self.headers
            del h["Content-Type"]
            response = requests.post(api_url, files={"upfile": (os.path.basename(local_path) ,f)}, data={"plugin":parser}, headers=h, proxies=proxies, verify=False)
            if response.status_code == 200:
                return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return response.content.decode('utf-8')

    def setToolStatus(self, toolmodel, newStatus, arg=""):
        api_url = '{0}tools/{1}/{2}/changeStatus'.format(self.api_url_base, self.getCurrentPentest(), toolmodel.getId())
        response = requests.post(api_url, headers=self.headers, data=json.dumps({"newStatus":newStatus, "arg":arg}), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return None
    def importExistingResultFile(self, filepath, plugin):
        api_url = '{0}files/{1}/import'.format(self.api_url_base, self.getCurrentPentest())
        with io.open(filepath, 'r', encoding='utf-8', errors="ignore") as f:
            response = requests.post(api_url, headers=self.headers, files={"upfile": (os.path.basename(filepath) ,f)}, data={"plugin":plugin}, proxies=proxies, verify=False)
            if response.status_code == 200:
                return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)

    def fetchWorkerInstruction(self, worker_name):
        api_url = '{0}workers/{1}/instructions'.format(self.api_url_base, worker_name)
        response = requests.get(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return data
        return None
    
    def deleteWorkerInstruction(self, worker_name, instruction_iid):
        api_url = '{0}workers/{1}/instructions/{2}'.format(self.api_url_base, worker_name, instruction_iid)
        response = requests.delete(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return data
        return None

    def sendStartAutoScan(self):
        api_url = '{0}autoscan/{1}/start'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.post(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return None
    
    def sendStopAutoScan(self):
        api_url = '{0}autoscan/{1}/stop'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.post(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return None

    def getAutoScanStatus(self):
        api_url = '{0}autoscan/{1}/status'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.get(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return None        

    def dumpDb(self, pentest, collection=""):
        api_url = '{0}dumpDb/{1}'.format(self.api_url_base, pentest)
        response = requests.get(api_url, headers=self.headers, params={"collection":collection}, proxies=proxies, verify=False)
        if response.status_code == 200:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            out_path = os.path.join(
                dir_path, "../../exports/", pentest if collection == "" else pentest+"_"+collection)+".gz"
            with open(out_path, 'wb') as f:
                f.write(response.content)
                return True, out_path
        return False, response.text      
    
    def importDb(self, filename):
        api_url = '{0}importDb'.format(self.api_url_base)
        with io.open(filename, 'r', encoding='utf-8', errors="ignore") as f:
            h = self.headers
            del h["Content-Type"]
            response = requests.post(api_url, headers=h, files={"upfile": (os.path.basename(filename) ,f)}, proxies=proxies, verify=False)
            return response.status_code == 200
        return False
    
    def importCommands(self, filename):
        api_url = '{0}importCommands'.format(self.api_url_base)
        with io.open(filename, 'r', encoding='utf-8', errors="ignore") as f:
            h = self.headers
            del h["Content-Type"]
            response = requests.post(api_url, headers=h, files={"upfile": (os.path.basename(filename) ,f)}, proxies=proxies, verify=False)
            return response.status_code == 200
        return False

    def copyDb(self, fromDb, toDb=""):
        api_url = '{0}copyDb'.format(self.api_url_base)
        data = {"fromDb":self.getCurrentPentest(), "toDb":toDb}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return None

    
    
    def generateReport(self, templateName, clientName, contractName, mainRedac):
        api_url = '{0}report/{1}/generate'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.get(api_url, headers=self.headers, params={"templateName":templateName, "contractName":contractName, "clientName":clientName, "mainRedactor":mainRedac}, proxies=proxies, verify=False)
        if response.status_code == 200:
            timestr = datetime.now().strftime("%Y%m%d-%H%M%S")
            ext = os.path.splitext(templateName)[-1]
            basename = clientName.strip()+"_"+contractName.strip()
            out_name = str(timestr)+"_"+basename
            out_path = os.path.join(dir_path, "../../exports/",out_name+ext)
            with open(out_path, 'wb') as f:
                f.write(response.content)
                return os.path.normpath(out_path)
        return response.content.decode("utf-8")

    def getTemplateList(self):
        api_url = '{0}report/templates'.format(self.api_url_base)
        try:
            response = requests.get(api_url, headers=self.headers, proxies=proxies, verify=False)
        except ConnectionError as e:
            raise e
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return []
    
    def downloadTemplate(self, templateName):
        api_url = '{0}report/templates/download'.format(self.api_url_base)
        response = requests.get(api_url, headers=self.headers, params={"templateName":templateName},proxies=proxies, verify=False)
        if response.status_code == 200:
            out_path = os.path.join(dir_path, "../../exports/",templateName)
            with open(out_path, 'wb') as f:
                f.write(response.content)
                return os.path.normpath(out_path)
        return None

    def getDefectTable(self):
        api_url = '{0}report/{1}/defects'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.get(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return []

    def moveDefect(self, defect_id, target_id):
        api_url = '{0}report/{1}/defects/move/{2}/{3}'.format(self.api_url_base, self.getCurrentPentest(), defect_id, target_id)
        response = requests.post(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return response.content.decode("utf-8")


    def getUsers(self):
        api_url = '{0}admin/listUsers'.format(self.api_url_base)
        response = requests.get(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return []

    def searchUsers(self, username):
        api_url = '{0}user/searchUsers/{1}'.format(self.api_url_base, username)
        response = requests.get(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return []

    def registerUser(self, username, password):
        api_url = '{0}user/register'.format(self.api_url_base)
        response = requests.post(api_url, headers=self.headers, data=json.dumps({"username":username, "pwd":password}), proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return None

    def deleteUser(self, username):
        api_url = '{0}user/delete/{1}'.format(self.api_url_base, username)
        response = requests.delete(api_url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        return None

    def changeUserPassword(self, oldPwd, newPwd):
        api_url = '{0}user/changePassword'.format(self.api_url_base)
        response = requests.post(api_url, headers=self.headers, data=json.dumps({"oldPwd":oldPwd, "newPwd":newPwd}), proxies=proxies, verify=False)
        if response.status_code == 200:
            return ""
        return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)

    def resetPassword(self, username, newPwd):
        api_url = '{0}admin/resetPassword'.format(self.api_url_base)
        response = requests.post(api_url, headers=self.headers, data=json.dumps({"username":username, "newPwd":newPwd}), proxies=proxies, verify=False)
        if response.status_code == 200:
            return ""
        return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)