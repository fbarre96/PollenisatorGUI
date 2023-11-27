"""StatusBar class. Show tagged elements numbers to user.
"""
import tkinter as tk
from tkinter import ttk
from customtkinter import *
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.components.tag import TagInfos

class StatusBar(CTkFrame):
    """StatusBar class. Show tagged numbers to user.
    Inherits CTkFrame
    """

    def tagClicked(self, name):
        """A lambda to callback with the tag name clicked
        Args:
            name: the tag name clicked
        """
        return lambda _event: self.statusbarClickedCallback(name)

    def __init__(self, master, statusbarClickedCallback):
        """
        Constructor of the status bar
        Args:
            master: parent tkinter window
            statusbarController: a controller to handle clicks on status bar.
                                It has to delcare a statusbarClicked function taking 1 arg : a tag name
        """
        # Cannot be imported at module level as tkinter will not have loaded.
        super().__init__(master, fg_color="transparent")
        # label = CTkLabel(self, text="Tagged")
        # label.pack(side="left")
        self.registeredTags = []
        self.statusbarClickedCallback = statusbarClickedCallback
        self.tagsCount = {}
        self.labelsTags = {}
        self.font = CTkFont("roboto", 11)
        DataManager.getInstance().attach(self)

    def refreshUI(self):
        for widget in self.winfo_children():
            widget.destroy()
        #self.pack_forget()
        lbl = CTkLabel(self, text="Filter by tags")
        lbl.pack(side="left", padx=1)

        self.registeredTags = Settings.getTags(ignoreCache=True)
        column = 1
        keys = list(self.registeredTags.keys())
        self.listOfLambdas = [self.tagClicked(keys[i]) for i in range(len(keys))]
        datamanager = DataManager.getInstance()
        tags = datamanager.get("tags", "*")
        for tag_obj in tags:
            for tag_info in tag_obj.tags:
                tag = TagInfos(tag_info)
                tag_name = tag.name
                self.tagsCount[str(tag_name)] = self.tagsCount.get(str(tag_name), 0) + 1
        for registeredTag, tag_info in self.registeredTags.items():
            self.tagsCount[registeredTag] = self.tagsCount.get(registeredTag, 0)
            color = tag_info["color"]
            try:
                if color == "transparent":
                    color = "white"
                self.labelsTags[registeredTag] = CTkLabel(self,  text=registeredTag+" : "+str(self.tagsCount[registeredTag]), fg_color=color, text_color="black",height=10, width=0, corner_radius=20,font=self.font)
            except tk.TclError:
                #color does not exist
                color = "gray97"
                self.labelsTags[registeredTag] = CTkLabel(self,text=registeredTag+" : "+str(self.tagsCount[registeredTag]),  fg_color=color, text_color="black",height=10, width=0,  corner_radius=20,font=self.font)
            self.labelsTags[registeredTag].pack(side="left", padx=1)
            self.labelsTags[registeredTag].bind('<Button-1>', self.listOfLambdas[column-1])
            column += 1

    def notify(self, addedTags, removedTags=[]):
        """
        Notify is called when tags are added or removed
        Args:
            addedTags: a list of tag names added
            removedTags: a list of tag names removed, default to []
        """
        updated = False
        if not "hidden" in addedTags:
            for tag in addedTags:
                tag = TagInfos(tag)
                if tag.name in self.tagsCount:
                    self.tagsCount[tag.name] += 1
                    updated = True
        for tag in removedTags:
            tag = TagInfos(tag)
            if tag.name in self.tagsCount:
                self.tagsCount[tag.name] -= 1
                updated = True
        if updated:
            self._update()
    

    def reset(self):
        """
        Rest all displayed tags count to 0
        """
        for registeredTag in self.registeredTags:
            self.tagsCount[registeredTag] = 0
        self._update()

    def _update(self):
        """
        Update all tags label to tags count
        """
        try:
            for tag, label in self.labelsTags.items():
                label.configure(text=tag+" : "+str(self.tagsCount.get(tag, 0)))
                label.update_idletasks()
        except Exception:
            pass

    def update_received(self, dataManager, notification, obj, old_obj):
        """
        Update the status bar when a tag is added or removed
        Args:
            dataManager: the DataManager instance
            notification: the notification type
            obj: the object that has been added or removed
        """
        if notification["collection"] == "settings":
            self.after(2000, self.refreshUI)
        if notification["collection"] == "tags":
            if old_obj is not None and obj is not None:
                if old_obj.tags != obj.tags:
                    self.notify(obj.tags, old_obj.tags)
    

    def refreshTags(self, tags):
        self.registeredTags = tags
        self.refreshUI()

