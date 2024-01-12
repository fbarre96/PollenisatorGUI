"""View for remark object. Handle node in treeview and present forms to user when interacted with."""

from tkinter import TclError
import tkinter as tk
from pollenisatorgui.core.views.viewelement import ViewElement
from pollenisatorgui.core.models.remark import Remark
from pollenisatorgui.core.components.apiclient import APIClient
import pollenisatorgui.core.components.utils as utils
from shutil import which
import os
import sys
import subprocess



class RemarkView(ViewElement):
    """View for remark object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory.
    """

    icon = 'defects.png'

    cached_icons =  {}

    @classmethod
    def getIconName(cls, typeOfRemark):
        return "remark_"+typeOfRemark.lower()+".png"

    @classmethod
    def getIcon(cls, typeOfRemark):
        """
        Load the object icon in cache if it is not yet done, and returns it

        Return:
            Returns the icon representing this object.
        """
        cache = cls.cached_icons.get(typeOfRemark, None)

        if cache is None:
            from PIL import Image, ImageTk
            path = utils.getIcon(cls.getIconName(typeOfRemark))
            cls.cached_icons[typeOfRemark] = ImageTk.PhotoImage(Image.open(path))
            return cls.cached_icons[typeOfRemark]
        return cache

    def __init__(self, appViewFrame, controller):
        """Constructor
        Args:
            controller: a CommandController for this view.
        """
        super().__init__(None, appViewFrame, None, controller)
        self.comboTypeForm = None
        self.imgTypeForm = None

    def searchCallback(self, searchreq, **options):
        remarks_obj, remarks_errors = APIClient.getInstance().searchRemark(searchreq, **options)
        if remarks_obj:
            for i, remark in enumerate(remarks_obj):
                remarks_obj[i]["TITLE"] = remark["title"]
        return remarks_obj, remarks_errors
    
    def openInsertWindow(self,  **kwargs):
        """
        Creates a tkinter form using Forms classes. This form aims to insert a new Remark
        Args:
            addButtons: boolean value indicating that insertion buttons should be visible. Default to True
        """
        modelData = self.controller.getData()
        
        search_panel = self.form.addFormPanel(grid=True, side="left", pady=0, padx=0)
        type_combo_search = search_panel.addFormPanel(grid=True, row=0, column=0)
        type_combo_search.addFormLabel("Type for search",  row=0, column=0)
        type_search = type_combo_search.addFormCombo("Search only", ["<Empty>", "Positive","Neutral","Negative"], row=0, column=1)
        s = search_panel.addFormSearchBar("Search Remark", self.searchCallback, None, row=1)
        s.addOptionForm(type_search, "remark_type")
        
        topPanel = self.form.addFormPanel(grid=True, side="right")
        head = topPanel.addFormPanel(grid=True, row=0)
        self.imgTypeForm = head.addFormImage(utils.getIcon(RemarkView.getIconName(modelData["type"])))
        self.comboTypeForm = head.addFormCombo("Type", ["Positive","Neutral","Negative"], command=self.updateImage, column=1, default=modelData["type"], binds={"<<ComboboxSelected>>": self.updateImage, "<<FormUpdated>>": self.updateImage})
        self.comboTypeForm.configure(command=self.updateImage)
        head.addFormStr("Title", r".+", "", column=2, placeholder_text="Title")
        bot = topPanel.addFormPanel(grid=True,row=1)
        bot.addFormText("Description", r".+", "description")
        s.panel_to_fill = topPanel
        if kwargs.get("addButtons", True):
            self.completeInsertWindow()
        else:
            self.showForm()

    def openModifyWindow(self, **kwargs):
        """
        Creates a tkinter form using Forms classes.
        This form aims to update or delete an existing Defect
        Args:
            addButtons: boolean value indicating that insertion buttons should be visible. Default to True
        """
        self.form.clear()
        modelData = self.controller.getData()
        search_panel = self.form.addFormPanel(grid=True, side="left", pady=0, padx=0)
        type_combo_search = search_panel.addFormPanel(grid=True, row=0, column=0)
        type_combo_search.addFormLabel("Type for search",  row=0, column=0)
        type_search = type_combo_search.addFormCombo("Search only", ["<Empty>", "Positive","Neutral","Negative"], row=0, column=1)
        s = search_panel.addFormSearchBar("Search Remark", self.searchCallback, self.form, row=1)

        topPanel = self.form.addFormPanel(grid=True, side="right")
        self.imgTypeForm = topPanel.addFormImage(utils.getIcon(RemarkView.getIconName(modelData["type"])))
        self.comboTypeForm = topPanel.addFormCombo("Type", ["Positive","Neutral","Negative"], column=1, default=modelData["type"],command=self.updateImage, binds={"<<ComboboxSelected>>": self.updateImage, "<<FormUpdated>>": self.updateImage})
        self.comboTypeForm.configure(command=self.updateImage)
        s.addOptionForm(type_search, "remark_type")
        topPanel.addFormStr(
            "Title", r".+", modelData["title"], column=2)
        topPanel.addFormText("Description", r".+", modelData["description"], row=2,column=2)
        if kwargs.get("addButtons", True):
            self.completeModifyWindow()
        else:
            self.showForm()

    def updateImage(self, _event=None):
        """Callback when ease or impact is modified.
        Calculate new resulting risk value
        Args
            _event: mandatory but not used
        """
        typeof = self.comboTypeForm.getValue()
        self.imgTypeForm.setImage(utils.getIcon(RemarkView.getIconName(typeof)))


    