"""Controller for Scope object. Mostly handles conversion between mongo data and python objects"""

import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.controllers.controllerelement import ControllerElement
from pollenisatorgui.core.models.scope import Scope


class ScopeController(ControllerElement):
    """Inherits ControllerElement
    Controller for Scope object. Mostly handles conversion between mongo data and python objects"""

    def doUpdate(self, values):
        """
        Update the Scope represented by this model in database with the given values.

        Args:
            values: A dictionary crafted by ScopeView containg all form fields values needed.

        Returns:
            The mongo ObjectId _id of the updated Scope document.
        """
        self.model.notes = values.get("Notes", self.model.notes)
        self.model.update()

    def doInsert(self, values):
        """
        Insert the Scope represented by this model in the database with the given values.

        Args:
            values: A dictionary crafted by MultipleScopeView or ScopeView containg all form fields values needed.

        Returns:
            {
                '_id': The mongo ObjectId _id of the inserted command document.
                'nbErrors': The number of objects that has not been inserted in database due to errors.
            }
        """
        # Only multi insert exists at the moment for Scope
        # Get form values
        wave = values["wave"]
        ret = []
        total = 0
        accepted = 0
        insert_setting = values["Settings"]
        split_range_setting = values.get("Split", False)
        for line in values["Scopes"].split("\n"):
            if line.strip() != "":
                # Insert in database
                scopeToAdd = line.strip()
                if utils.isIp(scopeToAdd):
                    scopeToAdd += "/32"
                if utils.isNetworkIp(scopeToAdd):
                    if split_range_setting:
                        network_ips = utils.splitRange(scopeToAdd)
                        if len(network_ips) == 0:
                            model = Scope().initialize(wave, scopeToAdd, "")
                            inserted_res, iid = model.addInDb()
                        else:
                            for network_ip in network_ips:
                                model = Scope().initialize(wave,  str(network_ip), "")
                                inserted_res, iid = model.addInDb()
                                if inserted_res:
                                    accepted += 1
                                    ret.append(iid)
                                total += 1
                    else:
                        model = Scope().initialize(wave,  scopeToAdd, "")
                        inserted_res, iid = model.addInDb()
                else:
                    model = Scope().initialize(wave,  scopeToAdd, "")
                    inserted_res, iid = model.addDomainInDb(insert_setting)
                if inserted_res == 1:
                    accepted += 1
                    ret.append(iid)
                total += 1
        return ret, total-accepted  # nb errors = total - accepted

    
    def getChecks(self):
        """Return scope assigned checks as a list of checkInstance
        Returns:
            list of checkInstance objects
        """
        return self.model.getChecks()

    def getType(self):
        """Returns a string describing the type of object
        Returns:
            "scope" """
        return "scope"