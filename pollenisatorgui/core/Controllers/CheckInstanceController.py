"""Controller for command object. Mostly handles conversion between mongo data and python objects"""
from turtle import title
from pollenisatorgui.core.Components.apiclient import APIClient
from pollenisatorgui.core.Controllers.ControllerElement import ControllerElement
import bson
import json

class CheckInstanceController(ControllerElement):
    """Inherits ControllerElement
    Controller for CheckInstance object. Mostly handles conversion between mongo data and python objects"""
    def doUpdate(self, values):
        """
        Update the command represented by this self.model in database with the given values.

        Args:
            values: A dictionary crafted by CheckInstanceView containg all form fields values needed.

        Returns:
            The mongo ObjectId _id of the updated command document.
        """
        # Get form values
        self.model.status = values.get(
            "Status", self.model.status)
        self.model.notes = values.get(
            "Notes", self.model.notes)
        # Update in database
        self.model.update()

    def getData(self):
        """Return command attributes as a dictionnary matching Mongo stored commands
        Returns:
            dict with keys name, lvl, safe, text, ports, priority, max_thread, priority, types, _id, tags and infos
        """
        return self.model.getData()

    def getCheckItem(self):
        return self.model.getCheckItem()

    def getCheckInstanceInfos(self):
        apiclient = APIClient.getInstance()
        return apiclient.getCheckInstanceInfos(self.model.getId())

    def getType(self):
        """Return a string describing the type of object
        Returns:
            "checkinstance" """
        return "checkinstance"

    def getStatus(self):
        return self.model.status

    def getCategory(self):
        return self.model.check_m.category
    
    def getTarget(self):
        return self.model.target_iid

    def getTools(self):
        return self.model.getTools()
        
    def actualize(self):
        """Ask the model to reload its data from database
        """
        if self.model is not None:
            self.model = self.model.__class__.fetchObject({"_id": bson.ObjectId(self.model.getId())})

   