"""Controller for computer object. Mostly handles conversion between mongo data and python objects"""

from pollenisatorgui.core.controllers.controllerelement import ControllerElement


class ComputerController(ControllerElement):
    """Inherits ControllerElement
    Controller for computer object. Mostly handles conversion between mongo data and python objects"""

    def doUpdate(self, values):
        """
        Update the computer represented by this model in database with the given values.

        Args:
            values: A dictionary crafted by ComputerView containg all form fields values needed.

        Returns:
            The mongo ObjectId _id of the updated computer document.
        """
        is_dc = values.get("is_dc", self.model.infos.is_dc)
        self.model.update({"infos.is_dc": is_dc})

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
        raise NotImplementedError("ComputerController.doInsert not implemented")
        # return ret, 0  # 0 errors

    
    def getType(self):
        """Return a string describing the type of object
        Returns:
            "computer" """
        return "computer"