"""Controller for Wave object. Mostly handles conversion between mongo data and python objects"""
from pollenisatorgui.core.controllers.controllerelement import ControllerElement


class WaveController(ControllerElement):
    """Inherits ControllerElement
    Controller for Wave object. Mostly handles conversion between mongo data and python objects"""

    def doUpdate(self, values):
        """
        Update the Wave represented by this model in database with the given values.

        Args:
            values: A dictionary crafted by WaveView containg all form fields values needed.

        Returns:
            The mongo ObjectId _id of the updated Wave document.
        """
        wave_commands_dict = values.get("Commands", self.model.wave_commands)
        wave_commands = [k for k, v in wave_commands_dict.items() if v == 1]
        
        self.model.wave_commands = list(wave_commands)
        self.model.update()
        

    def doInsert(self, values):
        """
        Insert the Wave represented by this model in the database with the given values.

        Args:
            values: A dictionary crafted by WaveView containing all form fields values needed.

        Returns:
            {
                '_id': The mongo ObjectId _id of the inserted command document.
                'nbErrors': The number of objects that has not been inserted in database due to errors.
            }
        """
        wave = values["Wave"]
        wave_commands_dict = values["Commands"]
        wave_commands = [k for k, v in wave_commands_dict.items() if v == 1]

        self.model.initialize(wave, wave_commands)
        ret, _ = self.model.addInDb()
        # Update this instance.
        return ret, 0  # 0 erros

    def getData(self):
        """Return wave attributes as a dictionnary matching Mongo stored waves
        Returns:
            dict with keys wave, wave_commands, tags and infos
        """
        return self.model.getData()
    def getIntervals(self):
        """Return scope assigned intervals as a list of mongo fetched intervals dict
        Returns:
            list of defect raw mongo data dictionnaries
        """
        return self.model.getIntervals()

    def getChecks(self):
        """Return wave assigned checks as a list of checkInstance
        Returns:
            list of checkInstance objects
        """
        return self.model.getChecks()

    def getAllTools(self):
        """Return all tools being part of this wave as a list of mongo fetched tools dict.
        Differs from getTools as it fetches all tools of the name and not only tools of level wave.
        Returns:
            list of defect raw mongo data dictionnaries
        """
        return self.model.getAllTools()

    def getScopes(self):
        """Return wave assigned scopes as a list of mongo fetched scopes dict
        Returns:
            list of defect raw mongo data dictionnaries
        """
        return self.model.getScopes()

    def isLaunchableNow(self):
        """Returns True if the tool matches criteria to be launched 
        (current time matches one of interval object assigned to this wave)
        Returns:
            bool
        """
        return self.model.isLaunchableNow()

    def getType(self):
        """Returns a string describing the type of object
        Returns:
            "wave" """
        return "wave"


