"""Controller for Port object. Mostly handles conversion between mongo data and python objects"""

from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.controllers.controllerelement import ControllerElement
import json

class PortController(ControllerElement):
    """Inherits ControllerElement
    Controller for Port object. Mostly handles conversion between mongo data and python objects"""

    def doUpdate(self, values):
        """
        Update the Port represented by this model in database with the given values.

        Args:
            values: A dictionary crafted by PortView containg all form fields values needed.

        Returns:
            The mongo ObjectId _id of the updated Port document.
        """
        self.model.service = values.get("Service", self.model.service)
        self.model.product = values.get("Product", self.model.product)
        self.model.notes = values.get("Notes", self.model.notes)
        self.model.infos = json.loads(values.get("Infos", self.model.infos))
        self.model.update()

    def doInsert(self, values):
        """
        Insert the Port represented by this model in the database with the given values.

        Args:
            values: A dictionary crafted by PortView containg all form fields values needed.

        Returns:
            {
                '_id': The mongo ObjectId _id of the inserted command document.
                'nbErrors': The number of objects that has not been inserted in database due to errors.
            }
        """
        # get form values
        port = values["Number"]
        proto = values["Proto"]
        service = values["Service"]
        product = values["Product"]
        notes = values["Product"]
        # Add the port in database
        self.model.initialize(values["ip"], port, proto, service, product, notes=notes)
        ret = self.model.addInDb()
        return ret, 0  # 0 errors

    
    def addCustomTool(self, command_iid):
        """Add command iid to instantiate as a tool in the model 
        Args:
            command_iid:  command iid of the command to instantiate as a tool in the model 
        """
        self.model.addCustomTool(command_iid)

    def getDefects(self):
        """Return port assigned defects as a list of mongo fetched defects dict
        Returns:
            list of defect raw mongo data dictionnaries
        """
        return self.model.getDefects()

    def getChecks(self):
        """Return ports assigned checks as a list of mongo fetched checks
        Returns:
            list of checkInstance objects
        """
        return self.model.getChecks()
    
    @classmethod
    def getDefectsForPorts(self, ports):
        datamanager = DataManager.getInstance()
        return datamanager.find("defect", {"target_iid": {"$in": [str(port.getId()) for port in ports]}})

    @classmethod
    def getChecksForPorts(self, ports):
        datamanager = DataManager.getInstance()
        return datamanager.find("checkinstance", {"target_iid": {"$in": [str(port.getId()) for port in ports]}})
    
    def getType(self):
        """Returns a string describing the type of object
        Returns:
            "port" """
        return "port"