import os
from bson import ObjectId
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.models.metaelement import REGISTRY
from multiprocessing import Manager
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
        if observer not in self._observers:
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
        self.currentDatabase = None
        pid = os.getpid()
        DataManager.__instances[pid] = self

    def load(self, forceReload=False):
        if len(self.data) > 0 and not forceReload:
            return
        self.currentPentest = APIClient.getInstance().getCurrentPentest()
        for coll, model in REGISTRY.items():
            self.data[coll.lower()] = {}
            datas = model.fetchPentestObjects()
            for item in datas:
                self.data[coll.lower()][str(item.getId())] = item

    def get(self, collection, iid, default=None):
        if collection not in self.data.keys() and collection[:-1] in self.data.keys():
            collection = collection[:-1]
        if collection not in self.data.keys():
            return default
        if iid == "*":
            return self.data[collection]
        return self.data[collection].get(str(iid), None)

    def find(self, collection, search, multi=True):
        if collection not in self.data.keys() and collection[:-1] in self.data.keys():
            collection = collection[:-1]
        if collection not in self.data.keys():
            return None
        ret = []
        for data_model in self.data[collection].values():
            is_match = True
            for key, val in search.items():
                data = data_model.getData()
                if data.get(key, None) != val:
                    is_match = False
                    break
            if is_match:
                ret.append(data)
                if not multi:
                    return data
        if not multi:
            return None
        return ret
            
    def getClass(self, class_str):
        for coll, model in REGISTRY.items():
            if coll.lower() == class_str or coll.lower()+"s" == class_str:
                return model
        raise ValueError("Class not found "+str(class_str))

    def remove(self, collection, iid):
        if collection not in self.data.keys() and collection+"s" in self.data.keys():
            collection = collection+"s"
        if collection not in self.data.keys():
            return 
        del self.data[collection][str(iid)]
        
    def set(self, collection, iid, newVal):
        if collection not in self.data.keys() and collection+"s" in self.data.keys():
            collection = collection+"s"
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
        apiclient = APIClient.getInstance()
        obj = None
        old_obj = None
        if notification["db"] != "pollenisator":
            class_name = notification["collection"]
            if class_name == "cheatsheet":
                class_name = "checkinstance" # because cheatsheet in db pollenisator is CheckItem, CheckInstance otherwise
            if class_name in self.data.keys() or class_name[:-1] in self.data.keys():
                if notification["action"] == "update" or notification["action"] == "insert":
                    updated_data = apiclient.findInDb(notification["db"], notification["collection"], {"_id": ObjectId(notification["iid"])}, False)
                    obj = self.getClass(class_name)(updated_data)
                    old_obj = self.get(class_name, notification["iid"])
                    self.set(class_name, notification["iid"], obj)
                elif notification["action"] == "delete":
                    self.remove(class_name, notification["iid"])
                try:
                    data = self.get(class_name, notification["iid"])
                except KeyError:
                    data = None
        self.notify(notification, obj, old_obj)

    
    

    