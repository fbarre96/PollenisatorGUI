"""Controller for defect object. Mostly handles conversion between mongo data and python objects"""

import os
from pollenisatorgui.core.Controllers.ControllerElement import ControllerElement
import pollenisatorgui.core.Models.Defect as Defect

class DefectController(ControllerElement):
    """Inherits ControllerElement
    Controller for defect object. Mostly handles conversion between mongo data and python objects"""

    def doUpdate(self, values):
        """
        Update the Defect represented by this model in database with the given values.

        Args:
            values: A dictionary crafted by DefectView containg all form fields values needed.

        Returns:
            The mongo ObjectId _id of the updated Defect document.
        """
        self.model.title = values.get("Title", self.model.title)
        self.model.synthesis = values.get("Synthesis", self.model.synthesis)
        self.model.description = values.get("Description", self.model.description)
        self.model.ease = values.get("Ease", self.model.ease)
        self.model.impact = values.get("Impact", self.model.impact)
        self.model.risk = values.get("Risk", self.model.risk)
        self.model.redactor = values.get("Redactor", self.model.redactor)
        mtype = values.get("Type", None)
        if mtype is not None:
            mtype = [k for k, v in mtype.items() if v == 1]
            self.model.mtype = mtype
        self.model.language = values.get("Language", self.model.language)
        self.model.notes = values.get("Notes", self.model.notes)
        self.model.fixes = values.get("Fixes", self.model.fixes)
        proofs = values.get("Add proofs", [])
        for val in proofs:
            self.addAProof(val)
        self.model.infos = values.get("Infos", self.model.infos)
        for info in self.model.infos:
            self.model.infos[info] = self.model.infos[info][0]
        # Updating

        self.model.update()

    def doInsert(self, values):
        """
        Insert the Defect represented by this model in the database with the given values.

        Args:
            values: A dictionary crafted by DefectView containing all form fields values needed.

        Returns:
            {
                '_id': The mongo ObjectId _id of the inserted command document.
                'nbErrors': The number of objects that has not been inserted in database due to errors.
            }
        """
        title = values["Title"]
        synthesis = values.get("Synthesis", "")
        description = values.get("Description", "")
        ease = values["Ease"]
        impact = values["Impact"]
        redactor = values["Redactor"]
        mtype_dict = values["Type"]
        language = values["Language"]
        risk = values["Risk"]
        notes = values.get("Notes", "")
        mtype = [k for k, v in mtype_dict.items() if v == 1]
        ip = values["ip"]
        port = values.get("port", None)
        proto = values.get("proto", None)
        proof = values["Proof"]
        proofs = []
        fixes = values["Fixes"]
        tableau_from_ease = Defect.Defect.getTableRiskFromEase()
       
        if risk == "" or risk == "N/A":
            risk = tableau_from_ease.get(ease,{}).get(impact,"N/A")
        self.model.initialize(ip, port, proto, title, synthesis, description, ease,
                              impact, risk, redactor, mtype, language, notes, fixes, proofs)
        ret, _ = self.model.addInDb()
        # Update this instance.
        # Upload proof after insert on db cause we need its mongoid
        for p in proof:
            if p.strip() != "":
                self.model.uploadProof(proof)
        return ret, 0  # 0 erros

    def addAProof(self, proof_path):
        """Add a proof file to model defect.
        Args:
            formValues: the view form values as a dict. Key "Proof "+str(index) must exist
        """
        if proof_path.strip() == "":
            return
        resName = self.model.uploadProof(proof_path)
        self.model.proofs.append(resName)
        # self.model.update()

    def getProof(self, ind):
        """Returns proof file to model defect.
        Args:
            ind: the proof index in the form to get
        Returns:
            the local path of the downloaded proof (string)
        """
        return self.model.getProof(ind)

    def deleteProof(self, ind):
        """Delete a proof file given a proof index
        Args:
            ind: the proof index in the form to delete
        """
        self.model.removeProof(ind)

    def isAssigned(self):
        """Checks if the defect model is assigned to an IP or is global
        Returns:    
            bool
        """
        return self.model.isAssigned()

    def getData(self):
        """Return defect attributes as a dictionnary matching Mongo stored defects
        Returns:
            dict with keys title, ease, ipact, risk, redactor, type, notes, ip, port, proto, proofs, _id, tags, infos
        """
        if self.model is None:
            return None
        return {"title": self.model.title, "synthesis":self.model.synthesis, "description":self.model.description, "ease": self.model.ease, "impact": self.model.impact,
                "risk": self.model.risk, "redactor": self.model.redactor, "type": self.model.mtype, "language":self.model.language, "notes": self.model.notes, "fixes":self.model.fixes,
                "ip": self.model.ip, "port": self.model.port, "proto": self.model.proto,"index":self.model.index,
                "proofs": self.model.proofs, "_id": self.model.getId(), "tags": self.model.tags, "infos": self.model.infos}

    def getType(self):
        """Returns a string describing the type of object
        Returns:
            "defect" """
        return "defect"