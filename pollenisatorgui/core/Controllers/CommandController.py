"""Controller for command object. Mostly handles conversion between mongo data and python objects"""
from pollenisatorgui.core.Components.apiclient import APIClient
from pollenisatorgui.core.Controllers.ControllerElement import ControllerElement
import bson

class CommandController(ControllerElement):
    """Inherits ControllerElement
    Controller for command object. Mostly handles conversion between mongo data and python objects"""
    def doUpdate(self, values):
        """
        Update the command represented by this self.model in database with the given values.

        Args:
            values: A dictionary crafted by CommandView containg all form fields values needed.

        Returns:
            The mongo ObjectId _id of the updated command document.
        """
        # Get form values
        self.model.bin_path = values.get(
            "Bin path", self.model.bin_path)
        self.model.plugin = values.get(
            "Plugin", self.model.plugin)
        self.model.text = values.get("Command line options", self.model.text)
        self.model.ports = values.get("Ports/Services", self.model.ports)
        self.model.safe = bool(values.get("Safe", self.model.safe))
        self.model.timeout = str(values.get("Timeout", self.model.timeout))
        types = values.get("Types", {})
        types = [k for k, v in types.items() if v == 1]
        self.model.types = list(types)
        self.model.owner = values.get("owner", "")
        # Update in database
        self.model.update()

    def doInsert(self, values):
        """
        Insert the command represented by this model in the database with the given values.

        Args:
            values: A dictionary crafted by CommandView containg all form fields values needed.

        Returns:
            {
                'Command': The Command object associated
                'nbErrors': The number of objects that has not been inserted in database due to errors.
            }
        """
        # Get form values
        bin_path = values["Bin path"]
        plugin = values["Plugin"]
        text = values["Command line options"]
        ports = values["Ports/Services"]
        name = values["Name"]
        lvl = values["Level"]
        safe = bool(values["Safe"])
        types = values["Types"]
        indb = values["indb"]
        timeout = values["Timeout"]
        owner = values["owner"]
        types = [k for k, v in types.items() if v == 1]
        self.model.initialize(name, bin_path, plugin, 
                              text, lvl, ports, safe, list(types), indb, timeout, owner)
        # Insert in database
        ret, _ = self.model.addInDb()
        if not ret:
            # command failed to be inserted, a duplicate exists
            # return None as inserted_id and 1 error
            return None, 1
        # Fetch the instance of this self.model now that it is inserted.
        return ret, 0  # 0 errors

    def getData(self):
        """Return command attributes as a dictionnary matching Mongo stored commands
        Returns:
            dict with keys name, lvl, safe, text, ports, priority, max_thread, priority, types, _id, tags and infos
        """
        return {"name": self.model.name, "bin_path":self.model.bin_path, "plugin":self.model.plugin, "lvl": self.model.lvl, "safe": bool(self.model.safe), "text": self.model.text,
                "ports": self.model.ports, "timeout": self.model.timeout,
                "types": self.model.types, "indb":self.model.indb, "owner": self.model.owner, "_id": self.model.getId(), "tags": self.model.tags, "infos": self.model.infos}

    def getType(self):
        """Return a string describing the type of object
        Returns:
            "command" """
        return "command"

    def actualize(self):
        """Ask the model to reload its data from database
        """
        if self.model is not None:
            self.model = self.model.__class__.fetchObject(
                {"_id": bson.ObjectId(self.model.getId())}, self.model.indb)

    def addToMyCommands(self, event=None):
        """Add command to current user's commands
        """
        self.model.addToMyCommands()

    def removeFromMyCommands(self, event=None):
        """Remove command from current user's commands
        """
        self.model.removeFromMyCommands()

    def isMine(self):
        return self.model.isMine()

    def isWorker(self):
        return self.model.isWorker()