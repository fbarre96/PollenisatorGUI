"""Controller for defect object. Mostly handles conversion between mongo data and python objects"""

import os
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.controllers.controllerelement import ControllerElement
import pollenisatorgui.core.models.defect as defect
import re

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
        fixes_inserted = values.get("Fixes", None)
        if fixes_inserted is not None:
            self.model.fixes = []
            for fix in fixes_inserted:
                if fix[0].strip() == "":
                    continue
                self.model.fixes.append({"title": fix[0], "execution": fix[1], "gain": fix[2],
                                          "synthesis": fix[3], "description": fix[4]})
        self.model.infos = values.get("Infos", self.model.infos)
        for info in self.model.infos:
            self.model.infos[info] = self.model.infos[info][0]

        group_proofs = self.findProofsInDescription(self.model.description)
        for group_proof in group_proofs:
            matched = group_proof.group(0)
            path = group_proof.group(1)
            if path.strip() != "":
                result_path = self.model.uploadProof(path)
                if result_path is not None:
                    result_path = os.path.basename(result_path)
                    self.model.description = self.model.description.replace(matched, f"![{result_path}]({result_path})")
        # Updating
        self.model.update()

    def update_fixes(self,fixes):
        """Update the fixes of the model"""
        self.model.fixes = fixes
        self.model.update({"fixes": fixes})

    def findProofsInDescription(self, description):
        regex_images = r"!\[.*\]\(((?!http).*)\)"
        return re.finditer(regex_images, description)
        

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
        target_id = values.get("target_id", "")
        target_type = values.get("target_type", "")
        fixes = []
        fixes_inserted = values.get("Fixes", None)
        if fixes_inserted is not None:
            for fix in fixes_inserted:
                if fix[0].strip() == "":
                    continue
                fixes.append({"title": fix[0], "execution": fix[1], "gain": fix[2],
                                          "synthesis": fix[3], "description": fix[4]})
        tableau_from_ease = defect.Defect.getTableRiskFromEase()
       
        if risk == "" or risk == "N/A":
            risk = tableau_from_ease.get(ease,{}).get(impact,"N/A")
        self.model.initialize(target_id, target_type, title, synthesis, description, ease,
                              impact, risk, redactor, mtype, language, notes, None, fixes, [])
        ret, _ = self.model.addInDb()
        # Update this instance.
        # Upload proof after insert on db cause we need its mongoid
        group_proofs = self.findProofsInDescription(description)
        must_update = False
        apiclient = APIClient.getInstance()
        for group_proof in group_proofs:
            matched = group_proof.group(0)
            path = group_proof.group(1)
            if path.strip() != "" and not path.startswith("http"):
                result_path = self.model.uploadProof(path)
                if result_path is not None:
                    result_path = os.path.basename(result_path)
                    self.model.description = self.model.description.replace(matched, f"![{result_path}]({result_path})")
                    must_update = True
        
        if must_update:
            self.model.update({"description": self.model.description}) 

        return ret, 0  # 0 erros

    def addAProof(self, proof_path):
        """Add a proof file to model defect.
        Args:
            formValues: the view form values as a dict. Key "Proof "+str(index) must exist
        """
        if proof_path.strip() == "":
            return
        result_path = self.model.uploadProof(proof_path)
        self.model.update()
        return result_path

    def getProof(self, ind):
        """Returns proof file to model defect.
        Args:
            ind: the proof index in the form to get
        Returns:
            the local path of the downloaded proof (string)
        """
        return self.model.getProof(ind)
    
    def getProofWithName(self, remote_name):
        """Returns proof file to model defect.
        Args:
            remote_name: the proof remote name to get
        Returns:
            the local path of the downloaded proof (string)
        """
        return os.path.realpath(self.model.getProofWithName(remote_name))

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
    
    def getTargetRepr(self):
        """Returns the target representation of the defect model
        Returns:
            str
        """
        return self.model.getTargetRepr()

    
    def getType(self):
        """Returns a string describing the type of object
        Returns:
            "defect" """
        return "defect"