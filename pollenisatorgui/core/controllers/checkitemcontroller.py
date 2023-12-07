"""Controller for command object. Mostly handles conversion between mongo data and python objects"""
from turtle import title
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.controllers.controllerelement import ControllerElement
import bson
import json

class CheckItemController(ControllerElement):
    """Inherits ControllerElement
    Controller for CheckItem object. Mostly handles conversion between mongo data and python objects"""
    def doUpdate(self, values, updateInDb=True):
        """
        Update the command represented by this self.model in database with the given values.

        Args:
            values: A dictionary crafted by CheckItemView containg all form fields values needed.

        Returns:
            The mongo ObjectId _id of the updated command document.
        """
        # Get form values
        self.model.title = values.get("Title", self.model.title)
        self.model.description = values.get("Description", self.model.description)
        self.model.check_type = values.get("Check type", self.model.check_type)
        self.model.lvl = values.get("Level", self.model.lvl)
        self.model.ports = values.get("Ports/Services", self.model.ports)
        tag_trigger = values.get("Tag Name", getattr(self.model, "tag_trigger", ""))
        if self.model.lvl.startswith("tag:") and tag_trigger != "":
            self.model.lvl = ":".join(self.model.lvl.split(":")[:2]) +":"+str(tag_trigger)
        self.model.priority = int(values.get("Priority", self.model.priority))
        self.model.max_thread = int(values.get("Shared threads", self.model.max_thread))
        self.model.category = values.get("Category", self.model.category)
        self.model.pentest_types = [x[0] for x in values.get("Pentest types", self.model.pentest_types).items() if x[1]]
        commands_raw = values.get("Commands", [])
        self.model.commands = [str(command[-1]) for command in commands_raw if str(command[-1]) != ""]
        defect_tags = values.get("Defects", [])
        self.model.defect_tags = [(defect[-2], str(defect[-1])) for defect in defect_tags if str(defect[-1]) != ""]
        self.model.script = values.get("Script", "")
        if updateInDb:
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
        title = values["Title"]
        description = values["Description"]
        ports = values.get("Ports/Services", "")
        lvl = values["Level"]
        priority = values["Priority"]
        max_thread = values.get("Shared threads", 1)
        category = values.get("Category", "")
        commands_raw = values.get("Commands", [])
        defects_raw = values.get("Defects", [])
        check_type = values["Check type"]
        pentest_types = [k for k,v in values["Pentest types"].items() if v]
        step = values["Step"]
        script = values.get("Script", "")
        parent = values.get("Parent", None)
        tag_trigger = values.get("Tag Name", "")
        if lvl.startswith("tag:") and tag_trigger != "":
            lvl = ":".join(lvl.split(":")[:2]) +":"+str(tag_trigger)
        if parent == "":
            parent = None
        commands = []
        for command in commands_raw:
            if len(command) == 3:
                commands.append(str(command[2]))
        defect_tags = []
        for defect in defects_raw:
            if len(defect) == 4:
                defect_tags.append((defect[4],defect[3]))
        self.model.initialize(title, pentest_types=pentest_types, lvl=lvl, ports=ports, priority=priority, max_thread=max_thread, description=description, category=category, check_type=check_type, step=step, parent=parent, commands=commands, defect_tags=defect_tags, script=script,  infos=None)
        # Insert in database
        ret, _ = self.model.addInDb()
        if not ret:
            # command failed to be inserted, a duplicate exists
            # return None as inserted_id and 1 error
            return None, 1
        # Fetch the instance of this self.model now that it is inserted.
        return ret, 0  # 0 errors
    
    def isAuto(self):
        """Return True if this command is an auto command"""
        return self.model.isAuto()

    def getType(self):
        """Return a string describing the type of object
        Returns:
            "checkitem" """
        return "checkitem"

    def getChecks(self):
        """Return check instances that implements this check item
        Returns:
            list of checkInstance objects
        """
        return self.model.getChecks()
    
    def getCategory(self):
        return self.model.category
        
    def getParent(self):
        if self.model is not None:
            return self.model.parent

    def actualize(self):
        """Ask the model to reload its data from database
        """
        if self.model is not None:
            self.model = self.model.__class__.fetchObject({"_id": bson.ObjectId(self.model.getId())})

   