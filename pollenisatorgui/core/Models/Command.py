"""Command Model."""
from pollenisatorgui.core.Models.Element import Element
from pollenisatorgui.core.Components.apiclient import APIClient


class Command(Element):
    """Represents a command object to be run on designated scopes/ips/ports.

    Attributes:
        coll_name: collection name in pollenisator or pentest database
    """

    coll_name = "commands"

    def __init__(self, valuesFromDb=None):
        """Constructor
        Args:
            valueFromDb: a dict holding values to load into the object. A mongo fetched command is optimal.
                        possible keys with default values are : _id (None), parent (None), tags([]), infos({}), name(""), 
                         text(""), lvl("network"), ports(""), safe(True), types([]), indb="pollenisator", timeout="300", owner=""
        """
        if valuesFromDb is None:
            valuesFromDb = dict()
        super().__init__(valuesFromDb.get("_id", None), valuesFromDb.get("parent", None),  valuesFromDb.get(
            "tags", []), valuesFromDb.get("infos", {}))
        self.initialize(valuesFromDb.get("name", ""), valuesFromDb.get("bin_path", ""), valuesFromDb.get("plugin", ""), 
                        valuesFromDb.get("text", ""), valuesFromDb.get(
                            "lvl", "network"),
                        valuesFromDb.get("ports", ""),
                        bool(valuesFromDb.get("safe", True)), valuesFromDb.get("types", []), valuesFromDb.get("indb", "pollenisator"), valuesFromDb.get("timeout", 300), 
                        valuesFromDb.get("owner", ""), valuesFromDb.get("infos", {}))

    def initialize(self, name, bin_path, plugin="Default", text="", lvl="network", ports="", safe=True, types=None, indb=False, timeout=300, owner="", infos=None):
        """Set values of command
        Args:
            name: the command name
            bin_path: local command, binary path or command line
            plugin: plugin that goes with this command
            text: the command line options. Default is "".
            lvl: level of the command. Must be either "wave", "network", "domain", "ip", "port" or a module name. Default is "network"
            ports: allowed proto/port, proto/service or port-range for this command
            safe: True or False with True as default. Indicates if autoscan is authorized to launch this command.
            types: type for the command. Lsit of string. Default to None.
            indb: db name : global (pollenisator database) or  local pentest database
            timeout: a timeout to kill stuck tools and retry them later. Default is 300 (in seconds)
            owner: the owner of the command
            infos: a dictionnary with key values as additional information. Default to None
        Returns:
            this object
        """
        self.name = name
        self.bin_path = bin_path
        self.plugin = plugin
        self.text = text
        self.lvl = lvl
        self.ports = ports
        self.safe = bool(safe)
        self.infos = infos if infos is not None else {}
        self.indb = indb
        self.timeout = timeout
        self.types = types if types is not None else []
        self.owner = owner
        return self

    def delete(self):
        """
        Delete the command represented by this model in database.
        Also delete it from every group_commands.
        Also delete it from every waves's wave_commands
        Also delete every tools refering to this command.
        """
        ret = self._id
        apiclient = APIClient.getInstance()
        if self.indb == "pollenisator":
            apiclient.deleteCommand(ret)
        else:
            apiclient.delete("commands", ret)
        

    def addInDb(self):
        """Add this command to pollenisator database
        Returns: a tuple with :
                * bool for success
                * mongo ObjectId : already existing object if duplicate, create object id otherwise 
        """
        apiclient = APIClient.getInstance()
        res, id = apiclient.insert("commands", {"name": self.name, "bin_path":self.bin_path, "plugin":self.plugin, "lvl": self.lvl,
                                                                            "text": self.text,
                                                                           "ports": self.ports, "safe": bool(self.safe), "types": self.types, "indb": self.indb, "timeout": int(self.timeout), "owner": self.owner})
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
            apiclient.update("commands", self._id, {"timeout": int(self.timeout),
                         "text": self.text, "ports": self.ports, "safe": bool(self.safe), "types": self.types, "indb":self.indb, "plugin":self.plugin, "bin_path":self.bin_path})
           
        else:
            apiclient.update("commands", self._id, pipeline_set)
            

    @classmethod
    def getList(cls, pipeline=None, targetdb="pollenisator"):
        """
        Get all command's name registered on database
        Args:
            pipeline: default to None. Condition for mongo search.
        Returns:
            Returns the list of commands name found inside the database. List may be empty.
        """
        if pipeline is None:
            pipeline = {}
        return [command for command in cls.fetchObjects(pipeline, targetdb)]

    @classmethod
    def fetchObject(cls, pipeline, targetdb="pollenisator"):
        """Fetch one command from database and return the Command object 
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a Command or None if nothing matches the pipeline.
        """
        apiclient = APIClient.getInstance()
        if targetdb == "pollenisator":
            res = apiclient.findCommand(pipeline)
            d = res[0] if res else None
        else:
            d = apiclient.findInDb(targetdb, "commands", pipeline, False)
        if d is None:
            return None
        return Command(d)

    @classmethod
    def fetchObjects(cls, pipeline, targetdb="pollenisator"):
        """Fetch many commands from database and return a Cursor to iterate over Command objects
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a cursor to iterate on Command objects
        """
        apiclient = APIClient.getInstance()
        if targetdb == "pollenisator":
            ds = apiclient.findCommand(pipeline)
        else:
            ds = apiclient.findInDb(targetdb, "commands", pipeline, True)
        if ds is None:
            return None
        for d in ds:
            yield Command(d)
    
    @classmethod
    def getMyCommands(cls, user=None):
        """Fetch many commands from database and return a Cursor to iterate over Command objects
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a cursor to iterate on Command objects
        """
        apiclient = APIClient.getInstance()
        if user is None:
            user = apiclient.getUser()
        ds = apiclient.findCommand({"owner":user})
        if ds is None:
            return None
        for d in ds:
            yield Command(d)    

    def addToMyCommands(self):
        apiclient = APIClient.getInstance()
        apiclient.addCommandToMyCommands(self.getId())

    def isMyCommand(self):
        user = APIClient.getInstance().getUser()
        return user == self.owner
        
    def isWorkerCommand(self):
        return self.owner == "Worker"

    def __str__(self):
        """
        Get a string representation of a command.

        Returns:
            Returns the command's name string.
        """
        return self.owner+":"+self.name

    def getDbKey(self):
        """Return a dict from model to use as unique composed key.
        Returns:
            A dict (1 key :"name")
        """
        return {"name": self.name, "owner":self.owner}
