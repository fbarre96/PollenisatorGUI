"""
Module to add defects and export them
"""
import tkinter.ttk as ttk
from customtkinter import *
import tkinter as tk
import tkinter.messagebox
import os
import threading
from PIL import ImageTk, Image
from bson.objectid import ObjectId
from pollenisatorgui.core.components.logger_config import logger
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.models.defect import Defect
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.application.dialogs.ChildDialogInfo import ChildDialogInfo
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.application.dialogs.ChildDialogToast import ChildDialogToast
from pollenisatorgui.core.application.dialogs.ChildDialogDefectView import ChildDialogDefectView
from pollenisatorgui.core.application.dialogs.ChildDialogRemarkView import ChildDialogRemarkView
from pollenisatorgui.core.models.remark import Remark	
from pollenisatorgui.core.views.remarkview import RemarkView
from pollenisatorgui.modules.module import Module

class Report(Module):
    """
    Store elements to report and create docx or xlsx with them
    """
    iconName = "tab_report.png"
    tabName = "    Report    "
    collNames = ["defects", "remarks"]
    order_priority = Module.HIGH_PRIORITY
    
    def __init__(self, _parent, settings, tkApp):

        """
        Constructor
        """
        super().__init__()
        self.tkApp = tkApp
        self.langs = ["en"]
        self.docx_models = []
        self.curr_lang = "en"
        self.pptx_models = []
        self.mainRedac = "N/A"
        self.settings = settings
        self.dragging = None
        self.parent = None
        self.reportFrame = None
        self.rowHeight = 0
        self.pane_base_height = 31
        self.style = None
        self.defect_treevw = None
        self.drag_toast = None
        self.combo_word = None
        self.combo_pptx = None
        self.btn_template_photo = None
        self.lastMovedTo = None
        self.movingSelection = None
        self.inited = False
        return

    def open(self, view, nbk, treevw):
        self.nbk = nbk
        self.main_app_treevw = treevw
        if self.inited is False:
            self.initUI(view)
        self.refreshUI()
        return True


    def refreshUI(self):
        """
        Reload informations and reload them into the widgets
        """
        self.langs = APIClient.getInstance().getLangList()
        self.combo_lang.configure(values=self.langs)
        self.combo_lang.set(self.settings.db_settings.get("lang", "en"))
        self.langChange(None)
        self.reset()
        self.fillWithDefects()
        self.fillWithRemarks()
        return
        

    def initUI(self, parent):
        """
        Initialize window and widgets.
        """
        if self.inited:  # Already initialized
            self.reset()
            self.fillWithDefects()
            self.fillWithRemarks()
            return
        self.inited = True
        self.parent = parent
        ### MAIN PAGE FRAME ###
        self.reportFrame = CTkScrollableFrame(parent)
        self.image_add = CTkImage(Image.open(utils.getIcon("plus.png")))
        self.image_del = CTkImage(Image.open(utils.getIcon("delete.png")))
        self.image_edit = CTkImage(Image.open(utils.getIcon("stylo.png")))
        self.image_docs = CTkImage(Image.open(utils.getIcon("documents.png")))
        self.image_word = CTkImage(Image.open(utils.getIcon("word.png")))
        self.image_ppt = CTkImage(Image.open(utils.getIcon("ppt.png")))
        ### DEFECT TABLE ###
        self.rowHeight = 20
        self.style = ttk.Style()
        self.style.configure('Report.Treeview', rowheight=self.rowHeight)
        # REMARK TREEVW	
        self.remarksFrame = ttk.LabelFrame(self.reportFrame, text="Remarks table")	
        self.paned_remarks = tk.PanedWindow(self.remarksFrame, orient=tk.VERTICAL, height=900)	
        self.remarkframeTw = CTkFrame(self.paned_remarks)	
        frameButtonsRemark = CTkFrame(self.remarkframeTw)
        self.remarks_treevw = ttk.Treeview(self.remarkframeTw, style='Report.Treeview', height=0)	
        self.remarks_treevw["columns"] = ["Title", "Type"]	
        self.remarks_treevw.heading("#0", text='Title', anchor=tk.W)	
        self.remarks_treevw.column("#0", width=150, anchor=tk.W)	
        self.remarks_treevw.bind("<Delete>", self.deleteSelectedRemarkItem)	
        self.remarks_treevw.bind("<Double-Button-1>", self.OnRemarkDoubleClick)
        self.remarks_treevw.grid(row=0, column=0, sticky=tk.NSEW)	
        scbVSel = CTkScrollbar(self.remarkframeTw,	
                                orientation=tk.VERTICAL,	
                                command=self.remarks_treevw.yview)	
        self.remarks_treevw.configure(yscrollcommand=scbVSel.set)	
        scbVSel.grid(row=0, column=1, sticky=tk.NS)	
        self.remarkframeTw.columnconfigure(0, weight=1)	
        self.remarkframeTw.rowconfigure(0, weight=1)	
        self.remarkframeTw.pack(side=tk.TOP, fill=tk.BOTH, pady=5, expand=1, padx=5)	
        btn_addRemark = CTkButton(	
            frameButtonsRemark, text="Add remark", image=self.image_add, command=self.addRemarkCallback)	
        btn_addRemark.pack(side=tk.TOP, anchor=tk.CENTER, pady=5)	
        btn_delRemark = CTkButton(	
            frameButtonsRemark, text="Remove selection", image=self.image_del, command=self.deleteSelectedRemarkItem,
                                    fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")	
        btn_delRemark.pack(side=tk.TOP, anchor=tk.CENTER, pady=5)	
        frameButtonsRemark.grid(row=0, column=2, sticky=tk.W + tk.E)	
        frameAllBelow = CTkFrame(self.paned_remarks)	
            
        # DEFECT TREEVW	
        defectLabelFrame = ttk.LabelFrame(frameAllBelow, text="Defects table")	
        self.paned = tk.PanedWindow(defectLabelFrame, orient=tk.VERTICAL, height=800)

        self.frameTw = CTkFrame(self.paned)
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
            "Critical", background="black", foreground="gray97")
        self.treevw.tag_configure(
            "Major", background="red", foreground="gray97")
        self.treevw.tag_configure(
            "Important", background="orange", foreground="gray97")
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
        scbVSel = CTkScrollbar(self.frameTw,
                                orientation=tk.VERTICAL,
                                command=self.treevw.yview)
        self.treevw.configure(yscrollcommand=scbVSel.set)
        scbVSel.grid(row=0, column=1, sticky=tk.NS)
        self.frameTw.pack(side=tk.TOP, fill=tk.BOTH, padx=5, pady=10)
        self.frameTw.columnconfigure(0, weight=1)
        self.frameTw.rowconfigure(0, weight=1)
        ### OFFICE EXPORT FRAME ###
        belowFrame = CTkFrame(self.paned)
        frameBtn = CTkFrame(self.frameTw)
        #lbl_help = FormHelper("DefectHelper", "Use del to delete a defect, use Alt+Arrows to order them")
        #lbl_help.constructView(frameBtn)
        self.buttonUpImage = CTkImage(Image.open(utils.getIcon("up-arrow.png")))
        self.buttonDownImage = CTkImage(Image.open(utils.getIcon('down-arrow.png')))
        # use self.buttonPhoto
        frame_up_down = CTkFrame(frameBtn)
        btn_down = CTkButton(frame_up_down,  text = "", width=20, image=self.buttonDownImage, command=self.bDown)
        btn_down.pack(side="left", anchor="center")
        btn_up = CTkButton(frame_up_down, text = "",  width=20, image=self.buttonUpImage, command=self.bUp)
        btn_up.pack(side="left", anchor="center")
        frame_up_down.pack(side=tk.TOP, anchor=tk.CENTER)
        btn_delDefect = CTkButton(
            frameBtn, text="Remove selection", command=self.deleteSelectedItem, image=self.image_del, fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
        btn_delDefect.pack(side=tk.TOP, pady=5)
        btn_addDefect = CTkButton(
            frameBtn, text="Add defect", image=self.image_add, command=self.addDefectCallback)
        btn_addDefect.pack(side=tk.TOP, pady=5)
        btn_addDefect = CTkButton(
            frameBtn, text="Add Many defects", image=self.image_add, command=self.addManyDefectsCallback)
        btn_addDefect.pack(side=tk.TOP, pady=5)
        btn_setMainRedactor = CTkButton(
            frameBtn, text="Set main redactor", command=self.setMainRedactor, image=self.image_edit)
        btn_setMainRedactor.pack(side=tk.TOP, pady=5)
        btn_browseDefects = CTkButton(	
	            frameBtn, text="Browse defects templates", image=self.image_docs, command=self.browseDefectsCallback)	
        btn_browseDefects.pack(side=tk.TOP, pady=5)
        frameBtn.grid(row=0, column=2, sticky=tk.W + tk.E)
        officeFrame = ttk.LabelFrame(belowFrame, text=" Reports ")
        ### INFORMATION EXPORT FRAME ###
        informations_frame = CTkFrame(officeFrame)
        lbl_lang = CTkLabel(informations_frame, text="Lang")
        lbl_lang.grid(row=2, column=0, sticky=tk.E)
        self.combo_lang = CTkComboBox(informations_frame, values=self.langs, command=self.langChange)
        self.combo_lang.grid(row=2, column=1, sticky=tk.W)
        informations_frame.pack(side=tk.TOP, pady=10)
        ### WORD EXPORT FRAME ###
        templatesFrame = CTkFrame(officeFrame)
        lbl = CTkLabel(
            templatesFrame, text="Word template")
        lbl.grid(row=0, column=0, sticky=tk.E)
        self.combo_word = CTkComboBox(templatesFrame, values=self.docx_models, width=300)
        self.combo_word.grid(row=0, column=1)
        self.btn_template_photo = CTkImage(Image.open(utils.getIcon("download.png")))
        btn_word = CTkButton(
            templatesFrame, text="Generate", image=self.image_word, command=self.generateReportWord)
        btn_word.grid(row=0, column=2, sticky=tk.E, padx=5)
        btn_word_template_dl = CTkButton(templatesFrame, text="View empty template", width=40, image=self.btn_template_photo, command=self.downloadWordTemplate)
        btn_word_template_dl.grid(row=0, column=3, sticky=tk.W)
        
        ### POWERPOINT EXPORT FRAME ###
        lbl = CTkLabel(templatesFrame,
                        text="Powerpoint template")
        lbl.grid(row=1, column=0, sticky=tk.E, pady=20)
        self.combo_pptx = CTkComboBox(
            templatesFrame, values=self.pptx_models, width=300)
        self.combo_pptx.grid(row=1, column=1)
        
        btn_ppt = CTkButton(
            templatesFrame, text="Generate", image=self.image_ppt, command=self.generateReportPowerpoint)
        btn_ppt.grid(row=1, column=2, sticky=tk.E, padx=5)
        btn_pptx_template_dl = CTkButton(templatesFrame,text="View empty template",image=self.btn_template_photo,width=40, command=self.downloadPptxTemplate)
        btn_pptx_template_dl.grid(row=1, column=3, sticky=tk.W)
        templatesFrame.pack(side=tk.TOP,padx=10, pady=10, expand=1, anchor=tk.CENTER)
        officeFrame.pack(side=tk.TOP, fill=tk.BOTH, pady=10)
        belowFrame.pack(side=tk.TOP, fill=tk.BOTH)
        self.paned.add(self.frameTw, minsize=200)
        self.paned.add(belowFrame)
        self.paned.pack(fill=tk.BOTH, expand=1)
        defectLabelFrame.pack(side=tk.TOP, fill=tk.BOTH, pady=10)	
        frameAllBelow.pack(side=tk.TOP, fill=tk.BOTH)
        self.paned_remarks.add(self.remarkframeTw)	
        self.paned_remarks.add(frameAllBelow)	
        self.paned_remarks.pack(fill=tk.BOTH, expand=1)	
        self.remarksFrame.pack(side=tk.TOP, fill=tk.BOTH)
        self.reportFrame.pack(side=tk.TOP, fill=tk.BOTH, padx=10, pady=10, expand=1)
        

    def langChange(self, event=None):
        self.curr_lang = self.combo_lang.get()
        templates = APIClient.getInstance().getTemplateList(self.curr_lang)
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
            try:
                moving_item = tv.selection()[0]
            except IndexError:
                return # nothing selected
            moving_item = tv.item(moving_item)
            self.movingSelection = tv.identify_row(event.y)
            self.drag_toast = CTkLabel(self.parent, text=moving_item["text"])
            root = tv.winfo_toplevel()
            abs_coord_x = root.winfo_pointerx() - self.parent.winfo_rootx() + 10
            abs_coord_y = root.winfo_pointery() - self.parent.winfo_rooty() +3
            self.drag_toast.place(x=abs_coord_x,y=abs_coord_y)

    def dragRelease(self, event):
        if self.drag_toast is not None:
            self.drag_toast.destroy()
            self.drag_toast = None
        if self.movingSelection is None or self.lastMovedTo is None or self.lastMovedTo == "":
            return
        tv = event.widget
        apiclient = APIClient.getInstance()
        if tv.identify_row(event.y) in tv.get_children():
            apiclient.moveDefect(self.movingSelection, self.lastMovedTo)
            children = tv.get_children()
            iid_moving = children.index(self.lastMovedTo)
            tv.move(self.movingSelection, '', iid_moving)
            self.movingSelection = None
            self.lastMovedTo = None
            

    def dragMove(self, event):
        tv = event.widget
        rowToMove = tv.identify_row(event.y)
        moveto = tv.index(rowToMove)    
        self.lastMovedTo = rowToMove if rowToMove != self.movingSelection else self.lastMovedTo
        if self.drag_toast:
            root = tv.winfo_toplevel()
            abs_coord_x = root.winfo_pointerx() - self.parent.winfo_rootx() + 10
            abs_coord_y = root.winfo_pointery() - self.parent.winfo_rooty() +3
            self.drag_toast.place(x=abs_coord_x,y=abs_coord_y)
     

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
        try:
            selected = self.treevw.selection()[0]
        except IndexError:
            return
        self.removeItem(selected)

    def deleteSelectedRemarkItem(self, _event=None):	
        """	
        Remove selected remark from treeview	
        Args:	
            _event: not used but mandatory	
        """	
        selected = self.remarks_treevw.selection()[0]	
        self.remarks_treevw.delete(selected)	
        remark = Remark.fetchObject({"_id":ObjectId(selected)})	
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
        defectToDelete = Defect.fetchObject({"title": item["text"], "target_id":""})
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
        dialog = ChildDialogDefectView(self.tkApp, "Add a security defect", self.settings)
        try:
            self.tkApp.wait_window(dialog.app)	
        except tk.TclError:
            pass

    def browseDefectsCallback(self):	
        """Open an view to browse defects Templates"""	
        dialog = ChildDialogDefectView(self.tkApp, "Browse defect templates", self.settings, Defect(), True)	
        try:
            self.tkApp.wait_window(dialog.app)	
        except tk.TclError:
            pass

    def addManyDefectsCallback(self):
        """Open an multiview insert defect view form in a child window"""	
        dialog = ChildDialogDefectView(self.tkApp, "Add and edit multiple defect", self.settings, None, True)	
        try:
            self.tkApp.wait_window(dialog.app)	
        except tk.TclError:
            pass
		
    def addRemarkCallback(self):	
        """Open an insert defect view form in a child window"""	
        dialog = ChildDialogRemarkView(self.parent)

    def setMainRedactor(self):
        """Sets a main redactor for a pentest. Each not assigned defect will be assigned to him/her"""
        self.settings.reloadSettings()
        dialog = ChildDialogCombo(self.parent, self.settings.getPentesters()+["N/A"], "Set main redactor", "N/A")
        self.parent.wait_window(dialog.app)
        newVal = dialog.rvalue
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
        if defect_m.isAssigned():
            return ""
        try:
            exist = self.treevw.item(defect_m.getId())
        except:
            self.addDefect(defect_m)
            return
        try:
            columnEase = self.treevw['columns'].index("ease")
            columnImpact = self.treevw['columns'].index("impact")
            columnRisk = self.treevw['columns'].index("risk")
            columnType = self.treevw['columns'].index("type")
            columnRedactor = self.treevw['columns'].index("redactor")
        except :
            return
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
        #if self.movingSelection is None:
        self.treevw.move(defect_m.getId(), '', int(defect_m.index))

    def updateRemarkInTreevw(self, remark_m):
        """
        Change values of a selected remark in the treeview
        Args:
            remark_m: a remark model with updated values
        """
        try:
            exist = self.remarks_treevw.item(remark_m.getId())
        except:
            self.addRemark(remark_m)
            return
        self.remarks_treevw.item(remark_m.getId(), text=remark_m.title, values=[remark_m.type], image=RemarkView.getIcon(remark_m.type))

    def OnRemarkDoubleClick(self, event):
        """Callback for double click on remark treeview. Opens a window to update the double clicked remark view.
        """
        item = self.remarks_treevw.identify("item", event.x, event.y)
        if item is None or item == '':
            return
        remark_m = Remark.fetchObject({"_id": ObjectId(item)})
        dialog = ChildDialogRemarkView(self.tkApp,  remark_m)
        self.parent.wait_window(dialog.app)
        self.updateRemarkInTreevw(remark_m)
      
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
        dialog = ChildDialogDefectView(self.tkApp, "Edit defect", self.settings, defect_m)
        self.updateDefectInTreevw(defect_m)

    def fillWithDefects(self):
        """
        Fetch defects that are global (not assigned to an ip) and fill the defect table with them.
        """
        table = Defect.getDefectTable()
        for line in table:
            self.addDefect(Defect(line))

    def fillWithRemarks(self):	
        """	
        Fetch remarks and fill the remarks table with them.	
        """	
        self.reset_remarks()
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
                already_inserted = True
                break	
        if not already_inserted:	
            try:	
                self.remarks_treevw.insert('', 'end', str(remark_o.getId()), values = (remark_o.type), text=remark_o.title, image=RemarkView.getIcon(remark_o.type))	
            except tk.TclError:	
                # The defect already exists	
                self.remarks_treevw.item(str(remark_o.getId()), values = (remark_o.type), text=remark_o.title, image=RemarkView.getIcon(remark_o.type))
            
        self.resizeRemarkTreeview()	
                    
	
	
    def addDefect(self, defect_o):
        """
        Add the given defect object in the treeview
        Args:
            defect_o: a Models.Defect object to be inserted in treeview
        """
        if defect_o is None:
            return
        if not self.inited:
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
                self.treevw.insert('', int(indToInsert), defect_o.getId(), text=defect_o.title,
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
            self.treevw.configure(height=currentHeight)
            sx, sy = self.paned.sash_coord(0)
            if sy <= (currentHeight)*self.rowHeight + self.pane_base_height:
                self.paned.paneconfigure(self.frameTw, height=(currentHeight)*self.rowHeight + self.pane_base_height)
    
    def resizeRemarkTreeview(self):	
        currentHeight = len(self.remarks_treevw.get_children())	
        if currentHeight <= 5:	
            self.remarks_treevw.configure(height=currentHeight)	
            sx, sy = self.paned_remarks.sash_coord(0)	
            if sy <= (currentHeight)*self.rowHeight + self.pane_base_height:	
                self.paned_remarks.paneconfigure(self.remarkframeTw, height=(currentHeight)*self.rowHeight + self.pane_base_height)

    def generateReportPowerpoint(self):
        apiclient = APIClient.getInstance()
        toExport = apiclient.getCurrentPentest()
        if toExport != "":
            modele_pptx = str(self.combo_pptx.get())
            dialog = ChildDialogInfo(
                self.parent, "PowerPoint Report", "Creating report . Please wait.")
            dialog.show()
            x = threading.Thread(target=generateReport, args=(self.tkApp, dialog, modele_pptx, self.mainRedac, self.curr_lang))
            x.start()

    def generateReportWord(self):
        """
        Export a pentest defects to a word formatted file.
        """
        
        apiclient = APIClient.getInstance()
        toExport = apiclient.getCurrentPentest()
        if toExport != "":
            modele_docx = str(self.combo_word.get())
            dialog = ChildDialogInfo(
                self.parent, "Word Report", "Creating report . Please wait.")
            dialog.show()
            x = threading.Thread(target=generateReport, args=(self.tkApp, dialog, modele_docx,  self.mainRedac, self.curr_lang))
            x.start()
            

    def downloadWordTemplate(self):
        self._download_and_open_template(self.combo_word.get())

    def downloadPptxTemplate(self):
        self._download_and_open_template(self.combo_pptx.get())

    def _download_and_open_template(self, templateName):
        apiclient = APIClient.getInstance()
        path = apiclient.downloadTemplate(self, self.curr_lang, templateName)
        dialog = ChildDialogQuestion(self.parent,
                                    "Template downloaded", "Template was downloaded here : "+str(path)+". Do you you want to open it ?", ["Open", "Cancel"])
        self.parent.wait_window(dialog.app)
        if dialog.rvalue != "Open":
            return
        utils.openPathForUser(path, folder_only=True)

    def update_received(self, dataManager, notif, obj, old_obj):
        if notif["collection"] == "remarks":
            obj = Remark.fetchObject({"_id":notif["iid"]})
        if obj is None:
            return
        
        if notif["action"] == "delete":
            if notif["collection"] == "remarks":
                self.deleteRemarkInTreevw(obj)
            elif notif["collection"] == "defects":
                self.deleteDefectInTreevw(obj)
            return
        # insert ou update
        if notif["collection"] == "remarks":
            logger.debug("Received remark notification : "+str(notif))
            self.addRemark(obj)
        elif notif["collection"] == "defects":
            self.updateDefectInTreevw(obj)
      
        


def generateReport(tkApp, dialog, modele, mainRedac, curr_lang):
    apiclient = APIClient.getInstance()
    settings = Settings()
    settings._reloadDbSettings()
    additional_context = {}
    for module in tkApp.modules:
        if callable(getattr(module["object"], "onGenerateReport", None)):
                result = module["object"].onGenerateReport()
                if result.get("additional_context") is not None:
                    additional_context = {**result.get("additional_context", {}), **additional_context}
    res, msg = apiclient.generateReport(modele, settings.getClientName(), settings.getMissionName(), mainRedac, curr_lang, additional_context)
    dialog.destroy()
    if not res:
        tkinter.messagebox.showerror(
            "Failure", str(msg))
    else:
        tkinter.messagebox.showinfo(
            "Success", "The document was generated in "+str(msg))
        utils.openPathForUser(msg, folder_only=True)
        