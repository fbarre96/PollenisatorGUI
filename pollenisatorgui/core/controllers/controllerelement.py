"""Controller for model object. Mostly handles conversion between mongo data and python objects"""

from bson.objectid import ObjectId
from pollenisatorgui.core.components.apiclient import APIClient

from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.models.tags import Tag


class ControllerElement:
    """Controller for model object. Mostly handles conversion between mongo data and python objects"""
    def __init__(self, model):
        """Constructor
        Args:
            model: Any instance of classe that inherits core.Models.Element"""
        self.model = model

    def getDbId(self):
        """Returns the mongo database id of the model object
        Returns:
            bson.objectid ObjectId or None if self.model is None
        """
        if self.model is not None:
            return self.model.getId()
        return None

    def getParentId(self):
        """Return the parent object database id of the model. E.G a port would returns its parent IP mongo id
        Returns:
            None if model is None
            bson.objectid ObjectId of the parent object
        """
        if self.model is None:
            return None
        return self.model.getParentId()

    def getData(self):
        if self.model is None:
            return {}
        return self.model.getData()

    def doDelete(self):
        """Ask the model to delete itself from database
        """
        self.model.delete()

    def actualize(self):
        """Ask the model to reload its data from database
        """
        if self.model is not None:
            self.model = self.model.__class__.fetchObject(
                {"_id": ObjectId(self.model.getId())})

    def update(self):
        """Update object in database with model data
        """
        self.model.update()

    def updateInfos(self, infos):
        """Update object in database with given dictionnary
        Args:
            infos: a dictionnary with updated values for this object.
        """
        self.model.updateInfos(infos)

    def getModelRepr(self, detailed=False):
        """Returns a string representation of the model
        Returns:
            a string conversion of the model
        """
        try:
            if detailed:
                return self.model.getDetailedString()
            return str(self.model)
        except TypeError:
            return "Error"

    def getTags(self):
        """Returns a list of string decribing tags
        Returns:
            list of string
        """
        if self.model is None:
            return
        datamanager = DataManager.getInstance()
        res = datamanager.find("tags", {"item_id":ObjectId(self.model.getId())}, multi=False, fetch_on_none=False)
        if res is None:
            return []
        return res.tags

    def addTag(self, newTag, overrideGroupe=True):
        """Add the given tag to this object.
        Args:
            newTag: a new tag as a string to be added to this model tags
            overrideGroupe: Default to True. If newTag is in a group with a tag already assigned to this object, it will replace this old tag.
        """
        Tag.addTagTo(self.getDbId(), self.getType(), newTag, overrideGroupe)

    def delTag(self, tagToDelete):
        """Delete the given tag in this object.
        Args:
            tagToDelete: a tag as a string to be deleted from this model tags
        """
        Tag.delTag(self.getDbId(), self.getType(), tagToDelete)

    def setTags(self, tags):
        """Change all tags for the given new ones and update database
        Args:
            tags: a list of tag string
        """
        Tag.setTags(self.getDbId(), self.getType(), tags)

    def getDetailedString(self):
        """Return a string describing the model with more info than getModelRepr. E.G a port goes from "tcp/80" to "IP.IP.IP.IP tcp/80"
        Returns:
            a detailed string conversion of the model
        """
        return self.model.getDetailedString()

    def getType(self):
        """Return a string describing the type of object
        Returns:
            "element" """
        return "element"