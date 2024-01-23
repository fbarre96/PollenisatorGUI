from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.models.element import Element
class User(Element):
    coll_name = "users"
    
    def __init__(self, valuesFromDb=None):
        if valuesFromDb is None:
            valuesFromDb = {}
        super().__init__(valuesFromDb.get("_id", None), valuesFromDb.get("parent", None),  valuesFromDb.get("infos", {}))
        self.initialize(valuesFromDb.get("_id"), valuesFromDb.get("domain"), valuesFromDb.get("username"), valuesFromDb.get("password"),
            valuesFromDb.get("groups"), valuesFromDb.get("description"), valuesFromDb.get("infos", {}))

    def initialize(self, _id, domain=None, username=None, password=None,groups=None, description=None, infos=None):
        """User
        :param _id: iid of the object
        :type _id: str
        :param username: The username of this User.
        :type username: str
        :param password: The password of this User.
        :type password: str
        :param domain: The domain of this User.
        :type domain: str
        :param groups: The groups of this User.
        :type groups: List[str]
        :param description: The description of this User.
        :type description: str
        """
      
        self._id = _id
        self.username = username if username is not None else  ""
        self.password = password if password is not None else  ""
        self.domain = domain if domain is not None else  ""
        self.groups = groups
        self.description = description
        self.infos =  infos if infos is not None else {}
        return self
  
    def __str__(self):
        """
        Get a string representation of a defect.

        Returns:
            Returns the defect +title.
        """
        return self.domain+"\\"+self.username 

    def getData(self):
        return {"_id": self._id, "username":self.username, "password": self.password, "domain":self.domain,
         "groups": self.groups, "description":self.description, "infos":self.infos}

    
    @classmethod
    def fetchObjects(cls, pipeline):
        """Fetch many commands from database and return a Cursor to iterate over model objects
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a cursor to iterate on model objects
        """
        apiclient = APIClient.getInstance()
        pipeline["type"] = "user"
        ds = apiclient.find(cls.coll_name, pipeline, True)
        if ds is None:
            return None
        for d in ds:
            # disabling this error as it is an abstract function
            yield User(d)  #  pylint: disable=no-value-for-parameter
    
    @classmethod
    def fetchObject(cls, pipeline):
        """Fetch many commands from database and return a Cursor to iterate over model objects
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a cursor to iterate on model objects
        """
        apiclient = APIClient.getInstance()
        pipeline["type"] = "user"
        d = apiclient.find(cls.coll_name, pipeline, False)
        if d is None:
            return None
        return User(d)
    
    @classmethod
    def fetchPentestObjects(cls):
        return [x for x in User.fetchObjects({})]
    
    def _getParentId(self):
        """
        Return the mongo ObjectId _id of the first parent of this object. For a port it is the ip.

        Returns:
            Returns the parent ip's ObjectId _id".
        """
        return self.domain