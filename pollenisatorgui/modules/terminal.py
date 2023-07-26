# import os
# import tkinter as tk
# import tkinter.ttk as ttk
# from customtkinter import *
# from multiprocessing import Manager
# import pollenisatorgui.core.components.utils as utils
# from PIL import Image, ImageTk
# from pollenisatorgui.core.views.checkinstanceview import CheckInstanceView
# from pollenisatorgui.core.views.waveview import WaveView
# from pollenisatorgui.core.views.ipview import IpView
# from pollenisatorgui.core.views.portview import PortView
# from pollenisatorgui.core.views.scopeview import ScopeView
# from pollenisatorgui.modules.module import Module

# class Terminal(Module):
#     iconName = "tab_terminal.png"
#     tabName = "   Terminal  "
#     order_priority = Module.LOW_PRIORITY
#     settings = None

#     def __init__(self, parent, settings):
#         super().__init__()
#         self.proc = None
#         self.s = None
#         self.__class__.settings = settings
#         self.img = CTkImage(Image.open(utils.getIcon("help.png")))
#         manager = Manager()
#         self.exiting = manager.Value('i', 0)

#     def initUI(self, parent, nbk, treevw, tkApp):
#         self.treevw = treevw
#         if self.__class__.settings.isTrapCommand():
#             settings_text = "Setting trap command is ON\nEvery command typed here will be executed through pollenisator and will be logged / imported depending on the tools called.\nYou can disable the trap setting in the Settings to change this behaviour."
#         else:
#             settings_text = "Setting trap command is OFF\ntype 'pollex <YOUR COMMAND with --args>' to execute it through pollenisator\n(plugins will autocomplete the output file and import it once done).\n You can enable the trap setting in the Settings to auto-import each commands without prepending pollex."
#         frame = CTkFrame(parent)
#         s = ttk.Style()
#         s.configure('big.TLabel', font=('Helvetica', 12), background="gray97")
#         lbl = CTkLabel(frame,text="", image=self.img)
#         lbl.pack(anchor=tk.CENTER, side=tk.LEFT)
#         lbl = CTkLabel(frame, text=settings_text)
#         lbl.pack(anchor=tk.CENTER, side=tk.RIGHT)
#         frame.place(relx=.5, rely=.5, anchor="c")
#         return

#     def open(self):
#         self.__class__.openTerminal()
#         return True

#     @classmethod
#     def openTerminal(cls, default_target=None):
        
            
#         if cls.settings.isTrapCommand():
#             comm = "bash --rcfile "+os.path.join(utils.getMainDir(), "setupTerminalForPentest.sh")
#         else:
#             comm = "bash"
        
#         res = utils.executeInExternalTerm(comm, with_bash=False,  default_target=default_target)
        

#     def onClosing(self, _signum=None, _frame=None):
#         #self.exiting.value = 1
#         if self.s:
#             self.s.close()

#     def _initContextualsMenus(self, parentFrame):
#         """
#         Create a contextual menu
#         """
#         self.contextualMenu = utils.craftMenuWithStyle(parentFrame)
#         self.contextualMenu.add_command(
#             label="Attack from terminal", command=self.attackFromTerminal)
#         return self.contextualMenu

#     def attackFromTerminal(self, _event=None):
#         for selected in self.treevw.selection():
#             view_o = self.treevw.getViewFromId(selected)
#             if view_o is not None:
#                 if isinstance(view_o, CheckInstanceView):
#                     Terminal.openTerminal(view_o.controller.getDbId())
#                 else:
#                     lvl = "network" if isinstance(view_o, ScopeView) else None
#                     lvl = "wave" if isinstance(view_o, WaveView) else lvl
#                     lvl = "ip" if isinstance(view_o, IpView) else lvl
#                     lvl = "port" if isinstance(view_o, PortView) else lvl
                    
                    
#                     if lvl is not None:
#                         inst = view_o.controller.getData()
#                         Terminal.openTerminal(lvl+"|"+inst.get("wave", "Imported")+"|"+inst.get(
#                             "scope", "")+"|"+inst.get("ip", "")+"|"+inst.get("port", "")+"|"+inst.get("proto", ""))
#                     else:
#                         tk.messagebox.showerror(
#                             "ERROR : Wrong selection", "You have to select a object that may have tools")
