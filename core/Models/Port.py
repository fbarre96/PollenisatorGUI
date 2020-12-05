"""Port Model"""

from core.Models.Element import Element
from core.Models.Tool import Tool
from core.Models.Defect import Defect
from core.Components.apiclient import APIClient
from bson.objectid import ObjectId


class Port(Element):
    """
    Represents an Port object that defines an Port that will be targeted by port level tools.

    Attributes:
        coll_name: collection name in pollenisator database
    """
    coll_name = "ports"

    def __init__(self, valuesFromDb=None):
        """Constructor
        Args:
            valueFromDb: a dict holding values to load into the object. A mongo fetched interval is optimal.
                        possible keys with default values are : _id (None), parent (None), tags([]), infos({}),
                        ip(""), port(""), proto("tcp"), service(""), product(""), notes("")
        """
        if valuesFromDb is None:
            valuesFromDb = {}
        super().__init__(valuesFromDb.get("_id", None), valuesFromDb.get("parent", None), valuesFromDb.get(
            "tags", []), valuesFromDb.get("infos", {}))
        self.initialize(valuesFromDb.get("ip", ""), valuesFromDb.get("port", ""),
                        valuesFromDb.get("proto", "tcp"), valuesFromDb.get(
                            "service", ""), valuesFromDb.get("product", ""),
                        valuesFromDb.get("notes", ""), valuesFromDb.get("tags", []), valuesFromDb.get("infos", {}))

    def initialize(self, ip, port="", proto="tcp", service="", product="", notes="", tags=None, infos=None):
        """Set values of port
        Args:
            ip: the parent host (ip or domain) where this port is open
            port: a port number as string. Default ""
            proto: a protocol to reach this port ("tcp" by default, send "udp" if udp port.) Default "tcp"
            service: the service running behind this port. Can be "unknown". Default ""
            notes: notes took by a pentester regarding this port. Default ""
            tags: a list of tag. Default is None (empty array)
            infos: a dictionnary of additional info. Default is None (empty dict)
        Returns:
            this object
        """
        self.ip = ip
        self.port = port
        self.proto = proto
        self.service = service
        self.product = product
        self.notes = notes
        self.infos = infos if infos is not None else {}
        self.tags = tags if tags is not None else []
        return self

    def delete(self):
        """
        Deletes the Port represented by this model in database.
        Also deletes the tools associated with this port
        Also deletes the defects associated with this port
        """
        apiclient = APIClient.getInstance()
        
        apiclient.delete("ports", ObjectId(self._id))

    def update(self, pipeline_set=None):
        """Update this object in database.
        Args:
            pipeline_set: (Opt.) A dictionnary with custom values. If None (default) use model attributes.
        """
        apiclient = APIClient.getInstance()
        # Update variable instance. (this avoid to refetch the whole command in database)
        if pipeline_set is None:
            apiclient.update("ports", ObjectId(self._id), {"service": self.service, "product":self.product, "notes": self.notes, "tags": self.tags, "infos": self.infos})
        else:
            apiclient.update("ports", ObjectId(self._id),  pipeline_set)

    def addInDb(self):
        """
        Add this Port in database.

        Returns: a tuple with :
                * bool for success
                * mongo ObjectId : already existing object if duplicate, create object id otherwise 
        """
        base = self.getDbKey()
        apiclient = APIClient.getInstance()
        # Inserting port
        base["service"] = self.service
        base["product"] = self.product
        base["notes"] = self.notes
        base["tags"] = self.tags
        base["infos"] = self.infos
        res, iid = apiclient.insert("ports", base)
        self._id = iid
        
        return res, iid

    def addCustomTool(self, command_name):
        """
        Add the appropriate tools (level check and wave's commands check) for this port.

        Args:
            command_name: The command that we want to create all the tools for.
        """
        apiclient = APIClient.getInstance()
        return apiclient.addCustomTool(self._id, command_name)

    def _getParentId(self):
        """
        Return the mongo ObjectId _id of the first parent of this object. For a port it is the ip.

        Returns:
            Returns the parent ip's ObjectId _id".
        """
        apiclient = APIClient.getInstance()
        return apiclient.find("ips", {"ip": self.ip}, False)["_id"]

    def __str__(self):
        """
        Get a string representation of a port.

        Returns:
            Returns the string protocole/port number.
        """
        return self.proto+"/"+str(self.port)

    def getDetailedString(self):
        """Returns a detailed string describing this port.
        Returns:
            string : ip:proto/port
        """
        return str(self.ip)+":"+str(self)

    def getTools(self):
        """Return port assigned tools as a list of mongo fetched defects dict
        Returns:
            list of tool raw mongo data dictionnaries
        """
        apiclient = APIClient.getInstance()
        return apiclient.find("tools", {"lvl": "port", "ip": self.ip, "port": self.port, "proto": self.proto})

    def getDefects(self):
        """Return port assigned defects as a list of mongo fetched defects dict
        Returns:
            list of defect raw mongo data dictionnaries
        """
        apiclient = APIClient.getInstance()
        return apiclient.find("defects", {"ip": self.ip, "port": self.port, "proto": self.proto})

    def getDbKey(self):
        """Return a dict from model to use as unique composed key.
        Returns:
            A dict (3 keys :"ip", "port", "proto")
        """
        return {"ip": self.ip, "port": self.port, "proto": self.proto}
