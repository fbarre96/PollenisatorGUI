"""Wave Model. Stores which command should be launched and associates Interval and Scope"""

from bson.objectid import ObjectId
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.models.tool import Tool
from pollenisatorgui.core.models.element import Element
from pollenisatorgui.core.models.ip import Ip
from pollenisatorgui.core.models.interval import Interval
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.models.scope import Scope
from pollenisatorgui.core.components.apiclient import APIClient


class Wave(Element):
    """
    Represents a Wave object. A wave is a series of tools to execute.

    Attributes:
        coll_name: collection name in pollenisator database
    """
    coll_name = "waves"

    def __init__(self, valuesFromDb=None):
        """Constructor
        Args:
            valueFromDb: a dict holding values to load into the object. A mongo fetched interval is optimal.
                        possible keys with default values are : _id(None), parent(None), tags([]), infos({}),
                        wave(""), wave_commands([])
        """
        if valuesFromDb is None:
            valuesFromDb = {}
        super().__init__(valuesFromDb.get("_id", None), valuesFromDb.get("parent", None), valuesFromDb.get("infos", {}))
        self.initialize(valuesFromDb.get("wave", ""),
                        valuesFromDb.get("wave_commands", []), valuesFromDb.get("infos", {}))

    def initialize(self, wave="", wave_commands=None, infos=None):
        """Set values of scope
        Args:
            wave: the wave name, default is ""
            wave_commands: a list of command name that are to be launched in this wave. Defaut is None (empty list)
            infos: a dictionnary of additional info. Default is None (empty dict)
        Returns:
            this object
        """
        self.wave = wave
        self.wave_commands = wave_commands if wave_commands is not None else []
        self.infos = infos if infos is not None else {}
        return self

    def getData(self):
        return{"wave": self.wave, "wave_commands": self.wave_commands, "_id": self.getId(), "infos": self.infos}


    def delete(self):
        """
        Delete the wave represented by this model in database.
        Also delete the tools, intervals, scopes associated with this wave
        """
        apiclient = APIClient.getInstance()
        apiclient.delete("waves", ObjectId(self._id))

    def addInDb(self):
        """
        Add this wave in database.
        Returns: a tuple with :
                * bool for success
                * mongo ObjectId : already existing object if duplicate, create object id otherwise 
        """
        apiclient = APIClient.getInstance()
        res, iid = apiclient.insert(
            "waves", {"wave": self.wave, "wave_commands": list(self.wave_commands)})
        self._id = iid
        return res, iid

    def update(self, pipeline_set=None):
        """Update this object in database.
        Args:
            pipeline_set: (Opt.) A dictionnary with custom values. If None (default) use model attributes.
        """
        apiclient = APIClient.getInstance()
        if pipeline_set is None:
            apiclient.update("waves", ObjectId(self._id), {"wave_commands": list(self.wave_commands)})
        else:
            apiclient.update("waves", ObjectId(self._id), pipeline_set)


    def __str__(self):
        """
        Get a string representation of a wave.

        Returns:
            Returns the wave id (name).
        """
        return self.wave

 

    def getAllTools(self):
        """Return all tools being part of this wave as a list of mongo fetched tools dict.
        Differs from getTools as it fetches all tools of the name and not only tools of level wave.
        Returns:
            list of defect raw mongo data dictionnaries
        """
        return Tool.fetchObjects({"wave": self.wave})

    def getIntervals(self):
        """Return scope assigned intervals as a list of mongo fetched intervals dict
        Returns:
            list of defect raw mongo data dictionnaries
        """
        datamanager = DataManager.getInstance()
        return datamanager.find("intervals",
                                  {"wave": self.wave})

    def getScopes(self):
        """Return wave assigned scopes as a list of mongo fetched scopes dict
        Returns:
            list of defect raw mongo data dictionnaries
        """
        datamanager = DataManager.getInstance()
        return datamanager.find("scopes", {"wave": self.wave})

    def getDbKey(self):
        """Return a dict from model to use as unique composed key.
        Returns:
            A dict (1 key :"wave")
        """
        return {"wave": self.wave}

    def isLaunchableNow(self):
        """Returns True if the tool matches criteria to be launched 
        (current time matches one of interval object assigned to this wave)
        Returns:
            bool
        """
        intervals = Interval.fetchObjects({"wave": self.wave})
        for intervalModel in intervals:
            if utils.fitNowTime(intervalModel.dated, intervalModel.datef):
                return True
        return False



    @classmethod
    def listWaves(cls):
        """Return all waves names as a list 
        Returns:
            list of all wave names
        """
        ret = []
        datamanager = DataManager.getInstance()
        waves = datamanager.get("waves", '*')
        for wave in waves:
            ret.append(wave["wave"])
        return ret

  
