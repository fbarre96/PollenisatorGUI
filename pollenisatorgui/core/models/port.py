"""Port Model"""

from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.models.element import Element
from pollenisatorgui.core.models.tool import Tool
from pollenisatorgui.core.models.defect import Defect
from pollenisatorgui.core.components.apiclient import APIClient
from bson.objectid import ObjectId
import webbrowser

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
        super().__init__(valuesFromDb.get("_id", None), valuesFromDb.get("parent", None),  valuesFromDb.get("infos", {}))
        self.initialize(valuesFromDb.get("ip", ""), valuesFromDb.get("port", ""),
                        valuesFromDb.get("proto", "tcp"), valuesFromDb.get(
                            "service", ""), valuesFromDb.get("product", ""),
                        valuesFromDb.get("notes", ""), valuesFromDb.get("infos", {}))

    def initialize(self, ip, port="", proto="tcp", service="", product="", notes="",infos=None):
        """Set values of port
        Args:
            ip: the parent host (ip or domain) where this port is open
            port: a port number as string. Default ""
            proto: a protocol to reach this port ("tcp" by default, send "udp" if udp port.) Default "tcp"
            service: the service running behind this port. Can be "unknown". Default ""
            notes: notes took by a pentester regarding this port. Default ""
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
            apiclient.update("ports", ObjectId(self._id), {"service": self.service, "product":self.product, "notes": self.notes,  "infos": self.infos})
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
        base["infos"] = self.infos
        res, iid = apiclient.insert("ports", base)
        self._id = iid
        
        return res, iid

    def addCustomTool(self, command_iid):
        """
        Add the appropriate tools (level check and wave's commands check) for this port.

        Args:
            command_iid: The command that we want to create all the tools for.
        """
        apiclient = APIClient.getInstance()
        return apiclient.addCustomTool(self._id, command_iid)

    def _getParentId(self):
        """
        Return the mongo ObjectId _id of the first parent of this object. For a port it is the ip.

        Returns:
            Returns the parent ip's ObjectId _id".
        """
        datamanager = DataManager.getInstance()
        obj = datamanager.find("ips", {"ip":self.ip}, False)
        if obj is None:
            return None
        return obj.getId()

    def __str__(self):
        """
        Get a string representation of a port.

        Returns:
            Returns the string protocole/port number.
        """
        return (self.proto+"/" if self.proto == "udp" else "")+str(self.port)+" "+str(self.service)

    def getDetailedString(self):
        """Returns a detailed string describing this port.
        Returns:
            string : ip:proto/port
        """
        return str(self.ip)+":"+str(self)

    def getURL(self):
        ssl = self.infos.get("SSL", None) == "True" or ("https" in self.service or "ssl" in self.service)
        url = "https://" if ssl else "http://"
        url += self.ip+":"+self.port+"/"
        return url

    def getDefects(self):
        """Return port assigned defects as a list of mongo fetched defects dict
        Returns:
            list of defect raw mongo data dictionnaries
        """
        datamanager = DataManager.getInstance()
        return datamanager.find("defects", {"ip": self.ip, "port": self.port, "proto": self.proto})

    def getDbKey(self):
        """Return a dict from model to use as unique composed key.
        Returns:
            A dict (3 keys :"ip", "port", "proto")
        """
        return {"ip": self.ip, "port": self.port, "proto": self.proto}

    def getData(self):
        """Return port attributes as a dictionnary matching Mongo stored ports
        Returns:
            dict with keys ip, port, proto, service, product, notes, _id, tags and infos
        """
        return {"ip": self.ip, "port": self.port, "proto": self.proto,
                "service": self.service, "product": self.product, "notes": self.notes, "_id": self.getId(), "infos": self.infos}

    def openInBrowser(self, _event=None):
        """Callback for action open in browser
        Args:
            _event: nut used but mandatory
        """
        if self.service == "http":
            webbrowser.open_new_tab(
                "http://"+self.ip+":"+self.port)
        else:
            webbrowser.open_new_tab(
                "https://"+self.ip+":"+self.port)