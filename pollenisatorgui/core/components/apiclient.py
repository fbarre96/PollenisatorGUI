import json
import multiprocessing
import requests
import os
import io
from datetime import datetime
import sys
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.components.utils import JSONEncoder, JSONDecoder, saveClientConfig
from shutil import copyfile
from jose import jwt, JWTError
from functools import wraps
from bson import ObjectId
import tkinter as tk


dir_path = os.path.dirname(os.path.realpath(__file__))  # fullpath to this file
config_dir = utils.getConfigFolder()
sample_file = os.path.join(utils.getMainDir(), "config/clientSample.cfg")
configClientPath = os.path.join(config_dir, "client.cfg")
if not os.path.isfile(configClientPath):
    if os.path.isfile(sample_file):
        try:
            os.makedirs(config_dir)
        except:
            pass
        copyfile(sample_file, configClientPath)
if os.path.isfile(configClientPath):
    cfg = utils.loadClientConfig()
else:
    print("No client config file found under "+str(configClientPath))
    sys.exit(1)

class ErrorHTTP(Exception):
    def __init__(self, response, *args):
        self.response = response
        self.ret_values = args if args else None

def handle_api_errors(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            res = func(self, *args, **kwargs)
        except requests.exceptions.ProxyError:
            cfg = utils.loadClientConfig()
            cfg["proxies"] = ""
            saveClientConfig(cfg)
            return None
        except requests.exceptions.ConnectionError:
            cfg = utils.loadClientConfig()
            cfg["host"] = ""
            saveClientConfig(cfg)
            return None
        except requests.exceptions.InvalidURL:
            cfg = utils.loadClientConfig()
            cfg["host"] = ""
            saveClientConfig(cfg)
            return None
        except ErrorHTTP as err:
            if err.response.status_code == 401:
                cfg = utils.loadClientConfig()
                cfg["token"] = ""
                saveClientConfig(cfg)
                if "Authorization" in self.headers:
                    del self.headers["Authorization"] 
                err.with_traceback = False
                if self.appli is None:
                    return err.ret_values
                if self.appli.initialized:
                    raise err
                else:
                    return err.ret_values
            elif err.response.status_code == 500:
                raise err
            else:
                if isinstance(err.ret_values, tuple) and len(err.ret_values) == 1:
                    return err.ret_values[0]
                return err.ret_values
        return res
    return wrapper

def call_with_timeout(func, args, kwargs, timeout):
    manager = multiprocessing.Manager()
    return_dict = manager.dict()

    # define a wrapper of `return_dict` to store the result.
    def function(return_dict):
        try:
            return_dict['value'] = func(*args, **kwargs)
        except Exception as e:
            return None

    p = multiprocessing.Process(target=function, args=(return_dict,))
    p.start()

    # Force a max. `timeout` or wait for the process to finish
    p.join(timeout)

    # If thread is still active, it didn't finish: raise TimeoutError
    if p.is_alive():
        p.terminate()
        p.join()
        raise TimeoutError
    else:
        try:
            return return_dict['value']
        except KeyError:
            return None

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
    
   

    def searchDefect(self, searchTerms, **kwargs):
        api_url = '{0}report/search'.format(self.api_url_base)
        data = {"type":"defect", "terms":searchTerms, "language":kwargs.get('lang', ""), "perimeter":kwargs.get('perimeter', "")}
        #check_api = kwargs.get('check_api', None)
        #if check_api is not None:
        #    data["check_api"] = check_api
        response = requests.post(api_url, data=json.dumps(data), headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            res_obj = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return res_obj["answers"], "\n".join(res_obj["errors"])
        else:
            return None, "Unexpected server response "+str(response.status_code)+"\n"+response.text    

    def searchRemark(self, searchTerms, **kwargs):
        api_url = '{0}report/search'.format(self.api_url_base)
        response = requests.post(api_url, data=json.dumps({"type":"remark", "terms":searchTerms, "remark_type":kwargs.get("remark_type", "")}), headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            res_obj = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return res_obj["answers"], "\n".join(res_obj["errors"])
        elif response.status_code == 204:
            return None, "There is no external knowledge database to query. Check documentation if you have one ready."
        else:
            return None, "Unexpected server response "+str(response.status_code)+"\n"+response.text    

    def __init__(self):
        pid = os.getpid()  # HACK : One mongo per process.
        if APIClient.__instances.get(pid, None) is not None:
            raise Exception("This class is a singleton!")
        self.currentPentest = ""
        self.currentPentestName = ""
        self._observers = []
        self.scope = []
        self.userConnected = None
        self.appli = None
        APIClient.__instances[pid] = self
        self.headers = {'Content-Type': 'application/json'}
        host = cfg.get("host")
        if host is None:
            raise KeyError("config/client.cfg : missing API host value")
        port = cfg.get("port")
        if port is None:
            raise KeyError("config/client.cfg : missing API port value")
        http_proto = "https" if str(cfg.get("https", "True")).title() == "True" else "http"
        self.proxies = cfg.get("proxies", "")
        if isinstance(self.proxies, str):
            self.proxies = {"http": self.proxies, "https": self.proxies}

        self.api_url = http_proto+"://"+host+":"+str(port)+"/"
        self.api_url_base = http_proto+"://"+host+":"+str(port)+"/api/v1/"

    def tryConnection(self, config=None, force=False):
        if config is None:
            config = utils.loadClientConfig()
        if config is None:
            raise FileNotFoundError(str(configClientPath)+" does not exist")
        try:
            is_https = config.get("https", True)
            http_proto = "https" if str(is_https).lower() == "true" or is_https == 1 else "http"
            host = config.get("host")
            port = config.get("port")
            proxies = config.get("proxies", "")
            if isinstance(proxies, str):
                if proxies == "":
                    proxies = {}
                else:
                    proxies = {"http": proxies, "https": proxies}
            self.proxies = proxies
            token = None
            if not force:
                token = config.get("token", None)
            self.api_url = http_proto+"://"+host+":"+str(port)+"/"
            self.api_url_base = http_proto+"://"+host+":"+str(port)+"/api/v1/"
            # requests timeout does not work when the DNS does not respond. So we use a thread to do the request and kill it if it takes too long.
            response = call_with_timeout(requests.get, args=(self.api_url_base,), kwargs={"headers":self.headers, "proxies":self.proxies, "verify":False}, timeout=2)
        except requests.exceptions.RequestException as e:
            return False
        except TimeoutError as e:
            return False
        if response is None:
            return False
        if response.status_code == 200:
            saveClientConfig(config)
            import pollenisatorgui.core.components.settings as settings
            s = settings.Settings()
            if self.api_url not in [x["url"] for x in s.local_settings.get("hosts", [])]:
                s.local_settings["hosts"] = [{"url":self.api_url, "proto":http_proto,"port":port, "host":host}] + s.local_settings.get("hosts", [])
                s.saveLocalSettings()
            self.proxies = proxies
            if token:
                return self.setConnection(token)
        return response.status_code == 200
    
    def tryAuth(self):
        try:
            res = self.setCurrentPentest(self.getCurrentPentest())
        except Exception as e:
            #relog
            return False
        return res

    def reportError(self, err):
        api_url = '{0}issue'.format(self.api_url_base)
        requests.post(api_url, headers=self.headers, data=json.dumps({"error":err}), proxies=self.proxies, verify=False)
        

    def isConnected(self):
        return self.headers.get("Authorization", "") != ""

    
    
    def isAdmin(self):
        return "admin" in self.scope

    def getUser(self):
        return self.userConnected
    
    def disconnect(self):
        self.scope = []
        self.userConnected = None
        self.token = ""
        client_config = utils.loadClientConfig()
        client_config["token"] = self.token
        utils.saveClientConfig(client_config)
        try:
            del self.headers["Authorization"]
        except KeyError:
            pass

    def setConnection(self, token, name=""):
        try:
            jwt_decoded = jwt.decode(token, "", options={"verify_signature":False})
            self.scope = jwt_decoded["scope"]
            self.userConnected = jwt_decoded.get("sub", None)
            self.token = token
            self.headers["Authorization"] = "Bearer "+token
            self.currentPentest = ""
            self.currentPentestName = ""
            for scope in self.scope:
                if scope not in ["pentester", "admin", "user", "owner", "worker"]:
                    self.currentPentest = scope
                    self.currentPentestName = name
            client_config = utils.loadClientConfig()
            client_config["token"] = self.token
            utils.saveClientConfig(client_config)
            
        except JWTError as e:
            return False
        return True

    def getToken(self):
        return self.token

    def login(self, username, passwd):
        api_url = '{0}login'.format(self.api_url_base)
        data = {"username":username, "pwd":passwd}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            token = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return self.setConnection(token)
        return response.status_code == 200

    @handle_api_errors
    def getVersion(self):
        api_url = '{0}version'.format(self.api_url_base)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            version = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return version
        raise ErrorHTTP(response)
    
    @handle_api_errors
    def setCurrentPentest(self, newCurrentPentest, addDefaultCommands=False):
        if newCurrentPentest.strip() == "":
            self.headers["Authorization"] = ""
            self.scope = []
            self.currentPentest = ""
            self.currentPentestName = ""
            return False
        api_url = '{0}login/{1}'.format(self.api_url_base, newCurrentPentest)
        data = {"addDefaultCommands": addDefaultCommands}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            body = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            token = body["token"]
            pentest_name = body["pentest_name"]
            self.setConnection(token, pentest_name)
            return True
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False)
        
        return False

    def getCurrentPentest(self):
        return self.currentPentest
    
    def getCurrentPentestName(self):
        return self.currentPentestName

    @handle_api_errors
    def unregisterWorker(self, worker_name):
        api_url = '{0}workers/{1}/unregister'.format(self.api_url_base, worker_name)
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def setWorkerInclusion(self, worker_name, setInclusion):
        api_url = '{0}workers/{1}/setInclusion'.format(self.api_url_base, worker_name)
        data = {"db":self.getCurrentPentest(), "setInclusion":setInclusion}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def getRegisteredCommands(self, workerName):
        api_url = '{0}workers/{1}/getRegisteredCommands'.format(self.api_url_base, workerName)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def registeredCommands(self, workerName, commandNames):
        api_url = '{0}workers/{1}/registerCommands'.format(self.api_url_base, workerName)
        response = requests.put(api_url, headers=self.headers, data=json.dumps(commandNames, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def removeCommandFromMyCommands(self, iid):
        api_url = '{0}commands/removeFromMyCommands/{1}'.format(self.api_url_base, iid)
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def addCommandToMyCommands(self, iid):
        api_url = '{0}commands/addToMyCommands/{1}'.format(self.api_url_base, iid)
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def addCommandToWorkerCommands(self, iid):
        api_url = '{0}commands/addToWorkerCommands/{1}'.format(self.api_url_base, iid)
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    def reinitConnection(self):
        self.setCurrentPentest("")

    def attach(self, observer):
        """
        Attach an observer to the database. All attached observers will be notified when a modication is done to a pentest through the methods presented below.

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

    @handle_api_errors
    def fetchNotifications(self, pentest, fromTime):
        api_url = '{0}notification/{1}'.format(self.api_url_base, pentest)
        response = requests.get(api_url, headers=self.headers, params={"fromTime":fromTime}, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            notifications = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return notifications
        else:
            return []

    @handle_api_errors
    def getPentestList(self):
        api_url = '{0}pentests'.format(self.api_url_base)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
    
    @handle_api_errors
    def doDeletePentest(self, pentest):
        api_url = '{0}pentest/{1}/delete'.format(self.api_url_base, pentest)
        response = requests.delete(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
    @handle_api_errors
    def registerPentest(self, pentest, pentest_type, start_date, end_date, scope, settings, pentesters):
        api_url = '{0}pentest/{1}'.format(self.api_url_base, pentest)
        data = {"pentest_type":str(pentest_type), "start_date":start_date, "end_date":end_date, "scope":scope, "settings":settings, "pentesters":pentesters}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return True, json.loads(response.content.decode('utf-8'))
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, json.loads(response.content.decode('utf-8'), cls=JSONDecoder))
        else:
            return False, json.loads(response.content.decode('utf-8'), cls=JSONDecoder)

    @handle_api_errors
    def find(self, collection, pipeline=None, multi=True):
        try:
            return self.findInDb(self.getCurrentPentest(), collection, pipeline, multi)
        except ErrorHTTP as e:
            raise e


    @handle_api_errors
    def findCommand(self, pipeline=None):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}commands/find'.format(self.api_url_base)
        data = {"pipeline":(json.dumps(pipeline, cls=JSONEncoder))}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder),  proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def findCheckItem(self, pipeline=None, many=True):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}cheatsheet/find'.format(self.api_url_base)
        data = {"pipeline":(json.dumps(pipeline, cls=JSONEncoder))}
        data["many"] = many
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder),  proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
    
    @handle_api_errors
    def findCheckInstance(self, pipeline=None, many=True):
        apiclient = APIClient.getInstance()
        pentest = apiclient.getCurrentPentest()
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}find/{1}/checkinstances'.format(self.api_url_base, pentest)
        data = {"pipeline":(json.dumps(pipeline, cls=JSONEncoder))}
        data["many"] = many
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder),  proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def updateCheckInstance(self, iid, updatePipeline):
        apiclient = APIClient.getInstance()
        pentest = apiclient.getCurrentPentest()
        api_url = '{0}cheatsheet/{1}/{2}'.format(self.api_url_base, pentest, str(iid))
        response = requests.put(api_url, headers=self.headers, data=json.dumps(updatePipeline, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
        
    @handle_api_errors
    def multiChangeStatus(self, iids, toStatus):
        apiclient = APIClient.getInstance()
        pentest = apiclient.getCurrentPentest()
        api_url = '{0}cheatsheet/{1}/multiChangeOfStatus'.format(self.api_url_base, pentest)
        data = {"iids":iids, "status":toStatus}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def queueCheckInstances(self, iids, priority=0, force=False):
        apiclient = APIClient.getInstance()
        pentest = apiclient.getCurrentPentest()
        api_url = '{0}cheatsheet/{1}/queueCheckInstances'.format(self.api_url_base, pentest)
        data = {"iids":iids, "priority":priority, "force":force}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
    
    @handle_api_errors
    def updateCheckItem(self, iid, updatePipeline):
        api_url = '{0}cheatsheet/{1}'.format(self.api_url_base, str(iid))
        response = requests.put(api_url, headers=self.headers, data=json.dumps(updatePipeline, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
    
    @handle_api_errors
    def insertCheckItem(self, data):
        api_url = '{0}cheatsheet/'.format(self.api_url_base)
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            res = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return res["res"], res["iid"]
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
        
    @handle_api_errors
    def apply_check_to_pentest(self, check_iid):
        api_url = '{0}cheatsheet/{1}/{2}'.format(self.api_url_base, self.getCurrentPentest(), check_iid)
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            res = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return res["res"]
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def deleteCheckInstance(self, iid):
        apiclient = APIClient.getInstance()
        pentest = apiclient.getCurrentPentest()
        api_url = '{0}cheatsheet/{1}/{2}'.format(self.api_url_base, pentest, str(iid))
        response = requests.delete(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            res = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return res
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def deleteCheckItem(self, iid):
        api_url = '{0}cheatsheet/{1}'.format(self.api_url_base, str(iid))
        response = requests.delete(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            res = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return res
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def deleteCommand(self, command_iid):
        api_url = '{0}commands/delete/{1}'.format(self.api_url_base, command_iid)
        response = requests.delete(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None


    @handle_api_errors    
    def findInDb(self, pentest, collection, pipeline=None, multi=True, use_cache=True):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}find/{1}/{2}'.format(self.api_url_base, pentest, collection)
        data = {"pipeline":(json.dumps(pipeline, cls=JSONEncoder)), "many":multi, "use_cache":use_cache}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder),  proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def insert(self, collection, data):
        api_url = '{0}{1}/{2}'.format(self.api_url_base, collection, self.getCurrentPentest())
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder),  proxies=self.proxies, verify=False)
        if response.status_code == 200:
            res = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return res["res"], res["iid"]
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None


    @handle_api_errors
    def insertInDb(self, pentest, collection, pipeline=None, parent="", notify=False):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}insert/{1}/{2}'.format(self.api_url_base, pentest, collection)
        data = {"pipeline":json.dumps(pipeline, cls=JSONEncoder), "parent":parent, "notify":notify}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def update(self, collection, iid, updatePipeline):
        api_url = '{0}{1}/update/{2}/{3}'.format(self.api_url_base, collection, self.getCurrentPentest(), iid)
        response = requests.put(api_url, headers=self.headers,data=json.dumps(updatePipeline, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def updatePentest(self, pentest_name):
        api_url = '{0}pentest/{1}'.format(self.api_url_base, self.getCurrentPentest())
        data = {"pentest_name":pentest_name}
        response = requests.put(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def updatePentestSetting(self, key_value_dict):
        api_url = '{0}settings/{1}'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.post(api_url, headers=self.headers, data=json.dumps(key_value_dict, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
        
    @handle_api_errors       
    def updateInDb(self, pentest, collection, pipeline, updatePipeline, many=False, notify=False, upsert=False):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}update/{1}/{2}'.format(self.api_url_base, pentest, collection)
        data = {"pipeline":json.dumps(pipeline, cls=JSONEncoder), "updatePipeline":json.dumps(updatePipeline, cls=JSONEncoder), "many":many, "notify":notify, "upsert":upsert}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def delete(self, collection, iid):
        api_url = '{0}{1}/{2}/{3}'.format(self.api_url_base, collection, self.getCurrentPentest(), iid)
        response = requests.delete(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def bulkDelete(self, dictToDelete):
        api_url = '{0}delete/{1}/bulk'.format(self.api_url_base, self.getCurrentPentest())
        data = dictToDelete
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), verify=False, proxies=self.proxies)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def bulkDeleteCommands(self, dictToDelete, forWorker=False):
        api_url = '{0}commands/delete/bulk'.format(self.api_url_base)
        data = dictToDelete
        if forWorker:
            data["Worker"] = True
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), verify=False, proxies=self.proxies)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
    
    @handle_api_errors
    def deleteFromDb(self, pentest, collection, pipeline, many=False, notify=False):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}delete/{1}/{2}'.format(self.api_url_base, pentest, collection)
        data = {"pipeline":json.dumps(pipeline, cls=JSONEncoder), "many":many, "notify":notify}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def aggregate(self, collection, pipelines=None):
        pipelines = [] if pipelines is None else pipelines
        api_url = '{0}aggregate/{1}/{2}'.format(self.api_url_base, self.getCurrentPentest(), collection)
        data = pipelines
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def count(self, collection, pipeline=None):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}count/{1}/{2}'.format(self.api_url_base, self.getCurrentPentest(), collection)
        data = {"pipeline":json.dumps(pipeline, cls=JSONEncoder)}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, 0)
        else:
            return 0

    @handle_api_errors
    def getWorkers(self, pipeline=None):
        pipeline = {} if pipeline is None else pipeline
        api_url = '{0}workers'.format(self.api_url_base)
        data = {"pipeline":json.dumps(pipeline, cls=JSONEncoder)}
        response = requests.get(api_url, headers=self.headers, params=data, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code == 204:
            return []
        elif response.status_code >= 400:
            raise ErrorHTTP(response, [])
    
    @handle_api_errors
    def getWorker(self, pipeline=None):
        res = self.getWorkers(pipeline)
        if res is not None:
            if len(res) == 1:
                return res[0]
        return None

    
    @handle_api_errors
    def getSettings(self, pipeline=None):
        if pipeline is None:
            api_url = '{0}settings'.format(self.api_url_base)
            params={}
        else:
            api_url = '{0}settings/search'.format(self.api_url_base)
            params = {"pipeline":json.dumps(pipeline, cls=JSONEncoder)}
        response = requests.get(api_url, headers=self.headers, params=params, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code == 404:
            return []
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def createSetting(self, key, value):
        api_url = '{0}settings/add'.format(self.api_url_base)
        data = {"key":key, "value":json.dumps(value)}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
    
    @handle_api_errors
    def updateSetting(self, key, value):
        api_url = '{0}settings/update'.format(self.api_url_base)
        data = {"key":key, "value":json.dumps(value)}
        response = requests.put(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def registerTag(self, pentest, name, color):
        api_url = '{0}settings/registerTag'.format(self.api_url_base)
        data = {"name":name, "color":color, "pentest":pentest}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
    
    @handle_api_errors
    def unregisterTag(self,pentest, name):
        api_url = '{0}settings/unregisterTag'.format(self.api_url_base)
        data = {"name":name, "pentest":pentest}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def updateTag(self, name, color, level, isGlobal=False):
        api_url = '{0}settings/updateTag'.format(self.api_url_base)
        if not isGlobal:
            api_url += '/'+self.getCurrentPentest()
        data = {"name":name, "color":color, "level":level, "global":isGlobal}
        response = requests.put(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None


    @handle_api_errors
    def sendStopTask(self, tool_iid, forceReset=False):
        api_url = '{0}tools/{1}/stopTask/{2}'.format(self.api_url_base, self.getCurrentPentest(), tool_iid)
        data = {"forceReset":forceReset}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False,)
        else:
            return False

    @handle_api_errors
    def sendQueueTasks(self, tools_iid):
        if isinstance(tools_iid, str):
            tools_iid = [ObjectId(tools_iid)]
        elif isinstance(tools_iid, ObjectId):
            tools_iid = [tools_iid]
        api_url = '{0}tools/{1}/queueTasks'.format(self.api_url_base, self.getCurrentPentest())
        data = tools_iid
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
        
    @handle_api_errors
    def runTask(self, tool_iid):
        api_url = '{0}tools/{1}/{2}/runTask'.format(self.api_url_base, self.getCurrentPentest(), tool_iid)
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

        
    @handle_api_errors
    def sendRemoveTasks(self, tools_iid):
        if isinstance(tools_iid, str):
            tools_iid = [ObjectId(tools_iid)]
        elif isinstance(tools_iid, ObjectId):
            tools_iid = [tools_iid]
        api_url = '{0}tools/{1}/removeTasks'.format(self.api_url_base, self.getCurrentPentest())
        data = tools_iid
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
        
    @handle_api_errors  
    def getQueue(self):
        api_url = '{0}tools/{1}/getQueue'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
        
    @handle_api_errors
    def clear_queue(self):
        api_url = '{0}tools/{1}/clearTasks'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None


    @handle_api_errors
    def addCustomTool(self, port_iid, command_iid):
        api_url = '{0}ports/{1}/{2}/addCustomTool/'.format(self.api_url_base, self.getCurrentPentest(), port_iid)
        response = requests.post(api_url, headers=self.headers, data=json.dumps({"command_iid":command_iid}, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def putProof(self, defect_iid, local_path):
        api_url = '{0}files/{1}/upload/proof/{2}'.format(self.api_url_base, self.getCurrentPentest(), defect_iid)
        if os.path.exists(local_path) and os.path.isfile(local_path):
            with open(local_path,mode='rb') as f:
                h = self.headers.copy()
                h.pop("Content-Type", None)
                response = requests.post(api_url, files={"upfile": (os.path.basename(local_path) ,f)}, headers=h, proxies=self.proxies, verify=False)
                if response.status_code == 200:
                    return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
                elif response.status_code >= 400:
                    raise ErrorHTTP(response)
        return None

    @handle_api_errors
    def listProofs(self, defect_iid):
        api_url = '{0}files/{1}/download/proof/{2}'.format(self.api_url_base, self.getCurrentPentest(), defect_iid)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, [])
        return []

    @handle_api_errors
    def getResult(self, tool_iid, local_path):
        resultfile = self.getFileName("result", tool_iid)
        if resultfile is not None:
            try:
                return self._get("result", tool_iid, resultfile, local_path)
            except ErrorHTTP as e:
                raise e
        return None

    @handle_api_errors
    def getProof(self, defect_iid, filename, local_dir):
        try:
            return self._get("proof", defect_iid, filename, local_dir)
        except ErrorHTTP as e:
            raise e
        
    
    @handle_api_errors
    def getFileName(self, filetype, attached_iid):
        """Retrieve the list of filenames attached to a toolid
        Args:
            filetype: 'result' or 'proof' 
            attached_iid: tool or defect iid depending on filetype
        Returns : filename: remote file file name
        """
        api_url = '{0}files/{1}/download/{2}/{3}'.format(self.api_url_base, self.getCurrentPentest(), filetype, str(attached_iid))
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            ret = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            if isinstance(ret, list) and ret:
                return ret[0]
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None

    @handle_api_errors
    def _get(self, filetype, attached_iid, filename, local_path):
        """Download file affiliated with given iid and place it at given path
        Args:
            filetype: 'result' or 'proof' 
            attached_iid: tool or defect iid depending on filetype
            filename: remote file file name
            local_path: local file path
        """
        api_url = '{0}files/{1}/download/{2}/{3}/{4}'.format(self.api_url_base, self.getCurrentPentest(), filetype, attached_iid, filename)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            if not os.path.exists(local_path):
                os.makedirs(local_path)
            local_path = os.path.join(local_path, filename)
            with open(local_path, mode='wb') as f:
                f.write(response.content)
            return local_path
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None

    @handle_api_errors
    def rmProof(self, defect_iid, filename):
        """Remove file affiliated with given iid 
        """
        api_url = '{0}files/{1}/{2}/{3}'.format(self.api_url_base, self.getCurrentPentest(), defect_iid, filename)
        response = requests.delete(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None

    @handle_api_errors
    def getDesiredOutputForPlugin(self, cmdline, plugin):
        """Complete information for a command line. Plugin can be 'auto-detect', a marker for |outputDir| is to be replaced
        """
        api_url = '{0}tools/getDesiredOutputForPlugin'.format(self.api_url_base)
        response = requests.post(api_url, headers=self.headers, data=json.dumps({"plugin":plugin, "cmdline":cmdline}), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return True, data
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.content.decode('utf-8'))
        return False, response.content.decode('utf-8')
    
    @handle_api_errors
    def getCommandLine(self, toolId, commandline_options=""):
        """Get full command line from toolid and choosen parser, a marker for |outputDir| is to be replaced
        """
        api_url = '{0}tools/{1}/craftCommandLine/{2}'.format(self.api_url_base, self.getCurrentPentest(), toolId)
        response = requests.get(api_url, headers=self.headers, params={"commandline_options":commandline_options}, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return True, data
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.content.decode('utf-8'))
        return False, response.content.decode('utf-8')
    
    @handle_api_errors
    def importToolResult(self, tool_iid, parser, local_path):
        api_url = '{0}tools/{1}/importResult/{2}'.format(self.api_url_base, self.getCurrentPentest(), tool_iid)
        if not os.path.isfile(local_path):
            return "Failure to open provided file"
        with io.open(local_path, mode='rb') as f:
            h = self.headers.copy()
            h.pop("Content-Type", None)
            response = requests.post(api_url, files={"upfile": (os.path.basename(local_path) ,f)}, data={"plugin":parser}, headers=h, proxies=self.proxies, verify=False)
            if response.status_code == 200:
                return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            elif response.status_code >= 400:
                raise ErrorHTTP(response, response.content.decode('utf-8'))
            return response.content.decode('utf-8')

    @handle_api_errors
    def setToolStatus(self, tool_iid, newStatus, arg=""):
        api_url = '{0}tools/{1}/{2}/changeStatus'.format(self.api_url_base, self.getCurrentPentest(), tool_iid)
        response = requests.post(api_url, headers=self.headers, data=json.dumps({"newStatus":newStatus, "arg":arg}), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None

    @handle_api_errors
    def importExistingResultFile(self, filepath, plugin, default_target={}, command_used=""):
        api_url = '{0}files/{1}/import'.format(self.api_url_base, self.getCurrentPentest())
        with io.open(filepath, mode='rb') as f:
            h = self.headers.copy()
            h.pop("Content-Type", None)
            response = requests.post(api_url, headers=h, files={"upfile": (os.path.basename(filepath) ,f)}, data={"plugin":plugin, "default_target":json.dumps(default_target), "cmdline":command_used}, proxies=self.proxies, verify=False)
            if response.status_code == 200:
                return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            elif response.status_code >= 400:
                raise ErrorHTTP(response, json.loads(response.content.decode('utf-8'), cls=JSONDecoder))
        return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)

    @handle_api_errors
    def fetchWorkerInstruction(self, worker_name):
        api_url = '{0}workers/{1}/instructions'.format(self.api_url_base, worker_name)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return data
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None

    @handle_api_errors
    def deleteWorker(self, worker_name):
        api_url = '{0}workers/{1}'.format(self.api_url_base, worker_name)
        response = requests.delete(api_url, headers=self.headers, proxies=self.proxies, verify=False, timeout=2)
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return data
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None
    
    @handle_api_errors
    def deleteWorkerInstruction(self, worker_name, instruction_iid):
        api_url = '{0}workers/{1}/instructions/{2}'.format(self.api_url_base, worker_name, instruction_iid)
        response = requests.delete(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return data
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None

    @handle_api_errors
    def sendStartAutoScan(self, command_iids=None, autoqueue=False):
        if command_iids is None:
            command_iids = []
        api_url = '{0}autoscan/{1}/start'.format(self.api_url_base, self.getCurrentPentest())
        data = {"command_iids":command_iids, "autoqueue":bool(autoqueue)}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None
    
    @handle_api_errors
    def sendStopAutoScan(self):
        api_url = '{0}autoscan/{1}/stop'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None

    @handle_api_errors
    def getAutoScanStatus(self):
        api_url = '{0}autoscan/{1}/status'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None        

    @handle_api_errors
    def exportCommands(self, parent):
        api_url = '{0}exportCommands'.format(self.api_url_base)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            filename = "commands.json" 
            dir_path = os.path.dirname(os.path.realpath(__file__))
            out_path = os.path.normpath(os.path.join(
                dir_path, "../../exports/"))
            f = tk.filedialog.asksaveasfilename(parent=parent, defaultextension=".json", initialdir=out_path, initialfile=filename)
            if f is None or len(f) == 0:  # asksaveasfile return `None` if dialog closed with "cancel".
                return
            filename = str(f)
            with open(filename, mode='wb') as f:
                f.write(response.content)
                return True, filename
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        return False, response.text  

    @handle_api_errors
    def exportCheatsheet(self, parent):
        api_url = '{0}exportCheatsheet'.format(self.api_url_base)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            filename = "cheatsheet.json" 
            dir_path = os.path.dirname(os.path.realpath(__file__))
            out_path = os.path.normpath(os.path.join(
                dir_path, "../../exports/"))
            f = tk.filedialog.asksaveasfilename(parent=parent, defaultextension=".json", initialdir=out_path, initialfile=filename)
            if f is None or len(f) == 0:  # asksaveasfile return `None` if dialog closed with "cancel".
                return
            filename = str(f)
            with open(filename, mode='wb') as f:
                f.write(response.content)
                return True, filename
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        return False, response.text    
    
    @handle_api_errors
    def exportDefectTemplates(self, parent):
        api_url = '{0}report/DefectTemplates/export'.format(self.api_url_base)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            filename = "defect_templates.json" 
            dir_path = os.path.dirname(os.path.realpath(__file__))
            out_path = os.path.normpath(os.path.join(
                dir_path, "../../exports/"))
            f = tk.filedialog.asksaveasfilename(parent=parent, defaultextension=".json", initialdir=out_path, initialfile=filename)
            if f is None or len(f) == 0:  # asksaveasfile return `None` if dialog closed with "cancel".
                return 
            filename = str(f)
            with open(filename, mode='wb') as f:
                f.write(response.content)
                return True, filename
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        return False, response.text    

    @handle_api_errors
    def dumpDb(self, parent, pentest, collection=""):
        api_url = '{0}dumpDb/{1}'.format(self.api_url_base, pentest)
        response = requests.get(api_url, headers=self.headers, params={"collection":collection}, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            out_path = os.path.join(
                dir_path, "../../exports/")
            f = tk.filedialog.asksaveasfilename(parent=parent, defaultextension=".gz", initialdir=out_path, initialfile=(pentest if collection == "" else pentest+"_"+collection)+".gz")
            if f is None or len(f) == 0:  # asksaveasfile return `None` if dialog closed with "cancel".
                return None, None
            filename = str(f)          
            with open(filename, mode='wb') as f:
                f.write(response.content)
                return True, filename
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        return False, response.text  

    @handle_api_errors
    def importDb(self, filename, original_db_name):
        api_url = '{0}importDb'.format(self.api_url_base)
        with io.open(filename, mode='rb') as f:
            h = self.headers.copy()
            h.pop("Content-Type", None)
            response = requests.post(api_url, headers=h, files={"upfile": (os.path.basename(filename) ,f,'application/gzip')}, params={"orig_name":original_db_name}, proxies=self.proxies, verify=False)
            if response.status_code >= 400:
                raise ErrorHTTP(response, False)
            return response.status_code == 200
        return False
    
    @handle_api_errors
    def importCommands(self, filename, forWorker=False):
        api_url = '{0}importCommands'.format(self.api_url_base)
        if forWorker:
            api_url += "/worker"
        with io.open(filename, mode='rb') as f:
            h = self.headers.copy()
            h.pop("Content-Type", None)
            response = requests.post(api_url, headers=h, files={"upfile": (os.path.basename(filename) ,f, 'application/json')}, proxies=self.proxies, verify=False)
            if response.status_code >= 400:
                raise ErrorHTTP(response, False)
            return response.status_code == 200

    @handle_api_errors
    def importCheatsheet(self, filename):
        api_url = '{0}importCheatsheet'.format(self.api_url_base)
        with io.open(filename, mode='rb') as f:
            h = self.headers.copy()
            h.pop("Content-Type", None)
            response = requests.post(api_url, headers=h, files={"upfile": (os.path.basename(filename) ,f, 'application/json')}, proxies=self.proxies, verify=False)
            if response.status_code >= 400:
                raise ErrorHTTP(response, False)
            return response.status_code == 200

    @handle_api_errors
    def importDefectTemplates(self, filename):
        api_url = '{0}report/DefectTemplates/import'.format(self.api_url_base)
        with io.open(filename, mode='rb') as f:
            h = self.headers.copy()
            h.pop("Content-Type", None)
            response = requests.post(api_url, headers=h, files={"upfile": (os.path.basename(filename) ,f, 'application/json')}, proxies=self.proxies, verify=False)
            if response.status_code >= 400:
                raise ErrorHTTP(response, False)
            return response.status_code == 200
        
    @handle_api_errors
    def findDefectTemplateById(self, iid):
        api_url = '{0}report/DefectTemplates/find'.format(self.api_url_base)
        response = requests.post(api_url, headers=self.headers, data=json.dumps({"_id":ObjectId(iid)}, cls=JSONEncoder),  proxies=self.proxies, verify=False)
        if response.status_code == 200:
            res = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return res
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def insertAsTemplate(self, data):
        api_url = '{0}report/DefectTemplates/insert'.format(self.api_url_base)
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder),  proxies=self.proxies, verify=False)
        if response.status_code == 200:
            res = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return res["res"], res["iid"]
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None

    @handle_api_errors
    def updateDefectTemplate(self, iid, updatePipeline):
        api_url = '{0}report/DefectTemplates/update/{1}'.format(self.api_url_base, str(iid))
        response = requests.put(api_url, headers=self.headers, data=json.dumps(updatePipeline, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        else:
            return None
    
    @handle_api_errors
    def deleteDefectTemplate(self, iid):
        api_url = '{0}report/DefectTemplates/delete/{1}'.format(self.api_url_base, str(iid))
        response = requests.delete(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None

    @handle_api_errors
    def copyDb(self, fromDb, toDb=""):
        api_url = '{0}copyDb'.format(self.api_url_base)
        data = {"fromDb":self.getCurrentPentest(), "toDb":toDb}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None
 
    @handle_api_errors
    def generateReport(self, templateName, clientName, contractName, mainRedac, lang, additional_context):
        api_url = '{0}report/{1}/generate'.format(self.api_url_base, self.getCurrentPentest())
        data = {"templateName":templateName,"mainRedactor":mainRedac, "lang":lang, "additional_context":additional_context}
        response = requests.post(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            timestr = datetime.now().strftime("%Y%m")
            ext = os.path.splitext(templateName)[-1]
            basename = clientName.strip()+" - "+contractName.strip()
            out_name = str(timestr)+" - "+basename
            out_path = os.path.join(dir_path, "../../exports/")
            f = tk.filedialog.asksaveasfilename(defaultextension=ext, initialdir=out_path, initialfile=out_name+ext)
            if f is None or len(f) == 0:  # asksaveasfile return `None` if dialog closed with "cancel". and empty tuple if close by cross
                return False, "No report created"
            filename = str(f)
            with open(filename, mode='wb') as f:
                f.write(response.content)
                return True, os.path.normpath(filename)
        elif response.status_code >= 400:
            return False, response.content.decode("utf-8")
        return False, response.content.decode("utf-8")

    @handle_api_errors
    def getTemplateList(self, lang):
        api_url = '{0}report/{1}/templates'.format(self.api_url_base, lang)
        try:
            response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        except ConnectionError as e:
            raise e
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, [])
        return []

    @handle_api_errors
    def getLangList(self):
        api_url = '{0}report/langs'.format(self.api_url_base)
        try:
            response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        except ConnectionError as e:
            raise e
        if response.status_code == 200:
            return json.loads(response.content.decode("utf-8"), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, ["en"])
        return ["en"]
    
    @handle_api_errors
    def downloadTemplate(self, parent, lang, templateName):
        api_url = '{0}report/{1}/templates/download'.format(self.api_url_base, lang)
        response = requests.get(api_url, headers=self.headers, params={"templateName":templateName},proxies=self.proxies, verify=False)
        if response.status_code == 200:
            out_path = os.path.join(dir_path, "../../exports/")
            f = tk.filedialog.asksaveasfilename(parent=parent, initialdir=out_path, initialfile=templateName)
            if f is None or len(f) == 0:  # asksaveasfile return `None` if dialog closed with "cancel".
                return
            filename = str(f)
            with open(filename, mode='wb') as f:
                f.write(response.content)
                return os.path.normpath(filename)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None

    @handle_api_errors
    def getDefectTable(self):
        api_url = '{0}report/{1}/defects'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, [])
        return []

    @handle_api_errors
    def moveDefect(self, defect_id, target_id):
        api_url = '{0}report/{1}/defects/move/{2}/{3}'.format(self.api_url_base, self.getCurrentPentest(), defect_id, target_id)
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, response.content.decode("utf-8"))
        return response.content.decode("utf-8")

    @handle_api_errors
    def getUsers(self):
        api_url = '{0}admin/listUsers'.format(self.api_url_base)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, [])
        return []

    @handle_api_errors
    def searchUsers(self, username):
        api_url = '{0}user/searchUsers/{1}'.format(self.api_url_base, username)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, [])
        return []

    @handle_api_errors
    def registerUser(self, username, password, name, surname, email):
        api_url = '{0}user/register'.format(self.api_url_base)
        response = requests.post(api_url, headers=self.headers, data=json.dumps({"username":username, "pwd":password, "name":name, "surname":surname,"email":email}), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None

    @handle_api_errors
    def updateUserInfos(self, username, name, surname, email):
        api_url = '{0}user/updateUserInfos'.format(self.api_url_base)
        response = requests.post(api_url, headers=self.headers, data=json.dumps({"username":username, "name":name, "surname":surname,"email":email}), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None

    @handle_api_errors
    def deleteUser(self, username):
        api_url = '{0}user/delete/{1}'.format(self.api_url_base, username)
        response = requests.delete(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response)
        return None

    @handle_api_errors
    def changeUserPassword(self, oldPwd, newPwd):
        api_url = '{0}user/changePassword'.format(self.api_url_base)
        response = requests.post(api_url, headers=self.headers, data=json.dumps({"oldPwd":oldPwd, "newPwd":newPwd}), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return ""
        elif response.status_code >= 400:
            raise ErrorHTTP(response, json.loads(response.content.decode('utf-8'), cls=JSONDecoder))
        return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)

    @handle_api_errors
    def resetPassword(self, username, newPwd):
        api_url = '{0}admin/resetPassword'.format(self.api_url_base)
        response = requests.post(api_url, headers=self.headers, data=json.dumps({"username":username, "newPwd":newPwd}), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return ""
        elif response.status_code >= 400:
            raise ErrorHTTP(response, json.loads(response.content.decode('utf-8'), cls=JSONDecoder))
        return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)

    @handle_api_errors
    def getPlugins(self):
        api_url = '{0}tools/plugins'.format(self.api_url_base)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, [])
        return []

    @handle_api_errors
    def getDockerForPentest(self, pentest):
        api_url = '{0}workers/start/{1}'.format(self.api_url_base, pentest)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code == 403:
            tk.messagebox.showerror("Docker error", "Docker could not start, check server installation of docker")
            return None
        elif response.status_code >= 400:
            raise ErrorHTTP(response, [])
        return None

    @handle_api_errors
    def getComputerUsers(self, computer_iid):
        api_url = '{0}ActiveDirectory/computers/{1}/{2}/getUsers'.format(self.api_url_base, self.getCurrentPentest(), computer_iid)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code == 403:
            tk.messagebox.showerror("Docker error", "Docker could not start, check server installation of docker")
            return None
        elif response.status_code >= 400:
            raise ErrorHTTP(response, {})
        return None

    @handle_api_errors
    def linkAuth(self, auth_iid, object_iid):
        api_url = '{0}auth/{1}/{2}/link/{3}'.format(self.api_url_base, self.getCurrentPentest(), auth_iid, object_iid)
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return response.content.decode('utf-8')
        elif response.status_code >= 400:
            raise ErrorHTTP(response, "Error : "+str(response.content.decode('utf-8')))
        return "Undefined return status code"

    @handle_api_errors
    def getModuleInfo(self, module):
        api_url = '{0}{1}/getModuleInfo'.format(self.api_url_base, module)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, "Error : "+str(response.content.decode('utf-8')))
        return "Undefined return status code"

    @handle_api_errors
    def addRangeMatchingIps(self):
        api_url = '{0}NetworkDiscovery/{1}/addRangeMatchingIps'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return ""
        elif response.status_code >= 400:
            raise ErrorHTTP(response, json.loads(response.content.decode('utf-8'), cls=JSONDecoder))
        return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)


    @handle_api_errors
    def addRangeCloseToOthers(self):
        api_url = '{0}NetworkDiscovery/{1}/addRangeCloseToOthers'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return ""
        elif response.status_code >= 400:
            raise ErrorHTTP(response, json.loads(response.content.decode('utf-8'), cls=JSONDecoder))
        return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
    
    @handle_api_errors
    def addCommonRanges(self):
        api_url = '{0}NetworkDiscovery/{1}/addCommonRanges'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return ""
        elif response.status_code >= 400:
            raise ErrorHTTP(response, json.loads(response.content.decode('utf-8'), cls=JSONDecoder))
        return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)

    @handle_api_errors
    def addAllLANRanges(self):
        api_url = '{0}NetworkDiscovery/{1}/addAllLANRanges'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.post(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return ""
        elif response.status_code >= 400:
            raise ErrorHTTP(response, json.loads(response.content.decode('utf-8'), cls=JSONDecoder))
        return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)

    @handle_api_errors
    def getCheckInstanceRepr(self, checkinstance_iids):
        api_url = '{0}cheatsheet/{1}/getTargetRepr'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.post(api_url, headers=self.headers, data=json.dumps(checkinstance_iids, cls=JSONEncoder), proxies=self.proxies ,verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, {},)
        return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)

    @handle_api_errors
    def getCheckInstanceInfo(self, checkinstance_iid):
        api_url = '{0}cheatsheet/{1}/{2}'.format(self.api_url_base, self.getCurrentPentest(), checkinstance_iid)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies ,verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, {},)
        return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)

    @handle_api_errors
    def getDefectTargetRepr(self, defect_iids):
        api_url = '{0}defects/{1}/getTargetRepr'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.post(api_url, headers=self.headers, data=json.dumps(defect_iids, cls=JSONEncoder), proxies=self.proxies ,verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, {},)
        return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)

    @handle_api_errors
    def getToolProgress(self, tool_iid):
        api_url = '{0}tools/{1}/getProgress/{2}'.format(self.api_url_base, self.getCurrentPentest(), tool_iid)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        else:
            return None

    @handle_api_errors
    def getToolDetailedString(self, tool_iid):
        api_url = '{0}tools/{1}/{2}/getDetailedString'.format(self.api_url_base, self.getCurrentPentest(), tool_iid)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        else:
            return "Error reaching API"

    @handle_api_errors
    def getTriggerLevels(self):
        api_url = '{0}getTriggerLevels'.format(self.api_url_base)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        else:
            return []
        
    @handle_api_errors
    def getPluginTags(self):
        api_url = '{0}tags/getPluginTags'.format(self.api_url_base)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            tags_per_plugin = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            tags = []
            for plugin in tags_per_plugin:
                tags += tags_per_plugin[plugin]
            return tags
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        else:
            return []

    @handle_api_errors
    def getCommandVariables(self):
        api_url = '{0}getCommandVariables'.format(self.api_url_base)
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        else:
            return []
            
    @handle_api_errors
    def getGeneralInformation(self):
        api_url = '{0}pentest/{1}'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.get(api_url, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        else:
            return []
        
    @handle_api_errors
    def addTag(self, item_id, item_type, tag, overrideGroup=True):
        api_url = '{0}tags/{1}/addTag/{2}'.format(self.api_url_base, self.getCurrentPentest(), item_id)
        data = {"item_type":item_type,"tag":tag, "overrideGroup":overrideGroup}
        response = requests.put(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        else:
            return None
    
    @handle_api_errors
    def delTag(self, item_id, item_type, tag):
        api_url = '{0}tags/{1}/delTag/{2}'.format(self.api_url_base, self.getCurrentPentest(), item_id)
        data = {"item_type":item_type,"tag":tag}
        response = requests.put(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        else:
            return None
        
    @handle_api_errors
    def setTags(self, item_id, item_type, tags):
        api_url = '{0}tags/{1}/setTags/{2}'.format(self.api_url_base, self.getCurrentPentest(), item_id)
        data = {"item_type":item_type,"tags":tags}
        response = requests.put(api_url, headers=self.headers, data=json.dumps(data, cls=JSONEncoder), proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        else:
            return None
        
    @handle_api_errors
    def searchTaggedBy(self, tag_name):
        api_url = '{0}tags/{1}/getTaggedBy'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.get(api_url, params={"tag_name":tag_name}, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
        elif response.status_code >= 400:
            raise ErrorHTTP(response, False, response.text)
        else:
             return {"success":False, "msg":"Unexpected server response "+str(response.status_code)+"\n"+response.text}
        
    @handle_api_errors
    def searchPentest(self, stringQuery, textonly=False):
        api_url = '{0}search/{1}'.format(self.api_url_base, self.getCurrentPentest())
        response = requests.get(api_url, params={"s":stringQuery,"textonly":textonly}, headers=self.headers, proxies=self.proxies, verify=False)
        if response.status_code == 200:
            res_obj = json.loads(response.content.decode('utf-8'), cls=JSONDecoder)
            return res_obj
        else:
            return {"success":False, "msg":"Unexpected server response "+str(response.status_code)+"\n"+response.text}