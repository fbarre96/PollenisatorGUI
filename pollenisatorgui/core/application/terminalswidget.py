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
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.components.utils import getMainDir, getIcon
from pollenisatorgui.core.components.logger_config import logger
from PIL import Image, ImageTk


def read_and_forward_pty_output(fd, queue=None, queueResponse=None):
    max_read_bytes = 1024 * 20
    try:
        while True:
            time.sleep(0.01)
            if fd:
                timeout_sec = 0
                (data_ready, _, _) = select.select([fd], [], [], timeout_sec)
                if not queue.empty():
                    command = queue.get()
                    os.write(fd, command.encode())
                if data_ready:
                    output = os.read(fd, max_read_bytes).decode(
                        errors="ignore"
                    )
                    queueResponse.put(output.replace("\r",""))
    except Exception as e:
        pass

def killThisProc(proc):
    try:
        logger.error("Killing process terminal")
        time.sleep(1) # HACK to avoid xterm crash ✨ black magic ✨
        os.kill(proc.pid, signal.SIGTERM)
        
    except Exception as e:
        pass

class TerminalsWidget(CTkFrame):
    cachedClassIcon = None
    icon = "tab_terminal.png"
    def __init__(self, parent,  **kwargs):
        super().__init__(parent,  **kwargs)
        self.parent = parent
        
        self.child_pid = None
        self.proc = None
        self.fd = None
        self.inited = False
        self.initUI()

    def initUI(self):
        self.panedwindow = tk.PanedWindow(self, orient=tk.HORIZONTAL, height=200) 
        s = ttk.Style()
        s.configure('Terminal.Treeview.Item', indicatorsize=0)
        self.terminalTv = ttk.Treeview(self.panedwindow, show="tree", selectmode="browse", style="Terminal.Treeview")
        self.terminalTv.column('#0', minwidth=50, width=80, stretch=tk.YES)
        self.terminalFrame = tk.Frame(self)
        self.terminalFrame.pack(fill=tk.BOTH, expand=True)
        self.terminalTv.pack(fill=tk.Y, expand=True, padx=0,ipadx=0)
        self.terminalTv.bind("<<TreeviewSelect>>", self.onTreeviewSelect)
        self.terminalTv.tag_configure("notified", background="red")
        self.panedwindow.add(self.terminalTv)
        self.panedwindow.add(self.terminalFrame)
        self.panedwindow.pack(fill=tk.BOTH, expand=True)
    
    def onTreeviewSelect(self, event=None):
        selection = self.terminalTv.selection()
        
        if len(selection) == 1:
            try:
                self.terminalTv.item(str(selection[0]), tags=("neutral",))
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

    @classmethod
    def getIcon(cls):
        if cls.cachedClassIcon is None:
            path = getIcon(cls.icon)
            img = Image.open(path)
            resized_image = img.resize((16,16), Image.ANTIALIAS)
            cls.cachedClassIcon = ImageTk.PhotoImage(resized_image)
        return cls.cachedClassIcon
    

    def open_terminal(self, iid=None, title=""):
        if iid is not None:
            
            self.create_window(iid, title)
        elif not self.inited:
            self.create_terminal()
            self.inited = True
        return
    
    def notif_terminal(self, iid):
        self.terminalTv.item(str(iid), tags="notified")
        return

    def create_terminal(self):
        settings = Settings()
        settings.reloadLocalSettings()
        self.wid = self.terminalFrame.winfo_id()
        self.s = libtmux.Server()
        (child_pid, fd) = pty.fork()
        self.child_pid = child_pid
        child_pid
        if child_pid == 0:
            # child process with ✨ black magic ✨
            try:
                session_name = "pollenisator"
                sessions = self.s.sessions.filter(session_name=session_name)
                if len(sessions) > 0:
                    for session in sessions:
                        session.kill_session()
                wid = self.wid
                config_location = os.path.join(getMainDir(), "config/")
                xterm_conf = os.path.join(config_location, ".Xresources")
                tmux_conf = os.path.join(config_location, ".tmux.conf")
                terminal_conf = os.path.join(config_location, "shell_ressources")
                subprocess.run("xrdb -load %s" % xterm_conf, shell=True)
                shell_command = os.environ.get("SHELL", "/bin/bash")
                if shutil.which("zsh") or os.environ.get("ZSH"):
                    shell_command = "zsh"
                trap_suffix = ("trap" if settings.isTrapCommand()  else "notrap")
                if shell_command.endswith("zsh"):
                    terminal_conf = os.path.join(terminal_conf, "zshrc_"+trap_suffix)
                    default_command = f"ZDOTDIR={terminal_conf} {shell_command}"
                else:
                    terminal_conf = os.path.join(terminal_conf, "bash_setupTerminalForPentest_"+trap_suffix+".sh")
                    default_command = f"{shell_command} --rcfile {terminal_conf}"
                    
                tmux_conf_new = tmux_conf+".popo"
                with open(tmux_conf, "r") as f:
                    tmux_conf_content = f.read()
                    with open(tmux_conf_new, "w") as f2:
                        tmux_conf_content += f"\nset -g default-command \"{default_command}\""
                        f2.write(tmux_conf_content)
                    tmux_conf = tmux_conf_new
                command = f"xterm -into {wid} -class popoxterm -e \"tmux -f {tmux_conf} new-session -s {session_name} -n shell\""
                
                proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
                signal.signal(signal.SIGINT, lambda signum,sigframe: killThisProc(proc))
                signal.signal(signal.SIGTERM, lambda signum,sigframe: killThisProc(proc))
            except Exception as e:
                logger.error(e)
                sys.exit(0)
            try:
                # Wait for session to pop
                for i in range(3):
                    if len(self.s.sessions.filter(session_name=session_name)) > 0:
                        break
                    time.sleep(0.5*i)
                
                sessions = self.s.sessions.filter(session_name=session_name)
                if sessions:
                    session = sessions[0]
                    for i in range(3):
                        if len(session.windows.filter(window_name="shell")) > 0:
                            break
                        time.sleep(0.5*i)
                    if len(session.windows.filter(window_name="shell")) > 0:
                        window = session.windows.filter(window_name="shell")[0]
                        window.select_window()
                        
            except Exception as e:
                logger.error(e)
                sys.exit(0)
            try:
                proc._killed = False
                stdout, stderr = proc.communicate() # wait for ending
                sys.exit(0)
            except Exception as e:
                logger.error(e)
                sys.exit(0)
                
        else:
            
            queue = multiprocessing.Queue()
            queueResponse = multiprocessing.Queue()
            p = multiprocessing.Process(target=read_and_forward_pty_output, args=[fd, queue, queueResponse])
            p.start()
            self.terminalFrame.bind("<Configure>", self.update_size)
            self.update_size()
            self.terminalTv.insert("", "end", "shell", text="shell", image=TerminalsWidget.getIcon())
            self.terminalTv.selection_set("shell")
    
    def view_window(self, iid):
        sessions = self.s.sessions.filter(session_name="pollenisator")
        if sessions:
            session = sessions[0]
            windows = session.windows.filter(window_name=str(iid))
            if not windows:
                window = session.new_window(attach=True, window_name=str(iid))
            else:
                window = windows[0]
                window.select_window()
            


    def create_window(self, iid, title="none"):
        sessions = self.s.sessions.filter(session_name="pollenisator")
        if sessions:
            session = sessions[0]
            windows = session.windows.filter(window_name=str(iid))
            if iid != "shell":
                session.set_environment("POLLENISATOR_DEFAULT_TARGET", str(iid))

            if not windows:
                window = session.new_window(attach=True, window_name=str(iid))
                
                #if iid != "shell":
                    #window.panes[0].send_keys("export POLLENISATOR_DEFAULT_TARGET="+str(iid))
                    
            try:
                self.terminalTv.insert("", "end", str(iid), text=title, image=TerminalsWidget.getIcon())
            except tk.TclError:
                pass
            self.terminalTv.selection_set(str(iid)) # trigger treeview select 
