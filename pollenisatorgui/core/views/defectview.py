"""View for defect object. Handle node in treeview and present forms to user when interacted with."""

from tkinter import TclError
import tkinter as tk
from pollenisatorgui.core.views.viewelement import ViewElement
from pollenisatorgui.core.models.defect import Defect
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.components.apiclient import APIClient
from PIL import ImageTk, Image
from shutil import which
import os
import subprocess
from pollenisatorgui.core.application.dialogs.ChildDialogFixes import ChildDialogFixes

class DefectView(ViewElement):
    """View for defect object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory.
    """

    icon = 'defect.png'

    def __init__(self, appTw, appViewFrame, mainApp, controller):
        """Constructor
        Args:
            appTw: a PollenisatorTreeview instance to put this view in
            appViewFrame: an view frame to build the forms in.
            mainApp: the Application instance
            controller: a CommandController for this view.
        """
        super().__init__(appTw, appViewFrame, mainApp, controller)
        self.easeForm = None
        self.impactForm = None
        self.riskForm = None

    def openInsertWindow(self, notes="", addButtons=True):
        """
        Creates a tkinter form using Forms classes. This form aims to insert a new Defect
        Args:
            notes: default notes to be written in notes text input. Default is ""
            addButtons: boolean value indicating that insertion buttons should be visible. Default to True
        """
        settings = self.mainApp.settings
        settings.reloadSettings()
        modelData = self.controller.getData()
        topPanel = self.form.addFormPanel(grid=True)
        s = topPanel.addFormSearchBar("Search Defect", self.searchCallback, self.form, row=0, column= 0)
        topPanel.addFormLabel("Search Language",row=0, column=1)
        lang = topPanel.addFormStr("lang", row=0, column=2)
        s.addOptionForm(lang)
        topPanel = self.form.addFormPanel(grid=True)
        topPanel.addFormLabel("Title")
        topPanel.addFormStr("Title", r".+", "", column=1, width=50)
        topPanel = self.form.addFormPanel(grid=True)
        topPanel.addFormLabel("Ease")
        self.easeForm = topPanel.addFormCombo(
            "Ease", Defect.getEases(), width=10, column=1, binds={"<<ComboboxSelected>>": self.updateRiskBox})
        topPanel.addFormHelper("0: Trivial to exploit, no tool required\n1: Simple technics and public tools needed to exploit\n2: public vulnerability exploit requiring security skills and/or the development of simple tools.\n3: Use of non-public exploits requiring strong skills in security and/or the development of targeted tools", column=2)
        topPanel.addFormLabel("Impact", column=3)
        self.impactForm = topPanel.addFormCombo(
            "Impact", Defect.getImpacts(), width=10, column=4, binds={"<<ComboboxSelected>>": self.updateRiskBox})
        topPanel.addFormHelper("0: No direct impact on system security\n1: Impact isolated on precise locations of pentested system security\n2: Impact restricted to a part of the system security.\n3: Global impact on the pentested system security.", column=5)
        topPanel.addFormLabel("Risk", column=6)
        self.riskForm = topPanel.addFormCombo(
            "Risk", Defect.getRisks(), modelData["risk"], width=10, column=7)
        topPanel.addFormHelper(
            "0: small risk that might be fixed\n1: moderate risk that need a planed fix\n2: major risk that need to be fixed quickly.\n3: critical risk that need an immediate fix or an immediate interruption.", column=8)
        topPanel = self.form.addFormPanel(grid=True)
        topPanel.addFormLabel("Redactor", row=1)
        topPanel.addFormCombo("Redactor", self.mainApp.settings.getPentesters()+["N/A"], "N/A", row=1, column=1)
        topPanel.addFormLabel("Language", row=1, column=2)
        topPanel.addFormStr("Language", "", "en", row=1, column=3)
        

        chklistPanel = self.form.addFormPanel(grid=True)
        defectTypes = settings.getPentestTypes()
        if defectTypes is not None:
            defectTypes = defectTypes.get(settings.getPentestType(), [])
            if len(defectTypes) == 0:
                defectTypes = ["N/A"]
        else:
            defectTypes = ["N/A"]
        chklistPanel.addFormChecklist("Type", defectTypes, ["N/A"])
        proofsPanel = self.form.addFormPanel(grid=True)
        proofsPanel.addFormFile("Proof", r"", text="Add proof", width=90, height=4)
        topPanel = self.form.addFormPanel()
        topPanel.addFormText("Synthesis", r"", "Synthesis", state="readonly" if self.controller.isAssigned() else "", height=2, side="top")
        if not self.controller.isAssigned():
            topPanel.addFormText("Description", r"", "Description", side="top")
        else:
            topPanel.addFormHidden("Description", modelData.get("description", ""))
            notesPanel = self.form.addFormPanel()
            notesPanel.addFormLabel("Notes", side="top")
            notesPanel.addFormText("Notes", r"", notes, None, side="top")
        self.form.addFormHidden("ip", modelData["ip"])
        self.form.addFormHidden("proto", modelData["proto"])
        self.form.addFormHidden("port", modelData["port"])
        self.form.addFormHidden("Fixes", [])
        if addButtons:
            self.completeInsertWindow()
        else:
            self.showForm()

    def openMultiInsertWindow(self, addButtons=True):
        """
        Creates a tkinter form using Forms classes. This form aims to insert many Defects
        Args:
            addButtons: boolean value indicating that insertion buttons should be visible. Default to True
        """
        settings = self.mainApp.settings
        settings.reloadSettings()
        results, msg = APIClient.searchDefect("")
        default_values = {}
        
        if results is not None:
            for result in results:
                if result is not None:
                    default_values[result["title"]] = result["risk"]
            self.browse_top_treevw = self.form.addFormTreevw("Defects", ("Title", "Risk"),
                                default_values, side="top", fill="both", width=400, height=8, status="readonly", 
                                binds={"<Double-Button-1>":self.doubleClickDefectView, "<Delete>":self.deleteDefectTemplate})
        self.buttonUpImage = ImageTk.PhotoImage(Image.open(utils.getIconDir()+'up-arrow.png'))
        self.buttonDownImage = ImageTk.PhotoImage(Image.open(utils.getIconDir()+'down-arrow.png'))
        # use self.buttonPhoto
        buttonPan = self.form.addFormPanel(side="top", anchor="center", fill="none")
        btn_down = buttonPan.addFormButton("V", self.moveDownMultiTreeview, side="left", anchor="center", image=self.buttonDownImage)
        btn_down = buttonPan.addFormButton("Î", self.moveUpMultiTreeview, side="right", anchor="center", image=self.buttonUpImage)
        default_values = {}
        self.browse_down_treevw = self.form.addFormTreevw("Defects", ("Title", "Risk"),
                            default_values, side="bottom", fill="both", width=400, height=8, status="readonly")
        if addButtons:
            self.completeInsertWindow()
        else:
            self.showForm()

    def searchCallback(self, searchreq, **options):
        defects_obj, defects_errors = APIClient.searchDefect(searchreq, **options)
        if defects_obj:
            for i, defect in enumerate(defects_obj):
                defects_obj[i]["TITLE"] = defect["title"]
        return defects_obj, defects_errors

    def deleteDefectTemplate(self, event):
        apiclient = APIClient.getInstance()
        sel = self.browse_top_treevw.treevw.selection()
        if len(sel) > 1:
            answer = tk.messagebox.askyesno(
                        "Defect template deletion warning", f"{len(sel)} defects will be deleted from the defect templates database. Are you sure ?")
        for selected in sel:
            item = self.browse_top_treevw.treevw.item(selected)
            if item["text"].strip() != "":
                defect_m = self.findDefectTemplateByTitle(item["text"].strip())
                if isinstance(defect_m, Defect):
                    if len(sel) == 1:
                        answer = tk.messagebox.askyesno(
                            "Defect template deletion warning", f"{defect_m.title} will be deleted from the defect templates database. Are you sure ?")
                        if not answer:
                            return
                    apiclient.deleteDefectTemplate(defect_m.getId())
        self.browse_top_treevw.deleteItem()

    def openInChildDialog(self, defect_model, isTemplate=True):
        from pollenisatorgui.core.application.dialogs.ChildDialogDefectView import ChildDialogDefectView
        defect_model.isTemplate = isTemplate
        if defect_model.isTemplate:
            title = "Edit a security defect template"
        else:
            title = "Edit a security defect"
        dialog = ChildDialogDefectView(self.mainApp, title, self.mainApp.settings, defect_model)
        self.mainApp.wait_window(dialog.app)
        return dialog.rvalue

    def findDefectTemplateByTitle(self, title, multi=False):
        apiclient = APIClient.getInstance()
        defects_matching, msg = apiclient.searchDefect(title)
        if defects_matching is not None:
            if len(defects_matching) >= 1 and not multi:
                return Defect(defects_matching[0])
            else:
                return defects_matching
            

    def doubleClickDefectView(self, event):
        item = self.browse_top_treevw.treevw.identify("item", event.x, event.y)
        if item is None or item == '':
            return
        title = self.browse_top_treevw.treevw.item(item)["text"]
        defects_matching = self.findDefectTemplateByTitle(title)
        self.openInChildDialog(defects_matching)

    def moveDownMultiTreeview(self, _event):
        for iid in self.browse_top_treevw.selection():
            item = self.browse_top_treevw.item(iid)
            self.browse_down_treevw.addItem("","end", iid, text=item["text"], values=item["values"])
        self.browse_top_treevw.deleteItem()

    def moveUpMultiTreeview(self, _event):
        for iid in self.browse_down_treevw.selection():
            item = self.browse_down_treevw.item(iid)
            self.browse_top_treevw.addItem("","end", iid, text=item["text"], values=item["values"])
        self.browse_down_treevw.deleteItem()

    def openModifyWindow(self, addButtons=True):
        """
        Creates a tkinter form using Forms classes.
        This form aims to update or delete an existing Defect
        Args:
            addButtons: boolean value indicating that insertion buttons should be visible. Default to True
        """
        modelData = self.controller.getData()
        settings = self.mainApp.settings
        settings.reloadSettings()
        globalPanel = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5)
        topPanel = globalPanel.addFormPanel(grid=True)
        row = 0
        if modelData.get("ip", "") != "":
            topPanel.addFormLabel("IP", row=row, column=0)
            topPanel.addFormStr(
                "IP", '', modelData["ip"], None, column=1, row=row, state="readonly")
            row += 1
            if modelData.get("port", "") != "" and modelData["proto"] is not None:
                topPanel.addFormLabel("Port", row=row, column=0)
                port_str = modelData["proto"] + \
                    "/" if modelData["proto"] != "tcp" else ""
                port_str += modelData["port"]
                topPanel.addFormStr(
                    "Port", '', port_str, None, column=1, row=row, state="readonly")
                row += 1
        if not self.controller.isAssigned():
            if not self.controller.model.isTemplate:
                topPanel.addFormSearchBar("Search Defect", APIClient.searchDefect, globalPanel, row=row, column=1, autofocus=False)
                row += 1
            topPanel.addFormLabel("Title", row=row, column=0)
            topPanel.addFormStr(
                "Title", ".+", modelData["title"], width=50, row=row, column=1)
            row += 1
            topPanel = globalPanel.addFormPanel(grid=True)
            row = 0
            topPanel.addFormLabel("Ease", row=row)
            self.easeForm = topPanel.addFormCombo(
                "Ease", Defect.getEases(), modelData["ease"], width=10, row=row, column=1, binds={"<<ComboboxSelected>>": self.updateRiskBox})
            topPanel.addFormHelper("0: Trivial to exploit, no tool required\n1: Simple technics and public tools needed to exploit\n2: public vulnerability exploit requiring security skills and/or the development of simple tools.\n3: Use of non-public exploits requiring strong skills in security and/or the development of targeted tools", row=row, column=2)
            topPanel.addFormLabel("Impact", row=row, column=3)
            self.impactForm = topPanel.addFormCombo(
                "Impact", Defect.getImpacts(), modelData["impact"], width=10, row=row, column=4, binds={"<<ComboboxSelected>>": self.updateRiskBox})
            topPanel.addFormHelper("0: No direct impact on system security\n1: Impact isolated on precise locations of pentested system security\n2: Impact restricted to a part of the system security.\n3: Global impact on the pentested system security.", row=row, column=5)
            topPanel.addFormLabel("Risk", row=row, column=6)
            self.riskForm = topPanel.addFormCombo(
                "Risk", Defect.getRisks(), modelData["risk"], width=10, row=row, column=7)
            topPanel.addFormHelper(
                "0: small risk that might be fixed\n1: moderate risk that need a planed fix\n2: major risk that need to be fixed quickly.\n3: critical risk that need an immediate fix or an immediate interruption.", row=row, column=8)
            row += 1
            chklistPanel = globalPanel.addFormPanel(grid=True)
            defect_types = settings.getPentestTypes().get(settings.getPentestType(), [])
            for savedType in modelData["type"]:
                if savedType.strip() not in defect_types:
                    defect_types.insert(0, savedType)
            chklistPanel.addFormChecklist("Type", defect_types, modelData["type"])
            topPanel = globalPanel.addFormPanel(grid = True)
            row=0
            if not self.controller.model.isTemplate:
                topPanel.addFormLabel("Redactor", row=row)
                topPanel.addFormCombo("Redactor", list(set(self.mainApp.settings.getPentesters()+["N/A"]+[modelData["redactor"]])), modelData["redactor"], row=row, column=1)
            topPanel.addFormLabel("Language", row=row, column=2)
            topPanel.addFormStr("Language", "", modelData["language"], row=row, column=3)
            row += 1
            topPanel = globalPanel.addFormPanel()
            topPanel.addFormText("Synthesis", r"", modelData.get("synthesis","Synthesis"), state="readonly" if self.controller.isAssigned() else "",  height=2, side="top")
            topPanel.addFormText("Description", r"", modelData.get("description", "Description"), side="top")
            topPanel.addFormButton("Edit fixes", self.openFixesWindow)
        else:
            topPanel.addFormHidden("Title", modelData.get("title", ""))
            topPanel.addFormHidden("Ease", modelData.get("ease", ""))
            topPanel.addFormHidden("Impact", modelData.get("impact", ""))
            topPanel.addFormHidden("Risk", modelData.get("risk", ""))
            types = modelData.get("type", [])
            type_dict = dict()
            for type in types:
                type_dict[type] = 1
            topPanel.addFormHidden("Type", type_dict)
            topPanel.addFormHidden("Language", modelData.get("language", ""))
            topPanel.addFormHidden("Synthesis", modelData.get("synthesis", ""))
            topPanel.addFormHidden("Description", modelData.get("description", ""))
            notesPanel = globalPanel.addFormPanel()
            notesPanel.addFormLabel("Notes", side="top")
            notesPanel.addFormText(
                "Notes", r"", modelData["notes"], None, side="top", height=10)
        if not self.controller.model.isTemplate:
            proofPanel = globalPanel.addFormPanel(grid=True)
            i = 0
            for proof in modelData["proofs"]:
                proofPanel.addFormLabel("Proof "+str(i), proof, row=i, column=0)
                proofPanel.addFormButton("View", lambda event, obj=i: self.viewProof(
                    event, obj), row=i, column=1)
                proofPanel.addFormButton("Delete", lambda event, obj=i: self.deleteProof(
                    event, obj), row=i, column=2)
                i += 1
            proofPanel = globalPanel.addFormPanel()
            self.formFile = proofPanel.addFormFile("Add proofs", r"", "", width=100, height=3)
        self.formFixes = globalPanel.addFormHidden("Fixes", modelData["fixes"])
        if not self.controller.model.isTemplate:
            actionsPan = globalPanel.addFormPanel()
            actionsPan.addFormButton("Create defect template from this", self.saveAsDefectTemplate)
        if addButtons:
            self.completeModifyWindow(addTags=False)
        else:
            self.showForm()

    def openFixesWindow(self, _event=None):
        dialog = ChildDialogFixes(None, self)
        dialog.app.wait_window(dialog.app)
        if dialog.rvalue is None:
            return
        self.formFixes.setValue(dialog.rvalue)

    def updateRiskBox(self, _event=None):
        """Callback when ease or impact is modified.
        Calculate new resulting risk value
        Args
            _event: mandatory but not used
        """
        ease = self.easeForm.getValue()
        impact = self.impactForm.getValue()
        risk = Defect.getRisk(ease, impact)
        self.riskForm.setValue(risk)

    def viewProof(self, _event, obj):
        """Callback when view proof is clicked.
        Download and display the file 
        Args
            _event: mandatory but not used
            obj: the clicked index proof
        """
        proof_local_path = self.controller.getProof(obj)
        if proof_local_path is not None:
            if os.path.isfile(proof_local_path):
                res = utils.openPathForUser(proof_local_path)
                if not res:
                    tk.messagebox.showerror("Could not open", "Failed to open this file.")
                    proof_local_path = None
                    return
        if proof_local_path is None:
            tk.messagebox.showerror(
                "Download failed", "the file does not exist on sftp server")

    def deleteProof(self, _event, obj):
        """Callback when delete proof is clicked.
        remove remote proof and update window
        Args
            _event: mandatory but not used
            obj: the clicked index proof
        """
        self.controller.deleteProof(obj)
        self.form.clear()
        for widget in self.appliViewFrame.winfo_children():
            widget.destroy()
        self.openModifyWindow()

    def addAProof(self, _event):
        """Callback when add proof is clicked.
        Add proof and update window
        Args
            _event: mandatory but not used
        """
        values = self.formFile.getValue()
        for val in values:
            self.controller.addAProof(val)
        self.form.clear()
        for widget in self.appliViewFrame.winfo_children():
            widget.destroy()
        self.openModifyWindow()

    def beforeDelete(self, iid=None):
        """Called before defect deletion.
        Will attempt to remove this defect from global defect table.
        Args:
            iid: the mongo ID of the deleted defect
        """
        if iid is None:
            if self.controller is not None:
                iid = self.controller.getDbId()
        if iid is not None:
            for module in self.mainApp.modules:
                if callable(getattr(module["object"], "removeItem", None)):
                    module["object"].removeItem(iid)
    def addInTreeview(self, parentNode=None, _addChildren=True):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
            _addChildren: not used here
        """
        if not self.controller.isAssigned():
            # Unassigned defect are loaded on the report tab
            return
        if self.controller.model is None:
            return
        if parentNode is None:
            parentNode = DefectView.DbToTreeviewListId(
                self.controller.getParentId())
            nodeText = str(self.controller.getModelRepr())
        elif parentNode == '':
            nodeText = self.controller.getDetailedString()
        else:
            parentNode = DefectView.DbToTreeviewListId(parentNode)
            nodeText = str(self.controller.getModelRepr())
        try:
            parentNode = self.appliTw.insert(
                self.controller.getParentId(), 0, parentNode, text="Defects", image=self.getIcon())
        except TclError:
            pass
        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}
        try:
            self.appliTw.insert(parentNode, "end", str(self.controller.getDbId()),
                                text=nodeText, tags=self.controller.getTags(), image=self.getIcon())
        except TclError:
            pass
        if "hidden" in self.controller.getTags():
            self.hide()

    @classmethod
    def DbToTreeviewListId(cls, parent_db_id):
        """Converts a mongo Id to a unique string identifying a list of defects given its parent
        Args:
            parent_db_id: the parent node mongo ID
        Returns:
            A string that should be unique to describe the parent list of defect node
        """
        return str(parent_db_id)+"|Defects"

    @classmethod
    def treeviewListIdToDb(cls, treeviewId):
        """Extract from the unique string identifying a list of defects the parent db ID
        Args:
            treeviewId: the treeview node id of a list of defects node
        Returns:
            the parent object mongo id as string
        """
        return str(treeviewId).split("|")[0]

    def multi_insert(self):
        values = self.browse_down_treevw.getValue()
        for title in values:
            results, msg = APIClient.searchDefect(title)
            if results is not None:
                result = results[0]
                d_o = Defect()
                if isinstance(result.get("type"), str):
                    types = result["type"].split(",")
                elif isinstance(result.get("type"), list):
                    types = result.get("type")
                else:
                    tk.messagebox.showerror("Multi insert error", f"Invalid defect result for : {title}. Wrong type : {result.get('type')}")
                    return False
                d_o.initialize("", "", "", result["title"], result["synthesis"], result["description"],
                            result["ease"], result["impact"], result["risk"], "N/A", types, result["language"], "", result["fixes"])
                d_o.addInDb()
            #if msg != "":
            #    tk.messagebox.showerror("Could not search defect from knowledge db", msg)
        return True

    def insertReceived(self):
        """Called when a defect insertion is received by notification.
        Insert the node in treeview.
        Also insert it in global report of defect
        """
        if self.controller.model is None:
            return
        if self.controller.isAssigned():
            super().insertReceived()
        else:
            for module in self.mainApp.modules:
                if callable(getattr(module["object"], "addDefect", None)):
                    module["object"].addDefect(self.controller.model)
    
    def updateReceived(self):
        """Called when a defect update is received by notification.
        Update the defect node and the report defect table.
        """
        if self.controller.model is None:
            return
        if not self.controller.isAssigned():
            for module in self.mainApp.modules:
                if callable(getattr(module["object"], "updateDefectInTreevw", None)):
                    module["object"].updateDefectInTreevw(self.controller.model)
        super().updateReceived()

    def saveAsDefectTemplate(self, _event):
        res = self.controller.model.addInDefectTemplates()
        defect_m = self.findDefectTemplateByTitle(self.controller.model.title)
        self.openInChildDialog(defect_m)