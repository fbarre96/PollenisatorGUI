# """Shared notes module"""
# import tkinter as tk
# import tkinter.ttk as ttk
# from customtkinter import *
# from pollenisatorgui.core.components.apiclient import APIClient
# from pollenisatorgui.modules.module import Module
# from pollenisatorgui.core.components.settings import Settings
# from tkintermd.frame import TkintermdFrame
# import threading
# from difflib import Differ


# class SharedNotes(Module):
#     """
#     Shared notes tab. 
#     """
#     iconName = "notes.png"
#     tabName = "Notes"
#     collName = "documents"

#     order_priority = Module.MEDIUM_PRIORITY
    
#     def __init__(self, parent, settings):
#         """
#         Constructor
#         """
#         super().__init__()
#         self.parent = None
#         self.settings = settings

#     def open(self):
#         apiclient = APIClient.getInstance()
#         if apiclient.getCurrentPentest() is not None:
#             self.refreshUI()
#         return True

#     def refreshUI(self):
#         """
#         Reload data and display them
#         """
#         pass

#     def setText(self, text):
#         self.mdFrame.text_area.delete(1.0, tk.END)
#         self.mdFrame.text_area.insert(tk.INSERT, text)
 
#     def initUI(self, parent, nbk, treevw, tkApp):
#         """
#         Initialize Dashboard widgets
#         Args:
#             parent: its parent widget
#         """
#         if self.parent is not None:  # Already initialized
#             return
#         self.parent = parent
#         self.tkApp = tkApp
#         self.moduleFrame = CTkFrame(parent)

       
#         dark_mode = self.settings.is_dark_mode()
#         self.mdFrame = TkintermdFrame(parent, default_text="", just_editor=False, style_change=False, enable_preview=True)
#         if dark_mode:
#             self.mdFrame.load_style("material")
#         else:
#             self.mdFrame.load_style("stata")
#         self.sv = StringVar()
#         self.mdFrame.text_area.bind("<<KeyRelease>>", self.on_input_change)

#         self.mdFrame.pack(fill="both", expand=1)
#         self.moduleFrame.pack(padx=10, pady=10, side="top", fill=tk.BOTH, expand=True)
        
#     def open(self):
#         self.timer = None
#         @self.tkApp.sio.on("load-document")
#         def load_document(document):
#             self.setText(document)
#             self.save_document()
#         apiclient = APIClient.getInstance()
#         pentest = apiclient.getCurrentPentest()
#         self.tkApp.sio.emit("get-document", {"doc_id":pentest, "pentest":pentest})
#         @self.tkApp.sio.on("received-delta")
#         def handler(self, delta):
#             print(delta)

#     def on_input_change(self, event):
#         old_text = self.sv.get()
#         new_text = self.mdFrame.text_area.get("1.0", END)
#         difference = []
#         for d in Differ().compare(old_text, new_text):
#             difference.append(d)
#         self.sv.set(new_text)
#         self.tkApp.sio.emit("send-delta", difference)

#     def save_document(self):
#         self.tkApp.sio.emit("save-document", self.mdFrame.text_area.get(1.0, tk.END))
#         self.timer = threading.Timer(0.2, self.save_document)
#         self.timer.start()

#     def close(self):
#         self.tkApp.sio.on("received-delta",  )
#         self.timer.cancel()