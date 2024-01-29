"""Shared notes module"""
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.modules.module import Module
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.application.mdframe import TkintermdFrame
import threading
from difflib import Differ


class SharedNotes(Module):
    """
    Shared notes tab. 
    """
    iconName = "notes.png"
    tabName = "Notes"
    coll_name = "documents"

    order_priority = Module.MEDIUM_PRIORITY
    
    def __init__(self, parent, settings, tkApp):
        """
        Constructor
        """
        super().__init__()
        self.parent = None
        self.tkApp = tkApp
        self.inited = False
        self.settings = settings

    def open(self, view, nbk, treevw):
        apiclient = APIClient.getInstance()
        self.treevw = treevw
        if not self.inited:
            self.initUI(view)
        if apiclient.getCurrentPentest() is not None:
            self.refreshUI()
        self.timer = None
        @self.tkApp.sio.on("load-document")
        def load_document(document):
            self.setText(document)
            self.save_document()
        apiclient = APIClient.getInstance()
        pentest = apiclient.getCurrentPentest()
        self.tkApp.sio.emit("get-document", {"doc_id":pentest, "pentest":pentest})
        @self.tkApp.sio.on("received-delta")
        def handler(self, delta):
            print(delta)

    def refreshUI(self):
        """
        Reload data and display them
        """
        pass

    def setText(self, text):
        self.mdFrame.text_area.delete(1.0, tk.END)
        if isinstance(text, dict) and len(text) == 0:
            text = ""
        self.mdFrame.text_area.insert(tk.INSERT, text)
 
    def initUI(self, parent):
        """
        Initialize Dashboard widgets
        Args:
            parent: its parent widget
        """
        self.inited = True
        self.parent = parent
       
        dark_mode = self.settings.is_dark_mode()
        self.mdFrame = TkintermdFrame(parent, default_text="", tkApp=self.tkApp, just_editor=False, style_change=False, enable_preview=True)
        if dark_mode:
            self.mdFrame.load_style("material")
        else:
            self.mdFrame.load_style("stata-dark")
        self.sv = StringVar()
        self.mdFrame.text_area.bind("<<KeyRelease>>", self.on_input_change)

        self.mdFrame.pack(fill="both", expand=1)
        parent.pack(fill="both", expand=1)
        #self.moduleFrame.pack(padx=10, pady=10, side=tk.TOP, fill=tk.BOTH, expand=True)


    def on_input_change(self, event):
        old_text = self.sv.get()
        new_text = self.mdFrame.text_area.get("1.0", END)
        difference = []
        for d in Differ().compare(old_text, new_text):
            difference.append(d)
        self.sv.set(new_text)
        self.tkApp.sio.emit("send-delta", difference)

    def save_document(self):
        # tell to the main thread to save the document
        try:
            self.tkApp.after(0, self.do_save_document)
        except RuntimeError:
            return
        self.timer = threading.Timer(0.2, self.save_document)
        self.timer.start()

    def do_save_document(self):
        self.tkApp.sio.emit("save-document", self.mdFrame.text_area.get(1.0, tk.END))

    def close(self):
        self.tkApp.sio.on("received-delta",  )
        self.timer.cancel()