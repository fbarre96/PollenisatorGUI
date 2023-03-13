from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.datamanager import DataManager

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
    FIRST_PRIORITY = 0
    HIGH_PRIORITY = 1
    MEDIUM_PRIORITY = 2
    LOW_PRIORITY = 3
    LAST_PRIORITY = 99
    order_priority = LOW_PRIORITY
    def __init__(self):
        datamanager = DataManager.getInstance().attach(self)
        
    def update_received(self, dataManager, notif, obj, old_obj):
        pass
    
