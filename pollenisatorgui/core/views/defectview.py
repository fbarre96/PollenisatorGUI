"""View for defect object. Handle node in treeview and present forms to user when interacted with."""

from tkinter import TclError
import tkinter as tk
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.views.viewelement import ViewElement
from pollenisatorgui.core.models.defect import Defect
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.components.apiclient import APIClient
from PIL import ImageTk, Image
from shutil import which
from customtkinter import *
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
        apiclient = APIClient.getInstance()
        modelData = self.controller.getData()
        topPanel = self.form.addFormPanel(grid=True)
        s = topPanel.addFormSearchBar("Search Defect", self.searchCallback, self.form, row=0, column=0)
        topPanel = self.form.addFormPanel(grid=True)
        topPanel.addFormLabel("Search Language",row=1, column=0)
        lang = topPanel.addFormCombo("Lang", apiclient.getLangList(), default=settings.db_settings.get("lang", "en"), width=100, row=1, column=1)
        topPanel.addFormLabel("Only defect for type",row=2, column=0)
        perimeter = topPanel.addFormStr("perimeter", default=settings.db_settings.get("pentest_type", ""), row=2, column=1)
        s.addOptionForm(lang, "lang")
        s.addOptionForm(perimeter, "perimeter")
        topPanel.addFormLabel("Results",row=3, column=0)
        result = topPanel.addFormCombo("Result", [""], default="", width=200, row=3, column=1)
        s.setResultForm(result)
        topPanel = self.form.addFormPanel(grid=True)
        topPanel.addFormLabel("Title_lbl", text="Title")
        topPanel.addFormStr("Title", r".+", "", column=1, width=400)
        topPanel = self.form.addFormPanel(grid=True)
        topPanel.addFormLabel("Ease")
        self.easeForm = topPanel.addFormCombo(
            "Ease", Defect.getEases(), column=1, command=self.updateRiskBox, binds={"<<ComboboxSelected>>": self.updateRiskBox})
        topPanel.addFormHelper("0: Trivial to exploit, no tool required\n1: Simple technics and public tools needed to exploit\n2: public vulnerability exploit requiring security skills and/or the development of simple tools.\n3: Use of non-public exploits requiring strong skills in security and/or the development of targeted tools", column=2)
        topPanel.addFormLabel("Impact", column=3)
        self.impactForm = topPanel.addFormCombo(
            "Impact", Defect.getImpacts(),command=self.updateRiskBox, column=4, binds={"<<ComboboxSelected>>": self.updateRiskBox})
        topPanel.addFormHelper("0: No direct impact on system security\n1: Impact isolated on precise locations of pentested system security\n2: Impact restricted to a part of the system security.\n3: Global impact on the pentested system security.", column=5)
        topPanel.addFormLabel("Risk", column=6)
        self.riskForm = topPanel.addFormCombo(
            "Risk", Defect.getRisks(), modelData["risk"],  column=7)
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
        
        topPanel = self.form.addFormPanel()
        settings = self.mainApp.settings
        topPanel.addFormText("Synthesis", r"", "Synthesis", state="readonly" if self.controller.isAssigned() else "", side="top", height=3)
        if not self.controller.isAssigned():
            topPanel = self.form.addFormPanel()
            topPanel.addFormMarkdown("Description", r"", "Description", side="top", height=300)
        else:
            topPanel.addFormHidden("Description", modelData.get("description", ""))
            notesPanel = self.form.addFormPanel()
            notesPanel.addFormLabel("Notes", side="top")
            notesPanel.addFormText("Notes", r"", notes, None, side="top")
        #proofsPanel = self.form.addFormPanel()
        #proofsPanel.addFormFile("Proof", r"", text="Add proof",height=3)
        self.form.addFormHidden("ip", modelData["ip"])
        self.form.addFormHidden("proto", modelData["proto"])
        self.form.addFormHidden("port", modelData["port"])
        self.form.addFormHidden("Fixes", [])
        if addButtons:
            self.completeInsertWindow()
        else:
            self.showForm()
        self.updateRiskBox()

    def insert(self, _event=None):
        """
        Entry point to the model doInsert function.

        Args:
            _event: automatically filled if called by an event. Not used
        Returns:
            * a boolean to shwo success or failure
            * an empty message on success, an error message on failure
        """
        res, msg = super().insert(_event=None)
        if res:
            apiclient = APIClient.getInstance()
            results, msg = apiclient.searchDefect(self.controller.model.title, check_api=False)
            if results is not None and len(results) == 0:
                dialog = ChildDialogQuestion(self.mainApp, "Create defect template", "This defect seems new. Do you want to create a defect template with this defect?")
                self.mainApp.wait_window(dialog.app)
                if dialog.rvalue == "Yes":
                    self.saveAsDefectTemplate()
        return res

    def openMultiModifyWindow(self, addButtons=True):
        self.form.clear()
        settings = self.mainApp.settings
        settings.reloadSettings()
        apiclient = APIClient.getInstance()
        results, msg = apiclient.searchDefect("", check_api=False)
        default_values = {}
        formFilter = self.form.addFormPanel(grid=True)
        lbl_filter_title = formFilter.addFormLabel("Filters")
        self.str_filter_title = formFilter.addFormStr("Title", "", placeholder_text="title", row=0, column=1, binds={"<Key-Return>":  self.filter})
        formFilter.addFormLabel("Risk", row=0, column=2)
        risks = set([result["risk"] for result in results]+[""])
        self.box_filter_risk = formFilter.addFormCombo("Risk", risks, "", command=self.filter, width=100, row=0, column=3)
        formFilter.addFormLabel("Perimeter", row=0, column=4)
        default_perimeter = settings.getPentestType()
        perimeters = set()
        perimeters.add(default_perimeter)
        perimeters.add("")
        for result in results:
            for perimeter in result.get("perimeter", "").split(","):
                perimeters.add(perimeter)
        self.box_filter_perimeter = formFilter.addFormCombo("Perimeter", perimeters, default_perimeter , command=self.filter, width=100, row=0, column=5)
        formFilter.addFormLabel("Lang", row=0, column=6)
        langs = set([result["language"] for result in results]+[""])
        default_lang = settings.db_settings.get("lang", "en")
        self.box_filter_lang = formFilter.addFormCombo("Lang", langs, default_lang, command=self.filter, width=100, row=0, column=7)
        formFilterSecond = self.form.addFormPanel(grid=True)
        lbl_filter_title = formFilterSecond.addFormLabel("Show only results from")
        self.box_filter_source = formFilterSecond.addFormCombo("Source", ["All", "Local Templates", "API"], "All", command=self.filter, row=0, column=1)
        formTreevw = self.form.addFormPanel()
        if results is not None:
            for result in results:
                if result is not None:
                    default_values[str(result.get("_id", result.get("id")))] = (result["title"], result["risk"], result["language"], result.get("perimeter", settings.getPentestType()), result["source"])
            self.browse_top_treevw = formTreevw.addFormTreevw("Defects", ("Title", "Risk", "Lang", "Perimeter", "Source"),
                                default_values, side="top", fill="both", width=500, height=8, status="readonly", 
                                binds={"<Double-Button-1>":self.doubleClickDefectView, "<Delete>":self.deleteDefectTemplate})
            
        panel_action = self.form.addFormPanel()
        self.import_image = CTkImage(Image.open(utils.getIcon("import.png")))
        self.export_image = CTkImage(Image.open(utils.getIcon("download.png")))
        panel_action.addFormButton("Import", self.importDefectTemplates, image=self.import_image)
        panel_action.addFormButton("Export", self.exportDefectTemplates, image=self.export_image)
        if addButtons:
            self.completeModifyWindow()
        else:
            self.showForm()
        self.filter()

    def openMultiInsertWindow(self, addButtons=True):
        """
        Creates a tkinter form using Forms classes. This form aims to insert many Defects
        Args:
            addButtons: boolean value indicating that insertion buttons should be visible. Default to True
        """
        settings = self.mainApp.settings
        settings.reloadSettings()
        apiclient = APIClient.getInstance()
        results, msg = apiclient.searchDefect("")
        default_values = {}
        formFilter = self.form.addFormPanel(grid=True)
        lbl_filter_title = formFilter.addFormLabel("Filters")
        self.str_filter_title = formFilter.addFormStr("Title", "", placeholder_text="title", row=0, column=1, binds={"<Key-Return>":  self.filter})
        formFilter.addFormLabel("Risk", row=0, column=2)
        risks = set([result["risk"] for result in results]+[""])
        self.box_filter_risk = formFilter.addFormCombo("Risk", risks, "", command=self.filter, width=100, row=0, column=3)
        formFilter.addFormLabel("Perimeter", row=0, column=4)
        default_perimeter = settings.getPentestType()
        perimeters = set()
        perimeters.add(default_perimeter)
        perimeters.add("")
        for result in results:
            for perimeter in result["perimeter"].split(","):
                perimeters.add(perimeter)
        self.box_filter_perimeter = formFilter.addFormCombo("Perimeter", perimeters, default_perimeter , command=self.filter, width=100, row=0, column=5)
        formFilter.addFormLabel("Lang", row=0, column=6)
        langs = set([result["language"] for result in results]+[""])
        default_lang = settings.db_settings.get("lang", "en")
        self.box_filter_lang = formFilter.addFormCombo("Lang", langs, default_lang, command=self.filter, width=100, row=0, column=7)
        formFilterSecond = self.form.addFormPanel(grid=True)
        lbl_filter_title = formFilterSecond.addFormLabel("Show only results from")
        self.box_filter_source = formFilterSecond.addFormCombo("Source", ["All", "Local Templates", "API"], "All", command=self.filter, row=0, column=1)
        formTreevw = self.form.addFormPanel()
        if results is not None:
            for result in results:
                if result is not None:
                    default_values[str(result.get("_id", result.get("id")))]  = (result["title"], result["risk"], result["language"], result["perimeter"], result["source"])
            self.browse_top_treevw = formTreevw.addFormTreevw("Defects", ("Title", "Risk", "Lang", "Perimeter", "Source"),
                                default_values, side="top", fill="both", width=500, height=8, status="readonly", 
                                binds={"<Double-Button-1>":self.doubleClickDefectView, "<Delete>":self.deleteDefectTemplate})
            
        self.buttonUpImage = CTkImage(Image.open(utils.getIconDir()+'up-arrow.png'))
        self.buttonDownImage = CTkImage(Image.open(utils.getIconDir()+'down-arrow.png'))
        # use self.buttonPhoto
        buttonPan = self.form.addFormPanel(side="top", anchor="center", fill="none")
        btn_down = buttonPan.addFormButton("Add to report", self.moveDownMultiTreeview, side="left", anchor="center", image=self.buttonDownImage)
        btn_down = buttonPan.addFormButton("Remove from report", self.moveUpMultiTreeview, side="right", anchor="center", image=self.buttonUpImage)
        default_values = {}
        self.browse_down_treevw = self.form.addFormTreevw("Defects", ("Title", "Risk"),
                            default_values, side="bottom", fill="both", width=500, height=8, status="readonly")
        if addButtons:
            self.completeInsertWindow()
        else:
            self.showForm()
        self.filter()

    def filter(self, event=None):
        title = self.str_filter_title.getValue()
        lang = self.box_filter_lang.getValue()
        perimeter = self.box_filter_perimeter.getValue()
        risk = self.box_filter_risk.getValue()
        source = self.box_filter_source.getValue()
        if source == "Local Templates":
            source = "local"
        elif source == "All":
            source = True
        else:
            source = source.lower()
        
        self.browse_top_treevw.filter(title, risk, lang, perimeter, source)

    
    def searchCallback(self, searchreq, **options):
        defects_obj, defects_errors = APIClient.getInstance().searchDefect(searchreq, **options)
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
        defects_matching, msg = apiclient.searchDefect(title, check_api=False)
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

    def moveDownMultiTreeview(self, _event=None):
        for iid in self.browse_top_treevw.selection():
            item = self.browse_top_treevw.item(iid)
            self.browse_down_treevw.addItem("","end", iid, text=item["text"], values=item["values"])
        self.browse_top_treevw.deleteItem()

    def moveUpMultiTreeview(self, _event=None):
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
        self.form.clear()
        modelData = self.controller.getData()
        settings = self.mainApp.settings
        settings.reloadSettings()
        self.delete_image = CTkImage(Image.open(utils.getIconDir()+'delete.png'))
        self.edit_image = CTkImage(Image.open(utils.getIconDir()+'stylo.png'))
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
                topPanel.addFormSearchBar("Search Defect", APIClient.getInstance().searchDefect, globalPanel, row=row, column=1, autofocus=False)
                row += 1
            topPanel.addFormLabel("Title_lbl", text="Title", row=row, column=0)
            topPanel.addFormStr(
                "Title", ".+", modelData["title"],  width=400, row=row, column=1)
            row += 1
            topPanel = globalPanel.addFormPanel(grid=True)
            row = 0
            topPanel.addFormLabel("Ease", row=row)
            self.easeForm = topPanel.addFormCombo(
                "Ease", Defect.getEases(), modelData["ease"], command=self.updateRiskBox, row=row, column=1, binds={"<<ComboboxSelected>>": self.updateRiskBox})
            topPanel.addFormHelper("0: Trivial to exploit, no tool required\n1: Simple technics and public tools needed to exploit\n2: public vulnerability exploit requiring security skills and/or the development of simple tools.\n3: Use of non-public exploits requiring strong skills in security and/or the development of targeted tools", row=row, column=2)
            topPanel.addFormLabel("Impact", row=row, column=3)
            self.impactForm = topPanel.addFormCombo(
                "Impact", Defect.getImpacts(), modelData["impact"], command=self.updateRiskBox, row=row, column=4, binds={"<<ComboboxSelected>>": self.updateRiskBox})
            topPanel.addFormHelper("0: No direct impact on system security\n1: Impact isolated on precise locations of pentested system security\n2: Impact restricted to a part of the system security.\n3: Global impact on the pentested system security.", row=row, column=5)
            topPanel.addFormLabel("Risk", row=row, column=6)
            self.riskForm = topPanel.addFormCombo(
                "Risk", Defect.getRisks(), modelData["risk"],  row=row, column=7)
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
            topPanel.addFormText("Synthesis", r"", modelData.get("synthesis","Synthesis"), state="readonly" if self.controller.isAssigned() else "",  height=40, side="top")
            topPanel.addFormMarkdown("Description", r"", modelData.get("description", "Description"), side="top", just_editor=True)
            topPanel.addFormButton("Edit fixes", self.openFixesWindow,  image=self.edit_image)
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
                "Notes", r"", modelData["notes"], None, side="top", height=40)
        if not self.controller.model.isTemplate:
            if modelData["proofs"]:
                print("TODO PROOFS")
                # proofPanel = globalPanel.addFormPanel(grid=True)
                # i = 0
                # for proof in modelData["proofs"]:
                #     proofPanel.addFormLabel("Proof "+str(i), proof, row=i, column=0)
                #     proofPanel.addFormButton("View", lambda event, obj=i: self.viewProof(
                #         event, obj), row=i, column=1)
                #     proofPanel.addFormButton("Delete", lambda event, obj=i: self.deleteProof(
                #         event, obj), row=i, column=2, image=self.delete_image,
                #             fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                #             border_width=1, border_color="firebrick1", hover_color="tomato")
                #     i += 1
            #proofPanel = globalPanel.addFormPanel()
            #self.formFile = proofPanel.addFormFile("Add proofs", r"", "",  height=3)
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
        self.controller.update_fixes(dialog.rvalue)

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

    def addAProof(self, _event=None):
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
        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}
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
        try:
            self.appliTw.insert(parentNode, "end", str(self.controller.getDbId()),
                                text=nodeText, tags=self.controller.getTags(), image=self.getIcon())
        except TclError:
            pass
    
        if "hidden" in self.controller.getTags():
            self.hide("tags")
        if self.mainApp.settings.is_checklist_view():
            self.hide("checklist_view")

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
            results, msg = APIClient.getInstance().searchDefect(title)
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
                            result["ease"], result["impact"], result["risk"], "N/A", types, result["language"], "", None, result["fixes"])
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
    
    def updateReceived(self, obj=None, old_obj=None):
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

    def saveAsDefectTemplate(self, _event=None):
        settings = self.mainApp.settings
        settings.reloadSettings()
        perimeter = settings.getPentestType()
        self.controller.model.perimeter = perimeter 
        res = self.controller.model.addInDefectTemplates()
        defect_m = self.findDefectTemplateByTitle(self.controller.model.title)
        self.openInChildDialog(defect_m)

    def importDefectTemplates(self, _event=None):
        filename = ""
        f = tk.filedialog.askopenfilename(defaultextension=".json")
        if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return
        filename = str(f)
        try:
            apiclient = APIClient.getInstance()
            success = apiclient.importDefectTemplates(filename)
        except IOError:
            tk.messagebox.showerror(
                "Import defects templates", "Import failed. "+str(filename)+" was not found or is not a file.")
            return False
        if not success:
            tk.messagebox.showerror("Defects templates import", "Defects templatest failed")
        else:
            tk.messagebox.showinfo("Defects templates import", "Defects templates completed")
        self.openMultiModifyWindow(False)
        return success
    
    def exportDefectTemplates(self, _event=None):
        apiclient = APIClient.getInstance()
        res = apiclient.exportDefectTemplates(self.mainApp)
        if res is None:
            return
        else:
            res, msg = res # unpack tuple
        if res:
            tk.messagebox.showinfo(
                "Export Defect templates", "Export completed in "+str(msg))
        else:
            tk.messagebox.showinfo(msg)

    