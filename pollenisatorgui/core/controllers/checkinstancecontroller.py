"""Controller for command object. Mostly handles conversion between mongo data and python objects"""
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.controllers.controllerelement import ControllerElement
import bson

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

    def getCheckInstanceStatus(self):
        return self.model.getCheckInstanceStatus()

    def getCheckInstanceInfo(self):
        return APIClient.getInstance().getCheckInstanceInfo(self.model.getId())

    def getType(self):
        """Return a string describing the type of object
        Returns:
            "checkinstance" """
        return "checkinstance"

    def getStatus(self):
        return self.model.getStatus()
    
    def swapStatus(self):
        curr = self.getStatus()
        if curr == "done":
            self.model.status = "todo"
        elif curr == "todo" or curr == "running" or curr == "":
            self.model.status = "done"
        else:
            return
        self.model.update({"status": self.model.status})

    @property
    def target_repr(self):
        if hasattr(self.model, "target_repr"):
            return self.model.target_repr
        reprs = APIClient.getInstance().getCheckInstanceRepr([str(self.model.getId())])
        if reprs:
            self.model.target_repr = reprs.get(str(self.model.target_iid), str(self.model))
        else:
            self.model.target_repr = str(self)
        return self.model.target_repr
    
    @target_repr.setter
    def target_repr(self, value):
        self.model.target_repr = value

    def getCategory(self):
        return self.model.check_m.category
    
    def getTarget(self):
        return self.model.target_iid
    
    def getTools(self):
        return self.model.getTools()
        
    def isAuto(self):
        return self.model.check_m.isAuto()

    def actualize(self):
        """Ask the model to reload its data from database
        """
        if self.model is not None:
            self.model = self.model.__class__.fetchObject({"_id": bson.ObjectId(self.model.getId())})

   