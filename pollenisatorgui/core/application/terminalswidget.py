import multiprocessing
import os
import pty
import select
import shutil
import signal
import subprocess
import time
import tkinter as tk
from tkinter import ttk
from customtkinter import *
import libtmux
from pollenisatorgui.core.application.pseudotermframe import PseudoTermFrame
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.components.utils import getMainDir, getIcon, craftMenuWithStyle, read_and_forward_pty_output
from pollenisatorgui.core.components.logger_config import logger
from PIL import Image, ImageTk



# def read_and_forward_pty_output(fd, queue=None, queueResponse=None):
#     max_read_bytes = 1024 * 20
#     try:
#         while True:
#             time.sleep(0.01)
#             if fd:
#                 timeout_sec = 0
#                 (data_ready, _, _) = select.select([fd], [], [], timeout_sec)
#                 if not queue.empty():
#                     command = queue.get()
#                     os.write(fd, command.encode())
#                 if data_ready:
#                     output = os.read(fd, max_read_bytes).decode(
#                         errors="ignore"
#                     )
#                     queueResponse.put(output.replace("\r",""))
#     except Exception as e:
#         pass

def killThisProc(proc):
    try:
        logger.error("TERMINAL : Killing process terminal")
        time.sleep(1) # HACK to avoid xterm crash ✨ black magic ✨
        os.kill(proc.pid, signal.SIGTERM)
        
    except Exception as e:
        pass

