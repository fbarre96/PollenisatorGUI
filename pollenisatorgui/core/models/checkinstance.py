"""CheckItem Model."""
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.models.element import Element
from pollenisatorgui.core.models.checkitem import CheckItem
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.models.tool import Tool
from bson import ObjectId

class CheckInstance(Element):
    """Represents a CheckInstance object of a cheatsheet.

    Attributes:
        coll_name: collection name in pollenisator or pentest database
    """

    coll_name = "checkinstances"

    def __init__(self, valuesFromDb=None):
        """Constructor
        Args:
            valueFromDb: a dict holding values to load into the object. A mongo fetched command is optimal.
                        possible keys with default values are : _id (None), parent (None), check_iid, status, notes
        """
        if valuesFromDb is None:
            valuesFromDb = dict()
        super().__init__(valuesFromDb.get("_id", None), valuesFromDb.get("parent", None), valuesFromDb.get("infos", {}))
        self.initialize(valuesFromDb.get("check_iid"), valuesFromDb.get("target_iid"),valuesFromDb.get("target_type"), valuesFromDb.get("parent"), valuesFromDb.get("status", ""), valuesFromDb.get("notes", ""))
        
   
    def initialize(self, check_iid, target_iid, target_type, parent, status, notes):
        self.check_iid = check_iid
        self.parent = parent
        self.target_iid = target_iid
        self.target_type = target_type
        self.status = status
        self.notes = notes
        from pollenisatorgui.core.components.datamanager import DataManager
        datamanager = DataManager.getInstance()
        self.check_m = datamanager.get("checkitems", str(check_iid))
        if self.check_m is None:
            self.check_m = CheckItem.fetchObject({"_id":ObjectId(check_iid)})
        if self.check_m is None:
            #print(" Warning : Check item not found. Might have been deleted")
            return None
        return self

    def delete(self):
        ret = self._id
        apiclient = APIClient.getInstance()
        apiclient.deleteCheckInstance(ret)
        

    # def addInDb(self):
    #     """Add this command to pollenisator database
    #     Returns: a tuple with :
    #             * bool for success
    #             * mongo ObjectId : already existing object if duplicate, create object id otherwise 
    #     """
    #     apiclient = APIClient.getInstance()
    #     res, id = apiclient.insertCheckInstance(self.getData())
    #     if not res:
    #         return False, id
    #     self._id = id
    #     return True, id
        
    def getStatus(self):
        return self.status
    

    def update(self, pipeline_set=None):
        """Update this object in database.
        Args:
            pipeline_set: (Opt.) A dictionnary with custom values. If None (default) use model attributes.
        """
        apiclient = APIClient.getInstance()
        if pipeline_set is None:
            apiclient.updateCheckInstance(self._id, self.getData())
        else:
            apiclient.updateCheckInstance(self._id, pipeline_set )
        


    @classmethod
    def fetchObject(cls,  pipeline):
        """Fetch one CheckInstance from database and return the CheckInstance object 
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a CheckInstance or None if nothing matches the pipeline.
        """
        apiclient = APIClient.getInstance()
        res = apiclient.findCheckInstance(pipeline, many=False)
        d = res
        if d is None:
            return None
        return CheckInstance(d)

    @classmethod
    def fetchObjects(cls, pipeline):
        """Fetch many cheatsheet from database and return a Cursor to iterate over cheatsheet objects
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a cursor to iterate on cheatsheet objects
        """
        apiclient = APIClient.getInstance()
        if isinstance(pipeline, list):
            pipeline = {"_id": {"$in":list(map(ObjectId, pipeline))}}
        ds = apiclient.findCheckInstance(pipeline)
        if ds is None:
            return None
        for d in ds:
            yield CheckInstance(d)
    
    def getData(self):
        return {"_id": self._id,  "check_iid": self.check_iid, "target_type": self.target_type, "target_iid": self.target_iid,"parent":self.parent, "status": self.status, "notes": self.notes}

    def getCheckItem(self):
        return self.check_m

    def getTools(self):
        datamanager = DataManager.getInstance()
        return datamanager.find("tools", {"check_iid": str(self._id)})

    def getDbKey(self):
        """Return a dict from model to use as unique composed key.
        Returns:
            A dict (1 key :"name")
        """
        return {"check_iid": self.check_iid}

    def __str__(self):
        if self.check_m is None:
            return "ERROR"
        return self.check_m.title

    def getCheckInstanceStatus(self):
        """
        Get a more detailed string representation of a check instance.
        Returns:
            string
        """
        data = self.getData()
        if self.check_m is None:
            check_item_data = {}
        else:
            check_item_data = self.check_m.getData()
        data["check_item"] = check_item_data
        data["tools_done"] = {}
        data["tools_running"] = {}
        data["tools_not_done"] = {}
        all_complete = True
        at_least_one = False
        total = 0
        done = 0
        tools_to_add = self.getTools()
        if tools_to_add is not None:
            for tool in tools_to_add:
                if "done" in tool.getStatus():
                    done += 1
                    at_least_one = True
                    data["tools_done"][str(tool.getId())] = tool.getData()
                elif "running" in tool.getStatus():
                    at_least_one = True
                    data["tools_running"][str(
                        tool.getId())] = tool.getData()
                else:
                    data["tools_not_done"][str(
                        tool.getId())] = tool.getData()
                total += 1

        if done != total:
            all_complete = False
        if self.check_m is not None:
            if len(self.check_m.commands) > 0:
                if at_least_one and all_complete:
                    data["status"] = "done"
                elif at_least_one and not all_complete:
                    data["status"] = "running"
                else:
                    data["status"] = "todo"
            else:
                data["status"] = ""
        else:
            data["status"] = "error"
        return data
