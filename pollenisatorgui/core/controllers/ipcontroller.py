"""Controller for IP object. Mostly handles conversion between mongo data and python objects"""

from pollenisatorgui.core.controllers.controllerelement import ControllerElement
from pollenisatorgui.core.models.ip import Ip
import json

class IpController(ControllerElement):
    """Inherits ControllerElement
    Controller for IP object. Mostly handles conversion between mongo data and python objects"""

    def doUpdate(self, values):
        """
        Update the Ip represented by this model in database with the given values.

        Args:
            values: A dictionary crafted by IpView containg all form fields values needed.

        Returns:
            The mongo ObjectId _id of the updated Ip document.
        """
        self.model.notes = values.get("Notes", self.model.notes)
        self.model.infos = values.get("Infos", self.model.infos)
        if not isinstance(self.model.infos, dict):
            self.model.infos = json.loads(self.model.infos)
        for info in self.model.infos:
            self.model.infos[info] = self.model.infos[info][0]
        self.model.update()

    def doInsert(self, values):
        """
        Insert the Ip represented by this model in the database with the given values.

        Args:
            values: A dictionary crafted by MultipleIpView or IpView containg all form fields values needed.

        Returns:
            {
                '_id': The mongo ObjectId _id of the inserted command document.
                'nbErrors': The number of objects that has not been inserted in database due to errors.
            }
        """
        # Only multi insert exists at the moment for IP
        try:
            multi = True
        except KeyError:
            multi = False

        if multi:
            # Get form values
            ret = []
            total = 0
            accepted = 0
            for line in values["IPs"].split("\n"):
                if line != "":
                    # Insert in database
                    model = Ip().initialize(line)
                    inserted, iid = model.addInDb()
                    if inserted:
                        ret.append(iid)
                        accepted += 1
                    total += 1
            return ret, total-accepted  # nb errors = total - accepted

    def is_in_scope(self):
        """Return true if the ip has registered at least one scope in its field 'in_scopes' , False otherwise"""
        return bool(self.model.in_scopes)
    
    def getDefects(self):
        """Return ip assigned defects as a list of mongo fetched defects dict
        Returns:
            list of defect raw mongo data dictionnaries
        """
        return self.model.getDefects()

    def getChecks(self):
        """Return ip assigned checks as a list of mongo fetched checks instance
        Returns:
            list of checkInstance objects
        """
        return self.model.getChecks()

    def getPorts(self):
        """Return ip assigned ports as a list of mongo fetched defects dict
        Returns:
            list of defect raw mongo data dictionnaries
        """
        return self.model.getPorts()

    def getType(self):
        """Return a string describing the type of object
        Returns:
            "ip" """
        return "ip"