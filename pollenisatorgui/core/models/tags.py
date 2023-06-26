"""Tag Model. Tag other stuff with it"""

from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.models.element import Element
from pollenisatorgui.core.components.apiclient import APIClient
import pollenisatorgui.core.components.utils as utils
from bson.objectid import ObjectId


class Tag(Element):
    """
    Represents an interval object that defines an time interval where a wave can be executed.

    Attributes:
        coll_name: collection name in pollenisator database
    """
    coll_name = "tags"

    def __init__(self, valuesFromDb=None):
        """Constructor
        Args:
            valueFromDb: a dict holding values to load into the object. A mongo fetched interval is optimal.
                        possible keys with default values are : _id (None), item_id, item_type, tags([]), date
        """
        if valuesFromDb is None:
            valuesFromDb = {}
        super().__init__(valuesFromDb.get("_id", None), None, {})
        self.initialize(valuesFromDb.get("item_id", None), valuesFromDb.get("item_type", None), valuesFromDb.get("tags",[]), valuesFromDb.get("date", None))

    def initialize(self, item_id, item_type, tags, date):
        """Set values of interval
        Args:
            wave: the parent wave name
            dated: a starting date and tiem for this interval in format : '%d/%m/%Y %H:%M:%S'. or the string "None"
            datef: an ending date and tiem for this interval in format : '%d/%m/%Y %H:%M:%S'. or the string "None"
            infos: a dictionnary with key values as additional information. Default to None
        Returns:
            this object
        """
        self.item_id = item_id
        self.item_type = item_type
        self.tags = tags
        self.date = date
        return self

    def delete(self):
        """
        Delete the Interval represented by this model in database.
        """
        apiclient = APIClient.getInstance()
        apiclient.delete(
            "tags", self._id)
        
    @staticmethod
    def addTagTo(item_id, item_type, tag, overrideGroups=True):
        apiclient = APIClient.getInstance()
        apiclient.addTag(item_id, item_type, tag, overrideGroups)
    
    @staticmethod
    def delTag(item_id, item_type, tag):
        apiclient = APIClient.getInstance()
        apiclient.delTag(item_id, item_type, tag)

    @staticmethod
    def setTags(item_id, item_type, tags):
        apiclient = APIClient.getInstance()
        apiclient.setTags(item_id, item_type, tags)

    def getData(self):
        """Return interval attributes as a dictionnary matching Mongo stored intervals
        Returns:
            dict with keys _id, item_id, item_type, tags, date
        """
        return {"item_type": self.item_type, "item_id": self.item_id, "date": self.date, "_id": self.getId(), "tags": self.tags}

