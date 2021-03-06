"""
Module to add defects and export them
"""
import tkinter.ttk as ttk
import tkinter as tk
import tkinter.messagebox
import os
from PIL import ImageTk, Image
from shutil import which
from os.path import isfile, join
from bson.objectid import ObjectId
from datetime import datetime
from core.Components.apiclient import APIClient
from core.Models.Defect import Defect
from core.Components.Utils import getIconDir, execute
from core.Application.Dialogs.ChildDialogCombo import ChildDialogCombo
from core.Application.Dialogs.ChildDialogProgress import ChildDialogProgress
from core.Application.Dialogs.ChildDialogInfo import ChildDialogInfo
from core.Application.Dialogs.ChildDialogQuestion import ChildDialogQuestion
from core.Application.Dialogs.ChildDialogDefectView import ChildDialogDefectView
from core.Application.Dialogs.ChildDialogRemarkView import ChildDialogRemarkView
from core.Forms.FormHelper import FormHelper
from core.Models.Remark import Remark	
from core.Views.RemarkView import RemarkView

class Report:
    """
    Store elements to report and create docx or xlsx with them
    """
    iconName = "tab_report.png"
    tabName = "    Report    "

    def __init__(self, parent, settings):

        """
        Constructor
        """
        try:
            templates = APIClient.getInstance().getTemplateList()
        except:
            templates = []
        self.docx_models = [f for f in templates if f.endswith(".docx")]
        self.pptx_models = [f for f in templates if f.endswith(".pptx")]
        self.mainRedac = "N/A"
        self.settings = settings
        self.dragging = None
        self.parent = None
        self.reportFrame = None
        self.rowHeight = 0
        self.pane_base_height = 31
        self.style = None
        self.treevw = None
        self.ent_client = None
        self.ent_contract = None
        self.combo_word = None
        self.combo_pptx = None
        self.btn_template_photo = None
        self.lastMovedTo = None
        self.movingSelection = None
        return

    def open(self):
        self.refreshUI()
        return True

    

    def refreshUI(self):
        """
        Reload informations and reload them into the widgets
        """
        templates = APIClient.getInstance().getTemplateList()
        self.docx_models = [f for f in templates if f.endswith(".docx")]
        self.pptx_models = [f for f in templates if f.endswith(".pptx")]
        self.combo_word.configure(values=self.docx_models)
        self.combo_pptx.configure(values=self.pptx_models)
        self.settings.reloadSettings()
        pentest_type = self.settings.getPentestType().lower()
        
        pentesttype_docx_models = [f for f in self.docx_models if pentest_type in f.lower()]
        if pentesttype_docx_models:
            self.combo_word.set(pentesttype_docx_models[0])
        elif self.docx_models:
            self.combo_word.set(self.docx_models[0])

        pentesttype_pptx_models = [f for f in self.pptx_models if pentest_type in f.lower()]
        if pentesttype_pptx_models:
            self.combo_pptx.set(pentesttype_pptx_models[0])
        elif self.pptx_models:
            self.combo_pptx.set(self.pptx_models[0])

    def initUI(self, parent, nbk, treevw):
        """
        Initialize window and widgets.
        """
        if self.parent is not None:  # Already initialized
            self.reset()
            self.fillWithDefects()
            self.fillWithRemarks()
            return
        self.parent = parent
        ### MAIN PAGE FRAME ###
        self.reportFrame = ttk.Frame(parent)

        ### DEFECT TABLE ###
        self.rowHeight = 20
        self.style = ttk.Style()
        self.style.configure('Report.Treeview', rowheight=self.rowHeight)
        # REMARK TREEVW	
        self.remarksFrame = ttk.LabelFrame(self.reportFrame, text="Remarks table")	
        self.paned_remarks = tk.PanedWindow(self.remarksFrame, orient=tk.VERTICAL, height=900)	
        self.remarkframeTw = ttk.Frame(self.paned_remarks)	
        self.remarks_treevw = ttk.Treeview(self.remarkframeTw, style='Report.Treeview', height=0)	
        self.remarks_treevw["columns"] = ["Title", "Type"]	
        self.remarks_treevw.heading("#0", text='Title', anchor=tk.W)	
        self.remarks_treevw.column("#0", width=150, anchor=tk.W)	
        self.remarks_treevw.bind("<Delete>", self.deleteSelectedRemarkItem)	
        
        self.remarks_treevw.grid(row=0, column=0, sticky=tk.NSEW)	
        scbVSel = ttk.Scrollbar(self.remarkframeTw,	
                                orient=tk.VERTICAL,	
                                command=self.remarks_treevw.yview)	
        self.remarks_treevw.configure(yscrollcommand=scbVSel.set)	
        scbVSel.grid(row=0, column=1, sticky=tk.NS)	
        self.remarkframeTw.columnconfigure(0, weight=1)	
        self.remarkframeTw.rowconfigure(0, weight=1)	
        self.remarkframeTw.pack(side=tk.TOP, fill=tk.BOTH, pady=5, expand=1, padx=5)	
        frameAllBelow = ttk.Frame(self.paned_remarks)	
        frameBtnRemarks = ttk.Frame(frameAllBelow)	
        btn_addRemark = ttk.Button(	
            frameBtnRemarks, text="Add remark", command=self.addRemarkCallback)	
        btn_addRemark.pack(side=tk.LEFT, pady=5)	
        btn_delRemark = ttk.Button(	
            frameBtnRemarks, text="Remove selected", command=self.deleteSelectedRemarkItem)	
        btn_delRemark.pack(side=tk.LEFT, pady=5)	
        frameBtnRemarks.pack(side=tk.TOP)	
            
        # DEFECT TREEVW	
        defectLabelFrame = ttk.LabelFrame(frameAllBelow, text="Defects table")	
        self.paned = tk.PanedWindow(defectLabelFrame, orient=tk.VERTICAL, height=800)

        self.frameTw = ttk.Frame(self.paned)
        self.treevw = ttk.Treeview(self.frameTw, style='Report.Treeview', height=0)
        self.treevw['columns'] = ('ease', 'impact', 'risk', 'type', 'redactor')
        self.treevw.heading("#0", text='Title', anchor=tk.W)
        self.treevw.column("#0", anchor=tk.W, width=150)
        self.treevw.heading('ease', text='Ease')
        self.treevw.column('ease', anchor='center', width=40)
        self.treevw.heading('impact', text='Impact')
        self.treevw.column('impact', anchor='center', width=40)
        self.treevw.heading('risk', text='Risk')
        self.treevw.column('risk', anchor='center', width=40)
        self.treevw.heading('type', text='Type')
        self.treevw.column('type', anchor='center', width=10)
        self.treevw.heading('redactor', text='Redactor')
        self.treevw.column('redactor', anchor='center', width=20)
        self.treevw.tag_configure(
            "Critical", background="black", foreground="white")
        self.treevw.tag_configure(
            "Major", background="red", foreground="white")
        self.treevw.tag_configure(
            "Important", background="orange", foreground="white")
        self.treevw.tag_configure(
            "Minor", background="yellow", foreground="black")
        self.treevw.bind("<Double-Button-1>", self.OnDoubleClick)
        self.treevw.bind("<Delete>", self.deleteSelectedItem)
        self.treevw.bind("<Alt-Down>",self.bDown)
        self.treevw.bind("<Alt-Up>",self.bUp)
        self.treevw.bind("<ButtonPress-1>",self.dragStart)
        self.treevw.bind("<ButtonRelease-1>",self.dragRelease, add='+')
        self.treevw.bind("<B1-Motion>",self.dragMove, add='+')
        self.treevw.grid(row=0, column=0, sticky=tk.NSEW)
        scbVSel = ttk.Scrollbar(self.frameTw,
                                orient=tk.VERTICAL,
                                command=self.treevw.yview)
        self.treevw.configure(yscrollcommand=scbVSel.set)
        scbVSel.grid(row=0, column=1, sticky=tk.NS)
        self.frameTw.pack(side=tk.TOP, fill=tk.BOTH, padx=5, pady=10)
        self.frameTw.columnconfigure(0, weight=1)
        self.frameTw.rowconfigure(0, weight=1)
        ### OFFICE EXPORT FRAME ###
        belowFrame = ttk.Frame(self.paned)
        frameBtn = ttk.Frame(belowFrame)
        #lbl_help = FormHelper("DefectHelper", "Use del to delete a defect, use Alt+Arrows to order them")
        #lbl_help.constructView(frameBtn)
        self.buttonUpImage = ImageTk.PhotoImage(Image.open(getIconDir()+'up-arrow.png'))
        self.buttonDownImage = ImageTk.PhotoImage(Image.open(getIconDir()+'down-arrow.png'))
        # use self.buttonPhoto
        btn_down = ttk.Button(frameBtn, image=self.buttonDownImage, command=self.bDown)
        btn_down.pack(side="left", anchor="center")
        btn_up = ttk.Button(frameBtn, image=self.buttonUpImage, command=self.bUp)
        btn_up.pack(side="left", anchor="center")
        btn_delDefect = ttk.Button(
            frameBtn, text="Remove selection", command=self.deleteSelectedItem)
        btn_delDefect.pack(side=tk.RIGHT, padx=5)
        btn_addDefect = ttk.Button(
            frameBtn, text="Add a security defect", command=self.addDefectCallback)
        btn_addDefect.pack(side=tk.RIGHT, padx=5)
        btn_browseDefects = ttk.Button(	
	            frameBtn, text="Browse defects", command=self.browseDefectsCallback)	
        btn_browseDefects.pack(side=tk.RIGHT, padx=5)
        btn_setMainRedactor = ttk.Button(
            frameBtn, text="Set main redactor", command=self.setMainRedactor)
        btn_setMainRedactor.pack(side=tk.RIGHT, padx=5)
        frameBtn.pack(side=tk.TOP, pady=5)
        officeFrame = ttk.LabelFrame(belowFrame, text=" Office reports ")
        ### INFORMATION EXPORT FRAME ###
        informations_frame = ttk.Frame(officeFrame)
        lbl_client = ttk.Label(informations_frame, text="Client's name :")
        lbl_client.grid(row=0, column=0, sticky=tk.E)
        self.ent_client = ttk.Entry(informations_frame, width=50)
        self.ent_client.grid(row=0, column=1, sticky=tk.W)
        lbl_contract = ttk.Label(informations_frame, text="Contract's name :")
        lbl_contract.grid(row=1, column=0, sticky=tk.E)
        self.ent_contract = ttk.Entry(informations_frame, width=50)
        self.ent_contract.grid(row=1, column=1, sticky=tk.W)
        informations_frame.pack(side=tk.TOP, pady=10)
        ### WORD EXPORT FRAME ###
        templatesFrame = ttk.Frame(officeFrame)
        templatesFrame.grid_columnconfigure(2, minsize=70)
        templatesFrame.grid_columnconfigure(3, minsize=300)
        lbl = ttk.Label(
            templatesFrame, text="Word template", background="white")
        lbl.grid(row=0, column=0, sticky=tk.E)
        self.combo_word = ttk.Combobox(templatesFrame, values=self.docx_models, width=50)
        self.combo_word.grid(row=0, column=1)
        btn_word_template_dl = ttk.Button(templatesFrame)
        self.btn_template_photo = tk.PhotoImage(file=os.path.join(getIconDir(), "download.png"))
        btn_word_template_dl.config(image=self.btn_template_photo, command=self.downloadWordTemplate)
        btn_word_template_dl.grid(row=0, column=2, sticky=tk.W)
        btn_word = ttk.Button(
            templatesFrame, text="Generate Word report", command=self.generateReportWord, width=30)
        btn_word.grid(row=0, column=3, sticky=tk.E)
        ### POWERPOINT EXPORT FRAME ###
        lbl = ttk.Label(templatesFrame,
                        text="Powerpoint template", background="white")
        lbl.grid(row=1, column=0, sticky=tk.E, pady=20)
        self.combo_pptx = ttk.Combobox(
            templatesFrame, values=self.pptx_models, width=50)
        self.combo_pptx.grid(row=1, column=1)
        btn_pptx_template_dl = ttk.Button(templatesFrame)
        btn_pptx_template_dl.config(image=self.btn_template_photo, command=self.downloadPptxTemplate)
        btn_pptx_template_dl.grid(row=1, column=2, sticky=tk.W)
        btn_ppt = ttk.Button(
            templatesFrame, text="Generate Powerpoint report", command=self.generateReportPowerpoint, width=30)
        btn_ppt.grid(row=1, column=3, sticky=tk.E)
        templatesFrame.pack(side=tk.TOP, fill=tk.X, pady=10)
        officeFrame.pack(side=tk.TOP, fill=tk.BOTH, pady=10)
        belowFrame.pack(side=tk.TOP, fill=tk.BOTH)
        self.paned.add(self.frameTw)
        self.paned.add(belowFrame)
        self.paned.pack(fill=tk.BOTH, expand=1)
        defectLabelFrame.pack(side=tk.TOP, fill=tk.BOTH, pady=10)	
        frameAllBelow.pack(side=tk.TOP, fill=tk.BOTH)
        self.paned_remarks.add(self.remarkframeTw)	
        self.paned_remarks.add(frameAllBelow)	
        self.paned_remarks.pack(fill=tk.BOTH, expand=1)	
        self.remarksFrame.pack(side=tk.TOP, fill=tk.BOTH)
        self.reportFrame.pack(side=tk.TOP, fill=tk.BOTH, padx=10, pady=10, expand=1)
        self.fillWithDefects()
        self.fillWithRemarks()

    def bDown(self, event=None):
        item_iid = self.treevw.selection()[0]
        children = self.treevw.get_children()
        iid_moving = children.index(item_iid)
        try:
            iid_moved_by = children[iid_moving+1]
            apiclient = APIClient.getInstance()
            apiclient.moveDefect(item_iid, iid_moved_by)
            self.treevw.move(item_iid, '', iid_moving+1)
        except IndexError:
            pass
        return "break"


    def bUp(self, event=None):
        item_iid = self.treevw.selection()[0]
        children = self.treevw.get_children()
        iid_moving = children.index(item_iid)
        try:
            iid_moved_by = children[iid_moving-1]
            apiclient = APIClient.getInstance()
            apiclient.moveDefect(item_iid, iid_moved_by)
            self.treevw.move(item_iid, '', iid_moving-1)
        except IndexError:
            pass
        return "break"

    def dragStart(self, event):
        tv = event.widget
        if tv.identify_row(event.y) not in tv.selection():
            tv.selection_set(tv.identify_row(event.y))    
            self.movingSelection = tv.identify_row(event.y)

    def dragRelease(self, event):
        if self.movingSelection is None or self.lastMovedTo is None:
            return
        tv = event.widget
        apiclient = APIClient.getInstance()
        if tv.identify_row(event.y) in tv.selection():
            apiclient.moveDefect(self.movingSelection, self.lastMovedTo)
            self.movingSelection = None
            self.lastMovedTo = None

    def dragMove(self, event):
        tv = event.widget
        rowToMove = tv.identify_row(event.y)
        moveto = tv.index(rowToMove)    
        self.lastMovedTo = rowToMove if rowToMove != self.movingSelection else self.lastMovedTo
        for s in tv.selection():
            tv.move(s, '', moveto)

    def reset(self):
        """
        reset defect treeview by deleting every item inside.
        """
        for item in self.treevw.get_children():
            self.treevw.delete(item)

    def reset_remarks(self):	
        """	
        reset defect treeview by deleting every item inside.	
        """	
        for item in self.remarks_treevw.get_children():	
            self.remarks_treevw.delete(item)

    def deleteSelectedItem(self, _event=None):
        """
        Remove selected defect from treeview
        Args:
            _event: not used but mandatory
        """
        selected = self.treevw.selection()[0]
        self.removeItem(selected)

    def deleteSelectedRemarkItem(self, _event=None):	
        """	
        Remove selected remark from treeview	
        Args:	
            _event: not used but mandatory	
        """	
        selected = self.remarks_treevw.selection()[0]	
        self.remarks_treevw.delete(selected)	
        remark = Remark.fetchObject({"title":selected})	
        remark.delete()	
        self.resizeDefectTreeview()

    def removeItem(self, toDeleteIid):
        """
        Remove defect from given iid in defect treeview
        Args:
            toDeleteIid: database ID of defect to delete
        """
        try:
            item = self.treevw.item(toDeleteIid)
        except tk.TclError:
            return
        dialog = ChildDialogQuestion(self.parent,
                                     "DELETE WARNING", "Are you sure you want to delete defect "+str(item["text"])+" ?", ["Delete", "Cancel"])
        self.parent.wait_window(dialog.app)
        if dialog.rvalue != "Delete":
            return
        self.treevw.delete(toDeleteIid)
        defectToDelete = Defect.fetchObject({"title": item["text"], "ip":"", "port":"", "proto":""})
        if defectToDelete is not None:
            defectToDelete.delete()
            self.resizeDefectTreeview()

    def removeRemarkItem(self, toDeleteIid):	
        """	
        Remove remark from given iid in defect treeview	
        Args:	
            toDeleteIid: database ID of defect to delete	
        """	
        item = self.remarks_treevw.item(toDeleteIid)	
        dialog = ChildDialogQuestion(self.parent,	
                                        "DELETE WARNING", "Are you sure you want to delete remark "+str(item["text"])+" ?", ["Delete", "Cancel"])	
        self.parent.wait_window(dialog.app)	
        if dialog.rvalue != "Delete":	
            return	
        self.remarks_treevw.delete(toDeleteIid)	
        remarkToDelete = Remark.fetchObject({"title": item["text"]})	
        if remarkToDelete is not None:	
            remarkToDelete.delete()	
            self.resizeRemarkTreeview()

    def addDefectCallback(self):
        """Open an insert defect view form in a child window"""
        dialog = ChildDialogDefectView(self.parent, self.settings)
        self.parent.wait_window(dialog.app)

    def browseDefectsCallback(self):	
        """Open an multiview insert defect view form in a child window"""	
        dialog = ChildDialogDefectView(self.parent, self.settings, None, True)	
        self.parent.wait_window(dialog.app)	
		
    def addRemarkCallback(self):	
        """Open an insert defect view form in a child window"""	
        dialog = ChildDialogRemarkView(self.parent)

    def setMainRedactor(self):
        """Sets a main redactor for a pentest. Each not assigned defect will be assigned to him/her"""
        self.settings.reloadSettings()
        dialog = ChildDialogCombo(self.parent, self.settings.getPentesters()+["N/A"], "Set main redactor", "N/A")
        newVal = self.parent.wait_window(dialog.app)
        if newVal is None:
            return
        if not newVal or newVal.strip() == "":
            return
        columnRedactor = self.treevw['columns'].index("redactor")
        for it in self.treevw.get_children():
            oldValues = self.treevw.item(it)["values"]
            if oldValues[columnRedactor] == "N/A":
                oldValues[columnRedactor] = newVal
                self.treevw.item(it, values=oldValues)
                d_o = Defect({"_id":it})
                d_o.update({"redactor":newVal})
        self.mainRedac = newVal

    def updateDefectInTreevw(self, defect_m, redactor=None):
        """
        Change values of a selected defect in the treeview
        Args:
            defect_m: a defect model with updated values
            redactor: a redactor name for this defect, can be None (default)
        """
        columnEase = self.treevw['columns'].index("ease")
        columnImpact = self.treevw['columns'].index("impact")
        columnRisk = self.treevw['columns'].index("risk")
        columnType = self.treevw['columns'].index("type")
        columnRedactor = self.treevw['columns'].index("redactor")
        oldValues = self.treevw.item(defect_m.getId())["values"]
        oldRisk = oldValues[columnRisk]
        newRisk = defect_m.risk
        newValues = [""]*5
        newValues[columnEase] = defect_m.ease
        newValues[columnImpact] = defect_m.impact
        newValues[columnRisk] = defect_m.risk
        newValues[columnType] = ", ".join(defect_m.mtype)
        newValues[columnRedactor] = defect_m.redactor
        self.treevw.item(defect_m.getId(), text=defect_m.title, tags=(newRisk), values=newValues)
        if self.movingSelection is None:
            self.treevw.move(defect_m.getId(), '', int(defect_m.index))
      
    def OnDoubleClick(self, event):
        """
        Callback for double click on treeview.
        Opens a window to update the double clicked defect view.
        Args:
            event: automatically created with the event catch. stores data about line in treeview that was double clicked.
        """
        item = self.treevw.identify("item", event.x, event.y)
        if item is None or item == '':
            return
        defect_m = Defect.fetchObject({"_id": ObjectId(item)})
        dialog = ChildDialogDefectView(self.parent, self.settings, defect_m)
        self.parent.wait_window(dialog.app)
        self.updateDefectInTreevw(defect_m)

    def fillWithDefects(self):
        """
        Fetch defects that are global (not assigned to an ip) and fill the defect table with them.
        """
        for line in Defect.getDefectTable():
            self.addDefect(Defect(line))

    def fillWithRemarks(self):	
        """	
        Fetch remarks and fill the remarks table with them.	
        """	
        remarks = Remark.fetchObjects({})	
        for remark in remarks:	
            self.addRemark(remark)
    
    def addRemark(self, remark_o):	
        type_of_remark = remark_o.type	
        already_inserted = False	
        already_inserted_iid = None	
        children = self.remarks_treevw.get_children()	
        for child in children:	
            title = self.remarks_treevw.item(child)["text"]	
            if title == remark_o.title:	
                break	
        if not already_inserted:	
            try:	
                self.remarks_treevw.insert('', 'end', remark_o.title, values = (remark_o.type), text=remark_o.title, image=RemarkView.getIcon(remark_o.type))	
            except tk.TclError:	
                # The defect already exists	
                pass	
        self.resizeRemarkTreeview()	
                    
	
	
    def addDefect(self, defect_o):
        """
        Add the given defect object in the treeview
        Args:
            defect_o: a Models.Defect object to be inserted in treeview
        """
        if defect_o is None:
            return
        children = self.treevw.get_children()
        indToInsert = defect_o.index
        types = defect_o.mtype
        types = ", ".join(defect_o.mtype)
        new_values = (defect_o.ease, defect_o.impact,
                      defect_o.risk, types, defect_o.redactor if defect_o.redactor != "N/A" else self.mainRedac)
        already_inserted = False
        already_inserted_iid = None
        for child in children:
            title = self.treevw.item(child)["text"]
            if title == defect_o.title:
                already_inserted = True
                already_inserted_iid = child
                break
        if not already_inserted:
            try:
                self.treevw.insert('', indToInsert, defect_o.getId(), text=defect_o.title,
                                   values=new_values,
                                   tags=(defect_o.risk))
            except tk.TclError:
                # The defect already exists
                already_inserted = True
                already_inserted_iid = defect_o.getId()
        if already_inserted:
            existing = self.treevw.item(already_inserted_iid)
            values = existing["values"]
            if values[4].strip() == "N/A":
                values[4] = defect_o.redactor
            elif defect_o.redactor not in values[4].split(", "):
                values[4] += ", "+defect_o.redactor
            self.treevw.item(already_inserted_iid, values=values)
        self.resizeDefectTreeview()
    
    def resizeDefectTreeview(self):
        currentHeight = len(self.treevw.get_children())
        if currentHeight <= 15:
            self.treevw.config(height=currentHeight)
            sx, sy = self.paned.sash_coord(0)
            if sy <= (currentHeight)*self.rowHeight + self.pane_base_height:
                self.paned.paneconfigure(self.frameTw, height=(currentHeight)*self.rowHeight + self.pane_base_height)
    
    def resizeRemarkTreeview(self):	
        currentHeight = len(self.remarks_treevw.get_children())	
        if currentHeight <= 5:	
            self.remarks_treevw.config(height=currentHeight)	
            sx, sy = self.paned_remarks.sash_coord(0)	
            if sy <= (currentHeight)*self.rowHeight + self.pane_base_height:	
                self.paned_remarks.paneconfigure(self.remarkframeTw, height=(currentHeight)*self.rowHeight + self.pane_base_height)

    def generateReportPowerpoint(self):
        if self.ent_client.get().strip() == "":
            tk.messagebox.showerror(
                "Missing required field", "The client's name input must be filled.")
            return
        if self.ent_contract.get().strip() == "":
            tk.messagebox.showerror(
                "Missing required field", "The contract's name input must be filled.")
            return
        apiclient = APIClient.getInstance()
        toExport = apiclient.getCurrentPentest()
        if toExport != "":
            modele_pptx = str(self.combo_pptx.get())
            dialog = ChildDialogInfo(
                self.parent, "PowerPoint Report", "Creating report . Please wait.")
            dialog.show()
            out_name = apiclient.generateReport(modele_pptx, self.ent_client.get().strip(), self.ent_contract.get().strip(), self.mainRedac)
            dialog.destroy()
            tkinter.messagebox.showinfo(
                "Success", "The document was generated in "+str(out_name))
            if which("xdg-open"):
                os.system("xdg-open "+os.path.dirname(out_name))
            elif which("explorer"):
                os.system("explorer "+os.path.dirname(out_name))
            elif which("open"):
                os.system("open "+os.path.dirname(out_name))

    def generateReportWord(self):
        """
        Export a calendar defects to a word formatted file.
        """
        if self.ent_client.get().strip() == "":
            tk.messagebox.showerror(
                "Missing required field", "The client's name input must be filled.")
            return
        if self.ent_contract.get().strip() == "":
            tk.messagebox.showerror(
                "Missing required field", "The contract's name input must be filled.")
            return
        apiclient = APIClient.getInstance()
        toExport = apiclient.getCurrentPentest()
        if toExport != "":
            modele_docx = str(self.combo_word.get())
            dialog = ChildDialogInfo(
                self.parent, "Word Report", "Creating report . Please wait.")
            dialog.show()
            res = apiclient.generateReport(modele_docx, self.ent_client.get().strip(), self.ent_contract.get().strip(), self.mainRedac)
            dialog.destroy()
            if res == None:
                tkinter.messagebox.showerror(
                    "Failure", str(res))
            tkinter.messagebox.showinfo(
                "Success", "The document was generated in "+str(res))
            if which("xdg-open"):
                os.system("xdg-open "+os.path.dirname(res))
            elif which("explorer"):
                os.system("explorer "+os.path.dirname(res))
            elif which("open"):
                os.system("open "+os.path.dirname(res))
    def downloadWordTemplate(self):
        self._download_and_open_template(self.combo_word.get())

    def downloadPptxTemplate(self):
        self._download_and_open_template(self.combo_pptx.get())

    def _download_and_open_template(self, templateName):
        apiclient = APIClient.getInstance()
        path = apiclient.downloadTemplate(templateName)
        if which("xdg-open") is not None:
            dialog = ChildDialogQuestion(self.parent,
                                        "Template downloaded", "Template was downloaded here : "+str(path)+". Do you you want to open it ?", ["Open", "Cancel"])
            self.parent.wait_window(dialog.app)
            if dialog.rvalue != "Open":
                return
            execute("xdg-open "+str(path))
        else:
            tkinter.messagebox.showinfo(
                "Success", "The template was generated in "+str(path))

    def notify(self, db, collection, iid, action, _parent):
        """
        Callback for the observer implemented in mongo.py.
        Each time an object is inserted, updated or deleted the standard way, this function will be called.

        Args:
            collection: the collection that has been modified
            iid: the mongo ObjectId _id that was modified/inserted/deleted
            action: string "update" or "insert" or "delete". It was the action performed on the iid
            _parent: Not used. the mongo ObjectId of the parent. Only if action in an insert. Not used anymore
        """
        apiclient = APIClient.getInstance()
        if not apiclient.getCurrentPentest() != "":
            return
        if apiclient.getCurrentPentest() != db:
            return
        if action == "update":
            if collection == "defects":
                defect_m = Defect.fetchObject({"_id":ObjectId(iid)})
                self.updateDefectInTreevw(defect_m, )
        elif action == "insert":	
            view = None	
            res = Defect.fetchObject({"_id": ObjectId(iid)})	
            # Defect insertion takes place in calendarTreeview,	
            # Remarks don't appear in the treeview, only in this module, so must notify here	
            if collection == "remarks":	
                self.addRemark(Remark.fetchObject({"_id":ObjectId(iid)}))