"""Controller for remark object. Mostly handles conversion between mongo data and python objects"""

import os
from pollenisatorgui.core.Controllers.ControllerElement import ControllerElement


class RemarkController(ControllerElement):
    """Inherits ControllerElement
    Controller for remark object. Mostly handles conversion between mongo data and python objects"""

    def doUpdate(self, values):
        """
        Update the Remark represented by this model in database with the given values.

        Args:
            values: A dictionary crafted by RemarkView containg all form fields values needed.

        Returns:
            The mongo ObjectId _id of the updated Remark document.
        """
        self.model.title = values.get("Title", self.model.title)
        self.model.type = values.get("Type", self.model.type)
        self.model.description = values.get("Description", self.model.description)
        # Updating
        self.model.update()

    def doInsert(self, values):
        """
        Insert the Remark represented by this model in the database with the given values.

        Args:
            values: A dictionary crafted by RemarkView containing all form fields values needed.

        Returns:
            {
                '_id': The mongo ObjectId _id of the inserted command document.
                'nbErrors': The number of objects that has not been inserted in database due to errors.
            }
        """
        title = values["Title"]
        typeof = values["Type"]
        description = values["Description"]
        self.model.initialize(typeof, title, description)
        ret, _ = self.model.addInDb()

        return ret, 0  # 0 erros

    def getData(self):
        """Return defect attributes as a dictionnary matching Mongo stored defects
        Returns:
            dict with keys title, ease, ipact, risk, redactor, type, notes, ip, port, proto, proofs, _id, tags, infos
        """
        if self.model is None:
            return None
        return {"title": self.model.title, "type": self.model.type, "description": self.model.description}

    def getType(self):
        """Returns a string describing the type of object
        Returns:
            "remark" """
        return "remark"