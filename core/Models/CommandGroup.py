"""Command Group Model."""
from core.Models.Element import Element
from core.Components.apiclient import APIClient
from bson.objectid import ObjectId


class CommandGroup(Element):
    """Represents a command group object that defines settings and ressources shared by many Commands.

    Attributes:
        coll_name: collection name in pollenisator database
    """
    coll_name = "group_commands"

    def __init__(self, valuesFromDb=None):
        """Constructor
        Args:
            valueFromDb: a dict holding values to load into the object. A mongo fetched command group is optimal.
                        possible keys with default values are : _id (None), parent (None), tags([]), infos({}),
                        name(""), sleep_between("0"), commands([]),
                        max_thread("1")
        """
        if valuesFromDb is None:
            valuesFromDb = {}
        super().__init__(valuesFromDb.get("_id", None), valuesFromDb.get("parent", None), valuesFromDb.get(
            "tags", []), valuesFromDb.get("infos", {}))
        self.initialize(valuesFromDb.get("name", ""), valuesFromDb.get("sleep_between", 0), valuesFromDb.get("commands", []),
                        valuesFromDb.get("max_thread", 1), valuesFromDb.get("infos", {}))

    def initialize(self, name, sleep_between=0, commands=None, max_thread=1, infos=None):
        """Set values of command group
        Args:
            name: the command group name
            sleep_between: delay to wait between two call to this command. Default is 0.
            commands: list of command names that are part of this group. Default is None and stores an empty array
            max_thread: number of parallel execution possible of this command. Default is 1.
            infos: a dictionnary with key values as additional information. Default to None
        Returns:
            this object
        """
        if commands is None:
            commands = []
        self.name = name
        self.sleep_between = int(sleep_between)
        self.commands = commands
        self.max_thread = int(max_thread)
        self.infos = infos if infos is not None else {}
        return self

    def delete(self):
        """
        Delete the command group represented by this model in database.
        """
        ret = self._id
        apiclient = APIClient.getInstance()
        apiclient.delete("group_commands", ret)

    def addInDb(self):
        """
        Add a new command group to pollenisator database.

        Returns: a tuple with :
                * bool for success
                * mongo ObjectId : already existing object if duplicate, create object id otherwise 
        """
        apiclient = APIClient.getInstance()
        res, id = apiclient.insert("group_commands", {
            "name": self.name, "sleep_between": int(self.sleep_between), "commands": self.commands, "max_thread": int(self.max_thread)})
        if not res:
            return False, id
        self._id = id
        return True, id


    @classmethod
    def fetchObject(cls, pipeline):
        """Fetch one command from database and return the CommandGroup object 
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a CommandGroup or None if nothing matches the pipeline.
        """
        apiclient = APIClient.getInstance()
        d = apiclient.findInDb(
            "pollenisator", "group_commands", pipeline, False)
        if d is None:
            return None
        return CommandGroup(d)

    @classmethod
    def fetchObjects(cls, pipeline):
        """Fetch many commands from database and return a Cursor to iterate over CommandGroup objects
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a cursor to iterate on CommandGroup objects
        """
        apiclient = APIClient.getInstance()
        ds = apiclient.findInDb(
            "pollenisator", "group_commands", pipeline, True)
        if ds is None:
            return None
        for d in ds:
            yield CommandGroup(d)

    def update(self, pipeline_set=None):
        """Update this object in database.
        Args:
            pipeline_set: (Opt.) A dictionnary with custom values. If None (default) use model attributes.
        """
        apiclient = APIClient.getInstance()
        if pipeline_set is None:
            # Update in database
            apiclient.update("group_commands", ObjectId(self._id), {"name": self.name, "sleep_between": int(self.sleep_between), "commands": self.commands, "max_thread": int(self.max_thread)})
        else:
            apiclient.update("group_commands",  ObjectId(self._id), pipeline_set)

    @classmethod
    def getList(cls):
        """
        Get all group of command's name registered on database

        Returns:
            Returns the list of command groups name found inside the database. List may be empty.
        """
        apiclient = APIClient.getInstance()
        gcommands = apiclient.findInDb("pollenisator", "group_commands")
        ret = []
        for gcommand in gcommands:
            ret.append(gcommand["name"])
        return ret

    def __str__(self):
        """
        Get a string representation of a command group.

        Returns:
            Returns the string "Command Group".
        """
        return self.name

    def getDbKey(self):
        """Return a dict from model to use as unique composed key.
        Returns:
            A dict (1 key: "_id")
        """
        return {"_id": self._id}
