"""View for remark object. Handle node in treeview and present forms to user when interacted with."""

from tkinter import TclError
import tkinter as tk
from pollenisatorgui.core.Views.ViewElement import ViewElement
from pollenisatorgui.core.Models.Remark import Remark
from pollenisatorgui.core.Components.apiclient import APIClient
import pollenisatorgui.core.Components.Utils as Utils
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
            path = Utils.getIconDir() + cls.getIconName(typeOfRemark)
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

    def openInsertWindow(self,  addButtons=True):
        """
        Creates a tkinter form using Forms classes. This form aims to insert a new Remark
        Args:
            addButtons: boolean value indicating that insertion buttons should be visible. Default to True
        """
        modelData = self.controller.getData()
        self.form.addFormSearchBar("Search Remark", APIClient.searchRemark, self.form)
        topPanel = self.form.addFormPanel(grid=True)
        self.imgTypeForm = topPanel.addFormImage(Utils.getIconDir()+RemarkView.getIconName(modelData["type"]))
        self.comboTypeForm = topPanel.addFormCombo("Type", ["Positive","Neutral","Negative"], column=1, default=modelData["type"], binds={"<<ComboboxSelected>>": self.updateImage, "<<FormUpdated>>": self.updateImage})
        topPanel.addFormStr("Title", r".+", "", column=2, width=50)
        if addButtons:
            self.completeInsertWindow()
        else:
            self.showForm()

    def openModifyWindow(self, addButtons=True):
        """
        Creates a tkinter form using Forms classes.
        This form aims to update or delete an existing Defect
        Args:
            addButtons: boolean value indicating that insertion buttons should be visible. Default to True
        """
        modelData = self.controller.getData()
        topPanel = self.form.addFormPanel(grid=True)
        topPanel.addFormSearchBar("Search Remark", APIClient.searchRemark, topPanel, row=0, column=1, autofocus=False)
        self.imgTypeForm = topPanel.addFormImage(Utils.getIconDir()+RemarkView.getIconName(modelData["type"]), row=1)
        self.comboTypeForm = topPanel.addFormCombo("Type", ["Positive","Neutral","Negative"], column=1, row=1, default=modelData["type"], binds={"<<ComboboxSelected>>": self.updateImage})
        topPanel.addFormStr(
            "Title", r".+", modelData["title"], width=50, row=1, column=2)
        if addButtons:
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
        self.imgTypeForm.setImage(Utils.getIconDir()+RemarkView.getIconName(typeof))


    