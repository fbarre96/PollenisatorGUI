from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.models.element import Element

class Share(Element):
    coll_name = "ActiveDirectory"

    def __init__(self, valuesFromDb=None):
        if valuesFromDb is None:
            valuesFromDb = {}
        self.initialize(valuesFromDb.get("_id"),  valuesFromDb.get("ip"),
            valuesFromDb.get("share"),  valuesFromDb.get("files"), valuesFromDb.get("infos"))

    def initialize(self,  _id=None, ip=None, share=None,  files=None, infos=None): 
        """
        :param ip: The ip of this Share. 
        :type ip: str
        :param share: The share of this Share. 
        :type share: str

        :param files: The files of this Share. 
        :type files: List[ShareFile]
        """
       
        self._id = _id
        self.ip = ip
        self.share = share
        self.files = [] 
        self.infos =  infos if infos is not None else {}
        if files is not None:
            for f in files:
                self.files.append(f)
        return self

    def getData(self):
        return {"_id": self._id, "ip":self.ip, "share": self.share,  "files":[f for f in self.files], "infos":self.infos}


    @classmethod
    def fetchObjects(cls, pipeline):
        """Fetch many commands from database and return a Cursor to iterate over model objects
        Args:
            pipeline: a Mongo search pipeline (dict)
        Returns:
            Returns a cursor to iterate on model objects
        """
        apiclient = APIClient.getInstance()
        pipeline["type"] = "share"
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
        pipeline["type"] = "share"
        d = apiclient.find(cls.coll_name, pipeline, False)
        if d is None:
            return None
        return cls(d)
    
    @classmethod
    def fetchPentestObjects(cls):
        return [x for x in Share.fetchObjects({})]