"""Controller for share object. Mostly handles conversion between mongo data and python objects"""

from pollenisatorgui.core.controllers.controllerelement import ControllerElement


class ShareController(ControllerElement):
    """Inherits ControllerElement
    Controller for share object. Mostly handles conversion between mongo data and python objects"""

    def doUpdate(self, values):
        """
        Update the share represented by this model in database with the given values.

        Args:
            values: A dictionary crafted by ShareView containg all form fields values needed.

        Returns:
            The mongo ObjectId _id of the updated share document.
        """
        raise NotImplementedError("ShareController.doUpdate not implemented")
        # self.model.dated = values.get("Start date", self.model.dated)
        # self.model.datef = values.get("End date", self.model.datef)
        self.model.update()

    def doInsert(self, values):
        """
        Insert the Interval represented by this model in the database with the given values.

        Args:
            values: A dictionary crafted by IntervalView containg all form fields values needed.

        Returns:
            {
                '_id': The mongo ObjectId _id of the inserted command document.
                'nbErrors': The number of objects that has not been inserted in database due to errors.
            }
        """
        # Get form values
        # dated = values["Start date"]
        # datef = values["End date"]
        # # Insert in database
        # self.model.initialize(values["waveName"], dated, datef)
        # ret, _ = self.model.addInDb()
        raise NotImplementedError("ShareController.doInsert not implemented")
        # return ret, 0  # 0 errors

    
    def getType(self):
        """Return a string describing the type of object
        Returns:
            "share" """
        return "share"