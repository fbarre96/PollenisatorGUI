from pollenisatorgui.core.components.apiclient import APIClient

REGISTRY = {}

def register_class(target_class):
    """Register the given class
    Args:
        target_class: type <class>
    """
    REGISTRY[target_class.__name__] = target_class

class MetaModule(type):
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        if name not in REGISTRY:
            register_class(cls)
        return cls

class Module(metaclass=MetaModule):
    need_admin = False
    pentest_types = ["all"]

    def loadModuleInfo(self):
        apiclient = APIClient.getInstance()
        if hasattr(self.__class__, "collName"):
            self.module_info = apiclient.getModuleInfo(self.__class__.collName)

    def notify(self, db, collection, iid, action, _parent):
        """
        Callback for the observer implemented in mongo.py.
        Each time an object is inserted, updated or deleted the standard way, this function will be called.

        Args:
            collection: the collection that has been modified
            iid: the mongo ObjectId _id that was modified/inserted/deleted
            action: string "update" or "insert" or "delete". It was the action performed on the iid
            _parent: Not used. the mongo ObjectId of the parent. Only if action in an insert. Not used anymore
        """
        apiclient = APIClient.getInstance()
        if not apiclient.getCurrentPentest() != "":
            return
        if apiclient.getCurrentPentest() != db:
            return
        if hasattr(self.__class__, "collName") and collection == self.__class__.collName:
            self.handleNotif(db, collection, iid, action)
        else:
            if hasattr(self.__class__, "collNames") and collection in self.__class__.collNames:
                self.handleNotif(db, collection, iid, action)

    def handleNotif(self, db, collection, iid, action):
        pass # NOT implemented