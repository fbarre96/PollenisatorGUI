"""Defect Model."""

import os
from bson.objectid import ObjectId
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.models.element import Element
from pollenisatorgui.core.components.apiclient import APIClient


class Defect(Element):
    """
    Represents a Defect object that defines a security defect. A security defect is a note added by a pentester on a port or ip which describes a security defect.

    Attributes:
        coll_name: collection name in pollenisator database
    """
    coll_name = "defects"

    def __init__(self, valuesFromDb=None):
        """Constructor
        Args:
            valueFromDb: a dict holding values to load into the object. A mongo fetched defect is optimal.
                        possible keys with default values are : _id (None), parent (None), tags([]), infos({}),
                        target_id, target_type, title(""), synthesis(""), description(""), ease(""), impact(""), risk(""),
                        redactor("N/A"), type([]), language(""), notes(""), creation_time(None),fixes([]), proofs([]), index(None)
        """
        if valuesFromDb is None:
            valuesFromDb = {}
        if isinstance(valuesFromDb, Defect):
            self = valuesFromDb
            return None
        self.proofs = []
        self.isTemplate = False
        super().__init__(valuesFromDb.get("_id", None), valuesFromDb.get("parent", None), valuesFromDb.get("infos", {}))
        types = valuesFromDb.get("type", [])
        if isinstance(types, str):
            types = [types]
        else:
            types = list(types)
        self.initialize(valuesFromDb.get("target_id", ""), valuesFromDb.get("target_type", ""),
                         valuesFromDb.get("title", ""), valuesFromDb.get("synthesis", ""), valuesFromDb.get("description", ""),
                        valuesFromDb.get("ease", ""), valuesFromDb.get(
                            "impact", ""),
                        valuesFromDb.get(
                            "risk", ""), valuesFromDb.get("redactor", "N/A"), types,
                        valuesFromDb.get("language", ""),
                        valuesFromDb.get("notes", ""), valuesFromDb.get("creation_time", None),
                        valuesFromDb.get("fixes", []), valuesFromDb.get("proofs", []), valuesFromDb.get("infos", {}),
                        valuesFromDb.get("index", "0"))

    def initialize(self, target_id="", target_type="", title="", synthesis="", description="", ease="", impact="", risk="", redactor="N/A", mtype=None, language="", notes="", creation_time=None, fixes=None, proofs=None, infos=None, index="0"):
        """Set values of defect
        Args:
            target_id: defect will be assigned to this id; can be empty
            target_type: defect will be assigned to target_id of this type
            title: a title for this defect describing what it is
            synthesis: a short summary of what this defect is about
            description: a more detailed explanation of this particular defect
            ease: ease of exploitation for this defect described as a string 
            impact: impact the defect has on system. Described as a string 
            risk: the combination of impact/ease gives a resulting risk value. Described as a string
            redactor: A pentester that waill be the redactor for this defect.
            mtype: types of this security defects (Application, data, etc...). Default is None
            language: the language in which this defect is redacted
            notes: notes took by pentesters
            proofs: a list of proof files, default to None.
            fixes: a list of fixes for this defect, default to empty list
            infos: a dictionnary with key values as additional information. Default to None
            index: the index of this defect in global defect table (only for unassigned defect)
        Returns:
            this object
        """
        self.title = title
        self.synthesis = synthesis
        self.description = description
        self.ease = ease
        self.impact = impact
        self.risk = risk
        self.redactor = redactor
        self.mtype = mtype if mtype is not None else []
        self.language = language
        self.notes = notes
        self.target_id = target_id
        self.target_type = target_type
        self.infos = infos if infos is not None else {}
        self.proofs = proofs if proofs is not None else []
        self.fixes = fixes if fixes is not None else []
        self.index = index
        self.creation_time = creation_time
        return self

    @classmethod
    def getTemplate(cls, title):
        apiclient = APIClient.getInstance()
        res = apiclient.findInDb("pollenisator", cls.coll_name, {"title":title}, False)
        print("searching "+str(res))
        if res is None:
            return None
        return Defect(res)
    
    @classmethod
    def getTemplateById(cls, iid):
        apiclient = APIClient.getInstance()
        res = apiclient.findDefectTemplateById(ObjectId(iid))
        if res is None:
            return None
        return Defect(res)

    @classmethod
    def getEases(cls):
        """
        Returns: 
            Returns a list of ease of exploitation levels for a security defect.
        """
        return ["Easy", "Moderate", "Difficult", "Arduous", "N/A"]

    @classmethod
    def getImpacts(cls):
        """
        Returns: 
            Returns a list of impact levels for a security defect.
        """
        return ["Critical", "Major", "Important", "Minor", "N/A"]

    @classmethod
    def getRisks(cls):
        """
        Returns: 
            Returns a list of risk levels for a security defect.
        """
        return ["Critical", "Major", "Important", "Minor", "N/A"]

    @classmethod
    def getTypes(cls):
        """
        Returns: 
            Returns a list of type for a security defect.
        """
        return ["Base", "Application", "Policy", "Active Directory", "Infrastructure", "Data"]

    @classmethod
    def getTableRiskFromEase(cls):
        return {"Easy": {"Minor": "Major", "Important": "Major", "Major": "Critical", "Critical": "Critical"},
                             "Moderate": {"Minor": "Important", "Important": "Important", "Major": "Major", "Critical": "Critical"},
                             "Difficult": {"Minor": "Minor", "Important": "Important", "Major": "Major", "Critical": "Major"},
                             "Arduous": {"Minor": "Minor", "Important": "Minor", "Major": "Important", "Critical": "Important"}}
            

    @classmethod
    def getRisk(cls, ease, impact):
        """Dict to find a risk level given an ease and an impact.
        Args:
            ease: ease of exploitation of this defect as as tring
            impact: the defect impact on system security
        Returns:
            A dictionnary of dictionnary. First dict keys are eases of exploitation. Second key are impact strings.
        """
        
        return cls.getTableRiskFromEase().get(ease, {}).get(impact, "N/A")

    def delete(self):
        """
        Delete the defect represented by this model in database.
        """
        ret = self._id
        apiclient = APIClient.getInstance()
        apiclient.delete("defects", ret)

    def addInDefectTemplates(self):
        """
        Add this defect to pollenisator template defect database.
        Returns: a tuple with :
                * bool for success
                * mongo ObjectId : already existing object if duplicate, create object id otherwise 
        """
        apiclient = APIClient.getInstance()
        base = dict()
        base["title"] = self.title
        base["synthesis"] = self.synthesis
        base["description"] = self.description
        base["ease"] = self.ease
        base["impact"] = self.impact
        base["risk"] = self.risk
        base["type"] = list(self.mtype)
        base["language"] = self.language
        base["fixes"] = self.fixes
        base["perimeter"] = self.perimeter
        res, id = apiclient.insertAsTemplate(base)
        if not res:
            return False, id
        return True, id
        
    def addInDb(self):
        """
        Add this defect to pollenisator database.
        Returns: a tuple with :
                * bool for success
                * mongo ObjectId : already existing object if duplicate, create object id otherwise 
        """
        apiclient = APIClient.getInstance()
        base = self.getDbKey()
        base["synthesis"] = self.synthesis
        base["description"] = self.description
        base["ease"] = self.ease
        base["impact"] = self.impact
        base["risk"] = self.risk
        base["redactor"] = self.redactor
        base["type"] = list(self.mtype)
        base["language"] = self.language
        base["fixes"] = self.fixes
        base["proofs"] = self.proofs
        base["notes"] = self.notes
        base["fixes"] = self.fixes
        if self.index is not None:
            base["index"] = str(self.index)
        res, id = apiclient.insert("defects", base)
        if not res:
            return False, id
        self._id = id
        return True, id

    def updateAsTemplate(self, pipeline_set=None):
        """Update this object in pollenisator database, template.
        Args:
            pipeline_set: (Opt.) A dictionnary with custom values. If None (default) use model attributes.
        """
        apiclient = APIClient.getInstance()
        if pipeline_set is None:
            res = apiclient.updateDefectTemplate(ObjectId(self._id), {"title": self.title, "synthesis":self.synthesis, "description":self.description,
                         "ease": self.ease, "impact": self.impact,
                         "risk": self.risk, "type": list(self.mtype), "language":self.language, "fixes":self.fixes})
        else:
            apiclient.updateDefectTemplate(ObjectId(self._id), pipeline_set)

    def update(self, pipeline_set=None):
        """Update this object in database.
        Args:
            pipeline_set: (Opt.) A dictionnary with custom values. If None (default) use model attributes.
        """
        apiclient = APIClient.getInstance()
        if self.isTemplate:
            print("UPDATING TEMPLATE n update"+str(pipeline_set))
            self.updateAsTemplate(pipeline_set)
        if pipeline_set is None:
            apiclient.update("defects", ObjectId(self._id), {"target_id":self.target_id, "target_type":self.target_type, "title": self.title, "synthesis":self.synthesis, "description":self.description,
                         "notes": self.notes, "ease": self.ease, "impact": self.impact,
                         "risk": self.risk, "redactor": self.redactor, "type": list(self.mtype), "language":self.language, "proofs": self.proofs, "fixes":self.fixes, "infos": self.infos, "index":str(self.index)})
        else:
            apiclient.update("defects", ObjectId(self._id), pipeline_set)

    def _getParentId(self):
        """
        Return the mongo ObjectId _id of the first parent of this object. For a Defect it is either an ip or a port depending on the Defect's level.

        Returns:
            Returns the parent's ObjectId _id".
        """
        return self.target_id

    def calcDirPath(self):
        """Returns a directory path constructed for this defect.
        Returns:
            path as string
        """
        apiclient = APIClient.getInstance()
        path_calc = str(apiclient.getCurrentPentest())+"/"+str(self.target_id)
        return path_calc

    def uploadProof(self, proof_local_path):
        """Upload the given proof file to the server
        Args:
            proof_local_path: a path to a local proof file
        Returns:
            the basename of the file 
        """
        apiclient = APIClient.getInstance()
        result = apiclient.putProof(self._id, proof_local_path)
        if result.get("remote_path", "") != "":
            return result.get("remote_path", "")
        return None

    def getProof(self, ind):
        """Download the proof file at given proof index
        Returns:
            A string giving the local path of the downloaded proof
        """
        apiclient = APIClient.getInstance()
        current_dir = os.path.dirname(os.path.realpath(__file__))
        local_path = os.path.join(current_dir, "../../results", self.calcDirPath())
        try:
            os.makedirs(local_path)
        except FileExistsError:
            pass
        local_path = os.path.join(local_path, self.proofs[ind])
        ret = apiclient.getProof(self._id, self.proofs[ind], local_path)
        return ret
    
    def getProofWithName(self, name):
        apiclient = APIClient.getInstance()
        current_dir = os.path.dirname(os.path.realpath(__file__))
        local_path = os.path.join(current_dir, "../../results", self.calcDirPath())
        try:
            os.makedirs(local_path)
        except FileExistsError:
            pass
        ret = apiclient.getProof(self.getId(), name, local_path)
        return ret

    def removeProof(self, ind):
        """Removes the proof file at given proof index
        """
        apiclient = APIClient.getInstance()
        filename = self.proofs[ind]
        ret = apiclient.rmProof(self._id, filename)
        del self.proofs[ind]
        return ret

    def __str__(self):
        """
        Get a string representation of a defect.

        Returns:
            Returns the defect +title.
        """
        return self.title
    
    def getTargetRepr(self):
        apiclient = APIClient.getInstance()
        result = apiclient.getDefectTargetRepr([self.getId()])
        if result is not None:
            return result.get(str(self.getId()), None)
        return None

    def getDetailedString(self, onlyTarget=False):
        """Returns a detailed string describing for this defect.
        Returns:
            the defect title. If assigned, it will be prepended with ip and (udp/)port
        """
        ret = ""
        target = self.getTargetRepr()
        if onlyTarget:
            return target
        ret = target+" "+self.__str__()
        return ret

    def getDbKey(self):
        """Return a dict from model to use as unique composed key.
        Returns:
            A dict (3 keys :"target_id" and "target_type" and "title")
        """
        return {"target_type": self.target_type, "target_id": self.target_id, "title": self.title}

    def isAssigned(self):
        """Returns a boolean indicating if this defect is assigned to an ip or is global.
        Returns:
            bool
        """
        return self.target_id != ""

    @classmethod
    def getDefectTable(cls):
        """Return the table of global defects sorted by their index field
        Returns:
            A list of Defect
        """
        return APIClient.getInstance().getDefectTable()

    @classmethod
    def fetchPentestObjects(cls):
        apiclient = APIClient.getInstance()
        ds = apiclient.find(cls.coll_name, {"target_id":{"$ne":""}}, True)
        if ds is None:
            return None
        for d in ds:
            # disabling this error as it is an abstract function
            yield cls(d)  

    def getData(self):
        """Return defect attributes as a dictionnary matching Mongo stored defects
        Returns:
            dict with keys title, ease, ipact, risk, redactor, type, notes, ip, port, proto, proofs, _id, tags, infos
        """
        return {"title": self.title, "synthesis":self.synthesis, "description":self.description, "ease": self.ease, "impact": self.impact,
                "risk": self.risk, "redactor": self.redactor, "type": self.mtype, "language":self.language, "notes": self.notes, "fixes":self.fixes,
                "target_id": self.target_id, "target_type": self.target_type,"index":self.index, "creation_time":self.creation_time,
                "proofs": self.proofs, "_id": self.getId(),"infos": self.infos}