class TerminalsWidget(CTkFrame):
    cachedClassIcon = None
    cachedPseudoTerminalClassIcon = None
    icon = "terminal_small.png"
    iconPseudoTerminal = "pseudo_terminal.png"
    def __init__(self, parent,  mainApp, **kwargs):
        super().__init__(parent,  **kwargs)
        self.parent = parent
        
        self.child_pid = None
        self.pseudoTermFrames = {}
        self.terminalFrames = {}
        self.proc = None
        self.fd = None
        self.mainApp = mainApp
        self.mainApp.subscribe_notification("notif_terminal", self.notif_terminal)
        self.inited = False
        self.opened = None
        self.initUI()

    def initUI(self):
        self.panedwindow = tk.PanedWindow(self, orient=tk.HORIZONTAL, height=200) 
        s = ttk.Style()
        s.configure('Terminal.Treeview.Item', indicatorsize=0)
        self.terminalTv = ttk.Treeview(self.panedwindow, show="tree", selectmode="browse", style="Terminal.Treeview")
        self.contextualMenu = craftMenuWithStyle(self.parent)
        self.contextualMenu.add_command(
            label="Close term", command=self.closeTerm)
        self.contextualMenu.add_command(
            label="Close done terms", command=self.closeDoneTerms)
        self.contextualMenu.add_command(
            label="Close all terms", command=self.closeAllTerms)
        self.contextualMenu.add_command(
            label="(Exit)", command= lambda: 0)# do nothing
        self.terminalTv.bind("<Button-3>", self.doPopup)
        self.terminalTv.column('#0', minwidth=50, width=80, stretch=tk.YES)
        self.proxyFrame = tk.Frame(self)
        self.pseudoTerminalFrame = tk.Frame(self.proxyFrame)
        self.terminalFrame = tk.Frame(self.proxyFrame)
        self.terminalFrame.pack(fill=tk.BOTH, expand=True)
        self.proxyFrame.pack(fill=tk.BOTH, expand=True)
        self.terminalTv.pack(fill=tk.Y, expand=True, padx=0,ipadx=0)
        self.terminalTv.bind("<<TreeviewSelect>>", self.onTreeviewSelect)
        self.terminalTv.tag_configure("notified", background="red")
        self.panedwindow.add(self.terminalTv)
        self.panedwindow.add(self.proxyFrame)
        self.panedwindow.pack(fill=tk.BOTH, expand=True)

    

    def doPopup(self, event):
        """Open the popup 
        Args:
            event: filled with the callback, contains data about line clicked
        """
        self.contextualMenu.selection = self.terminalTv.identify(
            "item", event.x, event.y)
        # display the popup menu
        try:
            self.contextualMenu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            print(e)
        finally:
            # make sure to release the grab (Tk 8.0a1 only)
            self.contextualMenu.grab_release()
        self.contextualMenu.focus_set()
        self.contextualMenu.bind('<FocusOut>', self.popupFocusOut)

    def popupFocusOut(self, _event=None):
        """Called when the contextual menu loses focus. Closes it.
        Args:
            _event: default to None
        """
        self.contextualMenu.unpost()
    
    def onTreeviewSelect(self, event=None):
        selection = self.terminalTv.selection()
        if len(selection) == 1:
            try:
                tags = self.terminalTv.item(str(selection[0]))["tags"]
                if "notified" in tags:
                    self.terminalTv.item(str(selection[0]), tags="notified-read")
            except tk.TclError:
                pass
            self.view_window(str(selection[0]))

    def update_size(self, event=None):
        xterm_width = self.terminalFrame.winfo_width()
        xterm_height = self.terminalFrame.winfo_height()
        if self.child_pid is not None:
            #HACK: only way I could find to resize the window is xdotool.
            xdotool_command = f"xdotool search --class popoxterm windowsize $(xdotool search --class popoxterm) {xterm_width} {xterm_height}"
            subprocess.call(xdotool_command, shell=True)

    def onClosing(self, _signum=None, _frame=None):
        if self.child_pid is not None:
            os.kill(self.child_pid, signal.SIGTERM)
        self.inited = False
        self.terminalTv.delete(*self.terminalTv.get_children())

    @classmethod
    def getIcon(cls):
        if cls.cachedClassIcon is None:
            path = getIcon(cls.icon)
            img = Image.open(path)
            cls.cachedClassIcon = ImageTk.PhotoImage(img)
        return cls.cachedClassIcon
    
    @classmethod
    def getPseudoTerminalIcon(cls):
        if cls.cachedPseudoTerminalClassIcon is None:
            path = getIcon(cls.iconPseudoTerminal)
            img = Image.open(path)
            cls.cachedPseudoTerminalClassIcon = ImageTk.PhotoImage(img)
        return cls.cachedPseudoTerminalClassIcon
    

    def open_terminal(self, iid=None, title="", enable_trap=True):
        if iid is not None:
            self.create_window(iid, title, enable_trap=enable_trap)
        elif not self.inited:
            self.create_terminal()
            self.after(100, self.update_size)
            self.inited = True
        return
    

    def launch_in_terminal(self, iid, commandline, use_pollex=True):
        session = self.get_session()
        settings = Settings()
        settings.reloadLocalSettings()
        if not settings.isTrapCommand() and use_pollex:
            commandline = "pollex "+commandline
        if settings.isTrapCommand() and not use_pollex:
            commandline = commandline
            
        if session is not None:
            window = session.windows.filter(window_name=str(iid))[0]
            self.terminalFrames[iid] = commandline
            window.select_window()
            window.panes[0].send_keys(commandline)


    def open_ro_terminal(self, iid, title, tool_controller, scanManager):
        if iid is not None:
            self.create_ro_window(iid, title, tool_controller, scanManager)
        return
    
    def open_any_terminal(self, iid, title, tool_controller, scanManager):
        if iid is not None:
            if iid in self.terminalFrames:
                self.open_terminal(iid, title)
            else:
                self.open_ro_terminal(iid, title, tool_controller, scanManager)

        return  

    def get_session(self):
        sessions = self.s.sessions.filter(session_name="pollenisator")
        if sessions:
            session = sessions[0]
        else:
            session = None
        return session

    def notif_terminal(self, notification):
        iid = notification.get("iid",{})
        check_iid = iid.get("check_iid", "")
        tool_iid = iid.get("tool_iid")
        iid = str(check_iid) if tool_iid is None else str(check_iid)+"|"+str(tool_iid)
        if self.opened != str(iid):
            try:
                self.terminalTv.item(str(iid), tags="notified")
            except tk.TclError: # item not found, may append if terminal is not opened
                pass
        return

    def create_terminal(self):
        settings = Settings()
        settings.reloadLocalSettings()
        self.terminalFrame.wait_visibility()

        self.wid = self.terminalFrame.winfo_id()
        self.s = libtmux.Server()
        (child_pid, fd) = pty.fork()
        self.child_pid = child_pid
        child_pid
        if child_pid == 0:
            # child process with ✨ black magic ✨
            try:
                logger.debug("Creating terminal...")
                session_name = "pollenisator"
                sessions = self.s.sessions.filter(session_name=session_name)
                if len(sessions) > 0:
                    for session in sessions:
                        session.kill_session()
                wid = self.wid
                logger.debug(f"Populatig window id {wid}")
                config_location = os.path.join(getMainDir(), "config/")
                xterm_conf = os.path.join(config_location, ".Xresources")
                tmux_conf = os.path.join(config_location, ".tmux.conf")
                terminal_conf = os.path.join(config_location, "shell_ressources")
                logger.debug(f"Trying to load xterm conf through xrdp {xterm_conf}")
                subprocess.run("xrdb -load %s" % xterm_conf, shell=True)
                is_there_zsh = os.environ.get("ZSH",None) is not None
                shell_command = settings.local_settings.get("terminal",  os.environ.get("SHELL","zsh" if is_there_zsh else "/bin/bash"))
                logger.debug(f"shell_command found : {shell_command}")
                trap_suffix = ("trap" if settings.isTrapCommand()  else "notrap")
                logger.debug(f"trap_suffix found : {trap_suffix}")
                if os.path.basename(shell_command) == "zsh":
                    terminal_conf = os.path.join(terminal_conf, "zshrc_"+trap_suffix)
                    default_command = f"ZDOTDIR={terminal_conf} {shell_command}"
                else:
                    terminal_conf = os.path.join(terminal_conf, "bash_setupTerminalForPentest_"+trap_suffix+".sh")
                    default_command = f"{shell_command} --rcfile {terminal_conf}"
                logger.debug(f"terminal_conf found : {terminal_conf}")
                logger.debug(f"default_command found : {default_command}")
                tmux_conf_new = tmux_conf+".popo"
                with open(tmux_conf, "r") as f:
                    tmux_conf_content = f.read()
                    with open(tmux_conf_new, "w") as f2:
                        if "/bin" not in shell_command:
                            shell_command = "/bin/"+shell_command
                        tmux_conf_content += f"\nset -g default-shell {shell_command}"
                        tmux_conf_content += f"\nset -g default-command \"{default_command}\"\n"
                        f2.write(tmux_conf_content)
                    tmux_conf = tmux_conf_new
                command = f"xterm -into {wid} -class popoxterm -name popoxterm -e \"tmux -f {tmux_conf} new-session -s {session_name} -n shell\""
                logger.debug(f"Lauching terminal : {command}")
                proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
                signal.signal(signal.SIGINT, lambda signum,sigframe: killThisProc(proc))
                signal.signal(signal.SIGTERM, lambda signum,sigframe: killThisProc(proc))
                # Wait for session to pop
                for i in range(3):
                    if len(self.s.sessions.filter(session_name=session_name)) > 0:
                        break
                    time.sleep(0.5*i)
                
                session = self.get_session()
                if session is not None:
                    logger.debug(f"SUCCESS Lauching terminal : session found")
                    for i in range(3):
                        if len(session.windows.filter(window_name="shell")) > 0:
                            break
                        time.sleep(0.5*i)
                    if len(session.windows.filter(window_name="shell")) > 0:
                        window = session.windows.filter(window_name="shell")[0]
                        window.select_window()
                        
            except Exception as e:
                logger.error("TERMINAL exception: "+str(e))
                sys.exit(0)
            try:
                proc._killed = False
                stdout, stderr = proc.communicate() # wait for ending
                logger.error("TERMINAL ended: "+str(stdout)+"///"+str(stderr))
                sys.exit(0)
            except Exception as e:
                logger.error("TERMINAL end exception: "+str(e))
                sys.exit(0)
                
        else:
            
            queue = multiprocessing.Queue()
            queueResponse = multiprocessing.Queue()
            p = multiprocessing.Process(target=read_and_forward_pty_output, args=[fd, child_pid, queue, queueResponse, False])
            p.start()
            self.terminalFrame.bind("<Configure>", self.update_size)
            self.update_size()
            self.terminalTv.insert("", "end", "shell", text="shell", image=TerminalsWidget.getIcon())
            self.terminalTv.selection_set("shell")
    
    def view_window(self, iid):
        if iid.endswith("|ro"):
            if self.terminalFrame.winfo_viewable():
                self.terminalFrame.pack_forget()
            if not self.pseudoTerminalFrame.winfo_viewable():
                self.pseudoTerminalFrame.pack(fill=tk.BOTH, expand=True)
            elif self.opened.endswith("|ro"):
                if self.opened in self.pseudoTermFrames:
                    self.pseudoTermFrames[self.opened].pack_forget()
                     

        else:
            if self.pseudoTerminalFrame.winfo_viewable():
                self.pseudoTerminalFrame.pack_forget()
            if not self.terminalFrame.winfo_viewable():
                self.terminalFrame.pack(fill=tk.BOTH, expand=True)
            sessions = self.s.sessions.filter(session_name="pollenisator")
            if sessions:
                session = sessions[0]
                windows = session.windows.filter(window_name=str(iid))
                if not windows:
                    window = session.new_window(attach=True, window_name=str(iid))
                else:
                    window = windows[0]
                    window.select_window()
        self.opened = iid

    def closeDoneTerms(self):
        for iid in self.terminalTv.get_children():
            if iid == "shell":
                continue
            try:
                tags = self.terminalTv.item(str(iid))["tags"]
                if "notified-read" not in tags:
                    continue
            except tk.TclError:
                continue
            if iid.endswith("|ro"):
                if iid in self.pseudoTermFrames:
                    self.pseudoTermFrames[iid].quit()
                self.terminalTv.selection_set("shell")
                self.pseudoTermFrames[iid].destroy()
                del self.pseudoTermFrames[iid]
            else:
                sessions = self.s.sessions.filter(session_name="pollenisator")
                if sessions:
                    session = sessions[0]
                    windows = session.windows.filter(window_name=str(iid))
                    if windows:
                        window = windows[0]
                        window.kill_window()
                    del self.terminalFrames[iid]
            self.terminalTv.delete(str(iid))

    def closeAllTerms(self):
        for iid in self.terminalTv.get_children():
            if iid == "shell":
                continue
            if iid.endswith("|ro"):
                if iid in self.pseudoTermFrames:
                    self.pseudoTermFrames[iid].quit()
                self.terminalTv.selection_set("shell")
                self.pseudoTermFrames[iid].destroy()
                del self.pseudoTermFrames[iid]
            else:
                sessions = self.s.sessions.filter(session_name="pollenisator")
                if sessions:
                    session = sessions[0]
                    windows = session.windows.filter(window_name=str(iid))
                    if windows:
                        window = windows[0]
                        window.kill_window()
                    del self.terminalFrames[iid]
        self.terminalTv.delete(*self.terminalTv.get_children())
        self.terminalTv.insert("", "end", "shell", text="shell", image=TerminalsWidget.getIcon())
        self.terminalTv.selection_set("shell")
            
    def closeTerm(self):
        if self.contextualMenu.selection is None:
            return
        item = self.terminalTv.item(self.contextualMenu.selection)
        iid = str(self.contextualMenu.selection)
        if not iid:
            return
        if iid == "shell":
            return
        
        if iid.endswith("|ro"):
            if iid in self.pseudoTermFrames:
                self.pseudoTermFrames[iid].quit()
            self.terminalTv.selection_set("shell")
            self.pseudoTermFrames[iid].destroy()
            del self.pseudoTermFrames[str(iid)]
        else:
            sessions = self.s.sessions.filter(session_name="pollenisator")
            if sessions:
                session = sessions[0]
                windows = session.windows.filter(window_name=iid)
                if windows:
                    window = windows[0]
                    window.kill_window()
                if str(iid) not in self.terminalFrames:
                    logger.error("TERMINAL not in terminalFrames: "+str(iid)+ " list is "+str(self.terminalFrames))
                else:
                    del self.terminalFrames[str(iid)]
        self.terminalTv.delete(iid)
        


    def create_window(self, iid, title="none", enable_trap=True):
        sessions = self.s.sessions.filter(session_name="pollenisator")
        if sessions:
            session = sessions[0]
            windows = session.windows.filter(window_name=str(iid))
            if iid != "shell":
                session.set_environment("POLLENISATOR_DEFAULT_TARGET", str(iid))
                session.set_environment("TRAP_FOR_POLLEX", str(enable_trap))
            if not windows:
                window = session.new_window(attach=True, window_name=str(iid))
            else:
                window = windows[0]
                #if iid != "shell":
                    #window.panes[0].send_keys("export POLLENISATOR_DEFAULT_TARGET="+str(iid))
                    
            try:
                self.terminalTv.insert("", "end", str(iid), text=title, image=TerminalsWidget.getIcon())
            except tk.TclError:
                pass
            self.terminalTv.selection_set(str(iid)) # trigger treeview select 

    def create_ro_window(self, iid, title, toolController, scanManager):
        tv_iid = iid+"|"+"ro"
        if tv_iid in self.pseudoTermFrames:
            self.pseudoTermFrames[tv_iid].quit()
        self.pseudoTermFrames[tv_iid] = PseudoTermFrame(self.pseudoTerminalFrame, toolController, scanManager)
        self.pseudoTermFrames[tv_iid].pack(fill=tk.BOTH, expand=True)
        try:
            self.terminalTv.insert("", "end", iid=str(tv_iid), text=title, image=TerminalsWidget.getPseudoTerminalIcon())
        except tk.TclError as e:
            print(e)
            pass
        self.terminalTv.selection_set(str(tv_iid)) # trigger treeview select 

        