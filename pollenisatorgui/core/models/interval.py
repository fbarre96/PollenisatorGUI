"""Interval Model. Useful to limit in a time frame some tools"""

from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.models.element import Element
from pollenisatorgui.core.models.tool import Tool
from pollenisatorgui.core.components.apiclient import APIClient
import pollenisatorgui.core.components.utils as utils
from bson.objectid import ObjectId
from datetime import datetime


class Interval(Element):
    """
    Represents an interval object that defines an time interval where a wave can be executed.

    Attributes:
        coll_name: collection name in pollenisator database
    """
    coll_name = "intervals"

    def __init__(self, valuesFromDb=None):
        """Constructor
        Args:
            valueFromDb: a dict holding values to load into the object. A mongo fetched interval is optimal.
                        possible keys with default values are : _id (None), parent (None), tags([]), infos({}),
                        wave(""), dated("None"), datef("None")
        """
        if valuesFromDb is None:
            valuesFromDb = {}
        super().__init__(valuesFromDb.get("_id", None), valuesFromDb.get("parent", None),  valuesFromDb.get("infos", {}))
        self.initialize(valuesFromDb.get("wave", ""), valuesFromDb.get("dated", "None"),
                        valuesFromDb.get("datef", "None"), valuesFromDb.get("infos", {}))

    def initialize(self, wave, dated="None", datef="None", infos=None):
        """Set values of interval
        Args:
            wave: the parent wave name
            dated: a starting date and tiem for this interval in format : '%d/%m/%Y %H:%M:%S'. or the string "None"
            datef: an ending date and tiem for this interval in format : '%d/%m/%Y %H:%M:%S'. or the string "None"
            infos: a dictionnary with key values as additional information. Default to None
        Returns:
            this object
        """
        self.wave = wave
        self.dated = dated
        self.datef = datef
        self.infos = infos if infos is not None else {}
        return self

    def delete(self):
        """
        Delete the Interval represented by this model in database.
        """
        apiclient = APIClient.getInstance()
        apiclient.delete(
            "intervals", self._id)
        

    def addInDb(self):
        """
        Add this interval in database.

        Returns: a tuple with :
                * bool for success
                * mongo ObjectId : already existing object if duplicate, create object id otherwise 
        """
        base = {"wave": self.wave, "dated": self.dated, "datef": self.datef}
        apiclient = APIClient.getInstance()
        res, iid = apiclient.insert("intervals", base)
        self._id = iid
        return True, iid

    def update(self, pipeline_set=None):
        """Update this object in database.
        Args:
            pipeline_set: (Opt.) A dictionnary with custom values. If None (default) use model attributes.
        """
        
        apiclient = APIClient.getInstance()
        if pipeline_set is None:
            apiclient.update("intervals", ObjectId(self._id), {"dated": self.dated, "datef": self.datef})
        else:
            apiclient.update("intervals", ObjectId(self._id), pipeline_set)

    def _getParentId(self):
        """
        Return the mongo ObjectId _id of the first parent of this object. For an interval it is the wave.

        Returns:
            Returns the parent wave's ObjectId _id".
        """
        datamanager = DataManager.getInstance()
        obj = datamanager.find("waves", {"wave": self.wave}, False)
        if obj is None:
            return None
        return obj["_id"]

    def getData(self):
        """Return interval attributes as a dictionnary matching Mongo stored intervals
        Returns:
            dict with keys wave, dated, datef, _id, tags and infos
        """
        return {"wave": self.wave, "dated": self.dated, "datef": self.datef, "_id": self.getId(), "infos": self.infos}


    def __str__(self):
        """
        Get a string representation of an interval

        Returns:
            Returns the string "Interval".
        """
        return "Interval"

    @classmethod
    def _translateDateString(cls, datestring):
        """Returns the datetime object when given a str wih format '%d/%m/%Y %H:%M:%S'
        Args:
            a string formated as datetime format : '%d/%m/%Y %H:%M:%S'
        """
        ret = None
        if(type(datestring) == str or type(datestring) == str):
            if datestring != "None":
                ret = datetime.strptime(
                    datestring, '%d/%m/%Y %H:%M:%S')
        return ret

    def getEndingDate(self):
        """Returns the ending date and time of this interval
        Returns:
            a datetime object.
        """
        return Interval._translateDateString(self.datef)
    
    def getStartingDate(self):
        """Returns the starting date and time of this interval
        Returns:
            a datetime object.
        """
        return Interval._translateDateString(self.dated)

    def getDbKey(self):
        """Return a dict from model to use as unique composed key.
        Returns:
            A dict (1 key :"wave")
        """
        return {"wave": self.wave}
