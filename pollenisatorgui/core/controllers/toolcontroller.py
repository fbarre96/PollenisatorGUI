"""Controller for Tool object. Mostly handles conversion between mongo data and python objects"""
from pollenisatorgui.core.controllers.controllerelement import ControllerElement


class ToolController(ControllerElement):
    """Inherits ControllerElement
    Controller for Tool object. Mostly handles conversion between mongo data and python objects"""

    def doUpdate(self, values):
        """
        Update the Tool represented by this model in database with the given values.

        Args:
            values: A dictionary crafted by ToolView containg all form fields values needed.

        Returns:
            The mongo ObjectId _id of the updated Tool document.
        """
        # Get form values
        dated = values.get("Start date", self.model.dated)
        datef = values.get("End date", self.model.datef)
        self.model.scanner_ip = values.get("Scanner", self.model.scanner_ip)
        self.model.notes = values.get("Notes", self.model.notes)
        # update fetched instance before update, in case there's a Hook after update.
        self.model.dated = dated
        self.model.datef = datef
        # Updating
        self.update()

    def getStatus(self):
        """Returns a string describing the tool current status
        Returns:
            string with possible values : "OOS"/"OOT"/"running"/"done". OOS = Out of Scope, OOT = Out of Time range
        """
        return self.model.getStatus()
        
    def setStatus(self, status):
        """Set the tool model status
        Args:
            status: string with possible values : "OOS"/"OOT"/"running"/"done". OOS = Out of Scope, OOT = Out of Time range
        """
        self.model.setStatus(status)

    def getName(self):
        """Returns the model tool name
        Returns: 
            string
        """
        return self.model.name

    
    def getOutputDir(self, pentestName):
        """Returns directory of the tool file output 
        Args:
            pentestName: the pentest database name
        Returns:
            string (path)
        """
        return self.model.getOutputDir(pentestName)

    def getResultFile(self):
        """Returns path of the tool resulting file output
        Returns:
            string (path)
        """
        return self.model.getResultFile()

    def markAsNotDone(self):
        """Change this model tool to status not done. (resets dates and scanner)
        """
        self.model.markAsNotDone()

    def getType(self):
        """Returns a string describing the type of object
        Returns:
            "tool" """
        return "tool"