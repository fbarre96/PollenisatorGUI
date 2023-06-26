"""Remark Model."""

import os
from bson.objectid import ObjectId
from pollenisatorgui.core.models.element import Element
from pollenisatorgui.core.components.apiclient import APIClient
import json

class Remark(Element):
    """
    Represents a Remark object that defines a synthesis point. A Remark is a note added by a pentester on a report to complete the defect section.

    Attributes:
        coll_name: collection name in pollenisator database
    """
    coll_name = "remarks"

    def __init__(self, valuesFromDb=None):
        """Constructor
        Args:
            valueFromDb: a dict holding values to load into the object. A mongo fetched remark is optimal.
                        possible keys with default values are : _id (None), 
                        type("Positive|Negative|Neutral"), title("")
        """
        if valuesFromDb is None:
            valuesFromDb = {}
        super().__init__(valuesFromDb.get("_id", None), None, {})
        self.initialize(valuesFromDb.get("type", "Positive"), valuesFromDb.get("title", ""), valuesFromDb.get("description", ""))

    def initialize(self, typeof, title, description):
        """Set values of remark
        Args:
            type: the type of the remark (Positive, Neutral or Negative)
            title: a title for this remark
            description: a description
        Returns:
            this object
        """
        self.title = title
        self.type = typeof
        self.description = description
        return self

    def delete(self):
        """
        Delete the remark represented by this model in database.
        """
        ret = self._id
        apiclient = APIClient.getInstance()
        apiclient.deleteFromDb(apiclient.getCurrentPentest(),"remarks", {"_id": ObjectId(ret)})

    def addInDb(self):
        """
        Add this defect to pollenisator database.
        Returns: a tuple with :
                * bool for success
                * mongo ObjectId : already existing object if duplicate, create object id otherwise 
        """
        base = self.getDbKey()
        # add to base parameters defined or not depending on the lvl.
        # Checking unicity
        apiclient = APIClient.getInstance()
        existing = apiclient.findInDb(apiclient.getCurrentPentest(), "remarks", base, False)
        if existing is not None:
            return False, existing["_id"]

        # Those are added to base after tool's unicity verification

        base["type"] = self.type
        base["title"] = self.title
        base["description"] = self.description
        # Get parent for notifications
        res = apiclient.insertInDb(apiclient.getCurrentPentest(), "remarks", base, notify=True)
        self._id = ObjectId(res)
        return True, self._id

    def update(self, pipeline_set=None):
        """Update this object in database.
        Args:
            pipeline_set: (Opt.) A dictionnary with custom values. If None (default) use model attributes.
        """
        apiclient = APIClient.getInstance()
        if pipeline_set is None:
            apiclient.updateInDb(apiclient.getCurrentPentest(), "remarks", {"_id":ObjectId(self._id)}, {"$set":{"type": self.type, "title": self.title, "description": self.description}})
        else:
            apiclient.updateInDb(apiclient.getCurrentPentest(),  {"_id":ObjectId(self._id)}, ObjectId(self._id), pipeline_set)

    def getData(self):
        """Return defect attributes as a dictionnary matching Mongo stored defects
        Returns:
            dict with keys title, ease, ipact, risk, redactor, type, notes, ip, port, proto, proofs, _id, tags, infos
        """
        return {"title": self.title, "type": self.type, "description": self.description}


    def _getParent(self):
        """
        Return the mongo ObjectId _id of the first parent of this object. For a Defect it is either an ip or a port depending on the Defect's level.

        Returns:
            Returns the parent's ObjectId _id".
        """
        return None
    
    def getParent(self):
        return None


    def __str__(self):
        """
        Get a string representation of a defect.

        Returns:
            Returns the defect +title.
        """
        return self.title

    def getDbKey(self):
        """Return a dict from model to use as unique composed key.
        Returns:
            A dict (1 key : "title")
        """
        return {"title": self.title}

