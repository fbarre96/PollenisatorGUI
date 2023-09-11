"""Controller for command object. Mostly handles conversion between mongo data and python objects"""
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.controllers.controllerelement import ControllerElement
from pollenisatorgui.core.components.settings import Settings
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
        local_bin_path = values.get(
            "My binary path", None)
        if local_bin_path is not None:
            settings = Settings()
            settings.local_settings["my_commands"] = settings.local_settings.get("my_commands", {})
            settings.local_settings["my_commands"][self.model.name] = local_bin_path
            settings.saveLocalSettings()
        self.model.plugin = values.get(
            "Plugin", self.model.plugin)
        self.model.text = values.get("Command line options", self.model.text)
        self.model.timeout = str(values.get("Timeout", self.model.timeout))
        self.model.owners = values.get("owners", [])
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
        name = values["Name"]
        indb = values["indb"]
        timeout = values["Timeout"]
        owners = values["owners"]
        #types = [k for k, v in types.items() if v == 1]
        self.model.initialize(name, bin_path, plugin, 
                              text,  indb, None, timeout, owners)
        # Insert in database
        ret, iid = self.model.addInDb()
        if not ret:
            # command failed to be inserted, a duplicate exists
            # return None as inserted_id and 1 error
            return None, 1
        # Fetch the instance of this self.model now that it is inserted.
        return ret, (0, iid)  # 0 errors

    
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

