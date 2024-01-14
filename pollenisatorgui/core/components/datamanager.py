import os
import traceback
from bson import ObjectId
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.models.metaelement import REGISTRY
from pollenisatorgui.core.components.logger_config import logger

class Subject:
    """Represents what is being observed"""
 
    def __init__(self):
        """create an empty observer list"""
        self._observers = []
 
    def notify(self, notif, obj, old_obj):
        """Alert the observers"""
        for observer in self._observers:
            observer.update_received(self, notif, obj, old_obj)
 
    def attach(self, observer):
        """If the observer is not in the list,
        append it into the list"""
        if type(observer) not in [type(o) for o in self._observers]:
            self._observers.append(observer)
 
    def detach(self, observer):
        """Remove the observer from the observer list"""
        try:
            self._observers.remove(observer)
        except ValueError:
            pass
 
class DataManager(Subject):
    __instances = dict()
    def __init__(self):
        super().__init__()
        self._observers
        self.data = {}
        self.ip_index = {}
        self.currentPentest = None
        pid = os.getpid()
        DataManager.__instances[pid] = self

    def openPentest(self, pentest):
        self.currentPentest = pentest
        self.data = {}


    # def load(self, collections=None, forceReload=False):
    #     if len(self.data) > 0 and not forceReload:
    #         return
    #     self.currentPentest = APIClient.getInstance().getCurrentPentest()
        
    #     for coll, model in REGISTRY.items():
    #         if collections is not None and coll not in collections:
    #             continue
    #         self.data[coll] = {}
    #         datas = model.fetchPentestObjects()
    #         for item in datas:
    #             self.data[coll][str(item.getId())] = item

    def get(self, collection, iid):
        collection = collection.lower()
        if collection not in REGISTRY.keys() and collection[:-1] in REGISTRY.keys():
            collection = collection[:-1]
        if iid == "*":
            ret = []
            datas = REGISTRY[collection].fetchPentestObjects()
            if self.data.get(collection, None) is None:
                self.data[collection] = {}
            for data in datas:
                self.data[collection][str(data._id)] = data
                if collection == "ip":
                    self.ip_index[data.ip] = data
                ret.append(data)
            return ret
        return self.find(collection, {"_id": iid}, multi=False, fetch_on_none=True)
        # collection = collection.lower()
        # if collection not in self.data.keys() and collection[:-1] in self.data.keys():
        #     collection = collection[:-1]
        # if collection not in self.data.keys():
        #     return default
        # if iid == "*":
        #     return self.data[collection]
        # return self.data[collection].get(str(iid), None)

    def find(self, collection, search, multi=True, fetch_on_none=True):
        collection = collection.lower()
        if collection not in REGISTRY.keys() and collection[:-1] in REGISTRY.keys():
            collection = collection[:-1]
        if collection not in self.data:
            self.data[collection] = {}
        if len(search) == 1:
            if "ip" in search.keys() and collection == "ip":
                ip = search["ip"]
                ret = self.ip_index.get(ip, None)
                if ret is None and fetch_on_none:
                    search = {"ip": ip}
                    ret = REGISTRY[collection].fetchObject(search)
                    self.data[collection][str(ret.getId())] = ret
                    self.ip_index[ip] = ret
                return ret
            if "_id" in search.keys():
                iid = search["_id"]
                ret = self.data[collection].get(str(iid), None)
                if ret is None and fetch_on_none:
                    search = {"_id": ObjectId(iid)}
                    if collection == "command":
                        ret = REGISTRY[collection].fetchObject(search, self.currentPentest)
                    else:
                        ret = REGISTRY[collection].fetchObject(search)
                    if ret is None:
                        return None
                    self.data[collection][str(ret.getId())] = ret
                return ret
        # if collection not in self.data.keys():
        #     return None
        ret = []
        for data_model in list(self.data.get(collection, {}).values()):
            is_match = True
            for key, val in search.items():
                data = data_model.getData()
                compared = data.get(key, None)
                if isinstance(compared, list):
                    if val not in compared:
                        is_match = False
                        break
                elif compared != val:
                    is_match = False
                    break
            if is_match:
                ret.append(data_model)
                if not multi:
                    return data_model
        if len(ret) == 0 and fetch_on_none:
            if multi:
                if collection == "command":
                        datas = REGISTRY[collection].fetchObjects(search, self.currentPentest)
                else:
                    datas = REGISTRY[collection].fetchObjects(search)
                for data in datas:
                    self.data[collection][str(data.getId())] = data
                    if collection == "ip":
                        self.ip_index[data.ip] = data
                    ret.append(data)
            else:
                if collection == "command":
                    data = REGISTRY[collection].fetchObject(search, self.currentPentest)
                else:
                    data = REGISTRY[collection].fetchObject(search)
                ret = data
        if not multi and not ret:
            return None
        return ret
            
    def getClass(self, class_str):
        for coll, model in REGISTRY.items():
            if coll == class_str or coll+"s" == class_str:
                return model
        raise ValueError("Class not found "+str(class_str))

    def remove(self, collection, iid):
        if collection not in self.data.keys() and collection+"s" in self.data.keys():
            collection = collection+"s"
        if collection not in self.data.keys() and collection[:-1] in self.data.keys():
            collection = collection[:-1]
        if collection not in self.data.keys():
            return
        try:
            del self.data[collection][str(iid)]
        except KeyError:
            pass
        
    def set(self, collection, iid, newVal):
        if collection not in self.data.keys() and collection+"s" in self.data.keys():
            collection = collection+"s"
        if collection not in self.data.keys() and collection[:-1] in self.data.keys():
            collection = collection[:-1]
        if collection not in self.data.keys():
            return 
        self.data[collection][str(iid)] = newVal
    
    @staticmethod
    def getInstance():
        """ Singleton Static access method.
        """
        pid = os.getpid()  # HACK : One api client per process.
        instance = DataManager.__instances.get(pid, None)
        if instance is None:
            DataManager()
        return DataManager.__instances[pid]

    def handleNotification(self, notification):
        try:
            apiclient = APIClient.getInstance()
            obj = None
            old_obj = None
            if notification["db"] != "pollenisator":
                class_name = notification["collection"]
                if class_name in self.data.keys() or class_name[:-1] in self.data.keys():
                    if notification["action"] == "update" or notification["action"] == "insert":
                        updated_data = apiclient.findInDb(notification["db"], notification["collection"], {"_id": ObjectId(notification["iid"])}, False, use_cache=False)
                        obj = self.getClass(class_name)(updated_data)
                        old_obj = self.get(class_name, notification["iid"])
                        if old_obj is None:
                            notification["action"] = "insert"
                        self.set(class_name, notification["iid"], obj)
                    elif notification["action"] == "insert_many" or notification["action"] == "update_many":
                        updated_data = apiclient.findInDb(notification["db"], notification["collection"], {"_id": {"$in":notification["iid"]}}, True)
                        obj = []
                        for data in updated_data:
                            try:
                                model = self.getClass(class_name)(data)
                            except Exception as e:
                                logger.error("Error while creating model : "+str(e))
                                continue
                            obj.append(model)
                            self.set(class_name, data["_id"], model)
                    elif notification["action"] == "delete":
                        self.remove(class_name, notification["iid"])
            self.notify(notification, obj, old_obj)
        except Exception as e:
            traceback.print_exc()
            logger.critical("Error while handling notification : "+str(e))
    
    

    