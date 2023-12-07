"""CheckItem Model."""
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.models.element import Element
from pollenisatorgui.core.components.apiclient import APIClient
from bson import ObjectId

class CheckItem(Element):
    """Represents a CheckItem object of a cheatsheet.

    Attributes:
        coll_name: collection name in pollenisator or pentest database
    """

    coll_name = "checkitems"

    def __init__(self, valuesFromDb=None):
        """Constructor
        Args:
            valueFromDb: a dict holding values to load into the object. A mongo fetched command is optimal.
                        possible keys with default values are : _id (None), parent (None), title, pentest_types=None, description="", category="", commands=None, defect_tags=None, script="",infos=None
        """
        if valuesFromDb is None:
            valuesFromDb = dict()
        super().__init__(valuesFromDb.get("_id", None), valuesFromDb.get("parent", None), valuesFromDb.get("infos", {}))
        self.initialize(valuesFromDb.get("title"), valuesFromDb.get("pentest_types", []), valuesFromDb.get("lvl", "port:onServiceUpdate"),
            valuesFromDb.get("ports", ""), valuesFromDb.get("priority", 0), valuesFromDb.get("max_thread", 1), valuesFromDb.get("description", ""), valuesFromDb.get("category", ""),\
            valuesFromDb.get("check_type", "manual"), valuesFromDb.get("step", 0), valuesFromDb.get("parent", None),
            valuesFromDb.get("commands", []), valuesFromDb.get("defect_tags", []), valuesFromDb.get("script", ""),  valuesFromDb.get("infos", {}))
        
    def initialize(self, title, pentest_types=None, lvl="port:onServiceUpdate", ports="", priority=0, max_thread=1, description="", category="", check_type="manual", step=0, parent=None, commands=None, defect_tags=None, script="", infos=None):
        self.title = title
        self.description = description
        self.category = category
        self.check_type = check_type
        self.step = step
        self.parent = parent
        self.lvl = lvl
        self.ports = ports
        self.max_thread = int(max_thread)
        self.priority = int(priority)
        self.commands = [] if commands is None else commands
        self.defect_tags = [] if defect_tags is None else defect_tags
        self.script = script
        self.pentest_types = [] if pentest_types is None else pentest_types
        self.defect_tags = [] if defect_tags is None else defect_tags
        self.infos = {} if infos is None else infos
        return self

    def delete(self):
        """
        Delete the command represented by this model in database.
        Also delete it from every waves's wave_commands
        Also delete every tools refering to this command.
        """
        ret = self._id
        apiclient = APIClient.getInstance()
        apiclient.deleteCheckItem(ret)
        

    def addInDb(self):
        """Add this command to pollenisator database
        Returns: a tuple with :
                * bool for success
                * mongo ObjectId : already existing object if duplicate, create object id otherwise 
        """
        apiclient = APIClient.getInstance()
        res, id = apiclient.insertCheckItem(self.getData())
        if not res:
            return False, id
        self._id = id
        return True, id
        

    def update(self, pipeline_set=None):
        """Update this object in database.
        Args:
            pipeline_set: (Opt.) A dictionnary with custom values. If None (default) use model attributes.
        """
        apiclient = APIClient.getInstance()
        if pipeline_set is None:
            apiclient.updateCheckItem(self._id, self.getData())
        else:
            apiclient.updateCheckItem(self._id, pipeline_set )
        


    @classmethod
    def fetchObject(cls,  pipeline):
        """Fetch one CheckItem from database and return the CheckItem object 
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a CheckItem or None if nothing matches the pipeline.
        """
        apiclient = APIClient.getInstance()
        res = apiclient.findCheckItem(pipeline, many=False)
        d = res
        if d is None:
            return None
        return CheckItem(d)

    @classmethod
    def fetchObjects(cls, pipeline):
        """Fetch many cheatsheet from database and return a Cursor to iterate over cheatsheet objects
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a cursor to iterate on cheatsheet objects
        """
        apiclient = APIClient.getInstance()
        ds = apiclient.findCheckItem(pipeline)
        if ds is None:
            return None
        for d in ds:
            yield CheckItem(d)
    
    def getChecks(self):
        """Return check instances that implements this check item
        Returns:
            list of checkInstance objects
        """
        datamanager = DataManager.getInstance()
        return datamanager.find("checkinstance", {"check_iid": str(self._id)}, multi=True)
    
    def getData(self):
        return {"_id": self._id,  "title":self.title, "pentest_types":self.pentest_types, "lvl":self.lvl, "ports":self.ports, 
                "priority": int(self.priority), "max_thread": int(self.max_thread),
                "description": self.description, "category":self.category,
                "check_type":self.check_type, "step":self.step, "parent":self.parent,
                "commands":self.commands, "defect_tags":self.defect_tags, "script":self.script, "infos":self.infos}


    def getDbKey(self):
        """Return a dict from model to use as unique composed key.
        Returns:
            A dict (1 key :"name")
        """
        return {"title": self.title}

    def isAuto(self):
        """Return True if this command is an auto command"""
        return "auto" in self.check_type

    def __str__(self):
        return self.title

    @classmethod
    def fetchPentestObjects(cls):
        return cls.fetchObjects({})