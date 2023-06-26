"""Element parent Model. Common ground for every model"""

from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.models.metaelement import MetaElement
from bson.objectid import ObjectId


class Element(metaclass=MetaElement):
    """
    Parent element for all model. This class should only be inherited.

    Attributes:
        coll_name:  collection name in pollenisator database
    """
    coll_name = None

    def __init__(self, _id, parent, infos):
        """
        Constructor to be inherited. Child model will all use this constructor.

        Args:
            _id: mongo database id
            parent: a parent mongo id object for this model.
            infos: a dicitonnary of custom information 
        """
        # Initiate a cachedIcon for a model, not a class.
        self._id = _id
        self.parent = parent
        self.infos = infos
        self.cachedIcon = None

    @classmethod
    def fetchObject(cls, pipeline):
        """Fetch one element from database and return the object 
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns the model object or None if nothing matches the pipeline.
        """
        apiclient = APIClient.getInstance()
        d = apiclient.find(cls.coll_name, pipeline, False)
        if d is None:
            return d
        # disabling this error as it is an abstract function
        return cls(d)  #  pylint: disable=no-value-for-parameter

    @classmethod
    def fetchPentestObjects(cls):
        apiclient = APIClient.getInstance()
        ds = apiclient.find(cls.coll_name, {}, True)
        if ds is None:
            return None
        for d in ds:
            # disabling this error as it is an abstract function
            yield cls(d)  


    @classmethod
    def fetchObjects(cls, pipeline):
        """Fetch many commands from database and return a Cursor to iterate over model objects
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a cursor to iterate on model objects
        """
        apiclient = APIClient.getInstance()
        ds = apiclient.find(cls.coll_name, pipeline, True)
        if ds is None:
            return None
        for d in ds:
            # disabling this error as it is an abstract function
            yield cls(d)  #  pylint: disable=no-value-for-parameter

    def getId(self):
        """Returns the mongo id  of this element.
        Returns:
            bson.objectid.ObjectId
        """
        return self._id

    def getChecks(self):
        """Return wave assigned checks as a list of checkInstance objects
        Returns:
            list of CheckInstance objects
        """
        from pollenisatorgui.core.models.checkinstance import CheckInstance
        return CheckInstance.fetchObjects({"target_iid": str(self._id)})

    def getParentId(self):
        """Returns the mongo id  of this element parent.
        Returns:
            bson.objectid.ObjectId
        """
        if self.parent is None:
            try:
                self.parent = self._getParentId()  # pylint: disable=assignment-from-none
            except TypeError:
                return None
        return self.parent

    def _getParentId(self):
        """
        To be overriden
        Return the mongo ObjectId _id of the first parent of this object. 
        Returns:
            Returns the parent's ObjectId _id".
        Returns:
            None
        """
        return None

    def delete(self):
        """
        To be overriden
        Delete the object represented by this model in database.
        """
        # pass

    def addInDb(self):
        """
        To be overriden
        Add this model to pollenisator database.
        Returns: a tuple with :
                * bool for success
                * mongo ObjectId : already existing object if duplicate, create object id otherwise 
        """
        # pass

    def update(self, _pipeline_set=None):
        """
        To be overriden
        Update this object in database.
        Args:
            pipeline_set: (Opt.) A dictionnary with custom values. If None (default) use model attributes.
        """
        # pass




    def getTagsGroups(self):
        """Returns groups of tags that may not be applied at the same time
        Returns:
            List of list of strings
        """
        import pollenisatorgui.core.components.settings as settings

        tags = settings.Settings.getTags()
        return [tags, ["hidden"]]

    

    def getDetailedString(self):
        """To be inherited and overriden
        Returns a detailed string describing this element. Calls __str__ of children by default.
        Returns:
            string
        """
        return str(self)

    def updateInfos(self, newInfos):
        """Change all infos stores in self.infos with the given new ones and update database.
        Args:
            newInfos: A new dictionnary of custom information
        """
        if "" in newInfos:
            del newInfos[""]
        self.infos.update(newInfos)
        self.update()
