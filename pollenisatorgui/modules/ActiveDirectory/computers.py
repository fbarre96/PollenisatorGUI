from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.models.element import Element
from pollenisatorgui.modules.ActiveDirectory.computer_infos import ComputerInfos

class Computer(Element):
    coll_name = "ActiveDirectory"

    @property
    def infos(self):
        """Gets the infos of this Computer.


        :return: The infos of this Computer.
        :rtype: ComputerInfos
        """
        return self._infos
    
    @infos.setter
    def infos(self, infos):
        """Sets the infos of this Computer.


        :param infos: The infos of this Computer.
        :type infos: ComputerInfos
        """
        #keeping clarity with explicit checks
        self._infos = infos
    
    def __init__(self, valuesFromDb=None):
        if valuesFromDb is None:
            valuesFromDb = {}
        self.initialize(valuesFromDb.get("_id"),  valuesFromDb.get("name"), valuesFromDb.get("ip"), \
             valuesFromDb.get("domain"),  valuesFromDb.get("admins"),  valuesFromDb.get("users"), valuesFromDb.get("infos"))

    def initialize(self, _id=None, name=None, ip=None, domain=None, admins=None, users=None, infos=None):  # noqa: E501
        """Computer - a model defined in OpenAPI
        :param _id: iid of the object
        :type _id: str
        :param name: The name of this Computer.  # noqa: E501
        :type name: str
        :param ip: The ip of this Computer.  # noqa: E501
        :type ip: str
        :param domain: The domain of this Computer.  # noqa: E501
        :type domain: str
        :param admins: The admins of this Computer.  # noqa: E501
        :type admins: List[str]
        :param users: The users of this Computer.  # noqa: E501
        :type users: List[str]
        :param infos: The infos of this Computer.  # noqa: E501
        :type infos: ComputerInfos
        """

        self._id = _id
        self.name = name
        self.ip = ip
        self.domain = domain
        self.admins = admins
        self.users = users
        self._infos = ComputerInfos(infos)
    
    def __str__(self):
        """
        Get a string representation of a defect.

        Returns:
            Returns the defect +title.
        """
        return self.domain+"\\"+self.name + " ("+self.ip+")"

    def getData(self):
        return {"_id": self._id, "name":self.name, "ip":self.ip, "domain":self.domain,
            "admins":self.admins, "users": self.users, "infos":self.infos.getData()}

    
    @classmethod
    def fetchObjects(cls, pipeline):
        """Fetch many commands from database and return a Cursor to iterate over model objects
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a cursor to iterate on model objects
        """
        apiclient = APIClient.getInstance()
        pipeline["type"] = "computer"
        ds = apiclient.find(cls.coll_name, pipeline, True)
        if ds is None:
            return None
        for d in ds:
            # disabling this error as it is an abstract function
            yield cls(d)  #  pylint: disable=no-value-for-parameter
    
    @classmethod
    def fetchObject(cls, pipeline):
        """Fetch many commands from database and return a Cursor to iterate over model objects
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a cursor to iterate on model objects
        """
        apiclient = APIClient.getInstance()
        pipeline["type"] = "computer"
        d = apiclient.find(cls.coll_name, pipeline, False)
        if d is None:
            return None
        return cls(d)
    
    @classmethod
    def fetchPentestObjects(cls):
        return [x for x in cls.fetchObjects({})]