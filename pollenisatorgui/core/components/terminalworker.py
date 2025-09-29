import threading
import time
import socketio
from pollenisatorgui.core.components.apiclient import APIClient
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.components.logger_config import logger
from pollenisatorgui.pollenisator import consoleConnect
from pollenisatorgui.core.components.scanworker import ScanWorker
import pty
import os
import subprocess
import select
import termios
import struct
import fcntl
import shlex

def set_winsize(fd, row, col, xpix=0, ypix=0):
    logger.debug("setting window size with termios")
    winsize = struct.pack("HHHH", row, col, xpix, ypix)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

class TerminalWorker(ScanWorker):
    
    def __init__(self, local_settings):
        super().__init__(local_settings)
        self.name = ""
        self.pid = None
        self.fd = None
        self.connected = False
        self.sessions = {}
        terminal, _ = utils.getPreferedShell()
        self.cmd = [terminal]


         
    def read_and_forward_pty_output(self, session_id):
        max_read_bytes = 1024 * 20
        fd = self.sessions[session_id]["fd"]
        while True:
            time.sleep(0.01)
            if fd:
                timeout_sec = 0
                (data_ready, _, _) = select.select([fd], [], [], timeout_sec)
                if data_ready:
                    output = os.read(fd, max_read_bytes).decode(
                        errors="ignore"
                    )
                    self.sio.emit("proxy-term", {"action":"pty-output", "id":session_id, "output": output})

    def startTerminalSession(self, data):
        session_id = data.get("id", None)
        target_check_iid = data.get("target_check_iid", None)
        if session_id is None:
            return
        if session_id in self.sessions:
            return
        self.sessions[session_id] = {
            "fd": None,
            "pid": None,
            "cmd": self.cmd,
            "timer": None,
            "connected": False,
            "target_check_iid": target_check_iid,
            "target_tools_iids": data.get("target_tools_iids", None)
        }
        (child_pid, fd) = pty.fork()
        if child_pid != 0:
            self.sessions[session_id]["fd"] = fd
            self.sessions[session_id]["pid"] = child_pid
            set_winsize(fd, data.get("dims", {}).get("rows", 50), data.get("dims", {}).get("cols", 50))
            cmd = " ".join(shlex.quote(c) for c in self.cmd)
            # logging/print statements must go after this because... I have no idea why
            # but if they come before the background task never starts
            t = threading.Thread(target=self.read_and_forward_pty_output, args=(session_id,))
            t.start()
            logger.info("child pid is " + str(child_pid))
            logger.info(
                f"starting background task with command `{cmd}` to continously read "
                "and forward pty output to client"
            )
            logger.info("task started")
        else:
            environ = os.environ.copy()
            target_check_iid = self.sessions[session_id].get("target_check_iid", None)
            target_tools_iids = self.sessions[session_id].get("target_tools_iids", None)
            target = ""
            if target_check_iid:
                if isinstance(target_check_iid, list):
                    target = ",".join(target_check_iid)
                else:
                    target = str(target_check_iid)
            if target_tools_iids:
                target += "|"
                if isinstance(target_tools_iids, list):
                    target += ",".join(target_tools_iids)
                else:
                    target += str(target_tools_iids)
            environ["POLLENISATOR_DEFAULT_TARGET"] = target
            logger.info("starting terminal session with command: %s" % self.cmd)
            subprocess.run(self.cmd,  shell=True, env=environ)
        
    def stopTerminalSession(self, data):
        session_id = data.get("id", None)
        if session_id is None:
            return
        if session_id not in self.sessions:
            return
        session = self.sessions[session_id]
        if session["fd"]:
            os.close(session["fd"])
        if session["pid"]:
            os.kill(session["pid"], 9)
        del self.sessions[session_id]

    def sendInput(self, data):
        session_id = data.get("id", None)
        if session_id is None:
            return
        if session_id not in self.sessions:
            return
        session = self.sessions[session_id]
        if session["fd"]:
            logger.debug("received input from browser: %s" % data["input"])
            os.write(session["fd"], data["input"].encode())

    def sendStop(self, session):
        if session["fd"]:
            print("sending Ctrl+c to session")
            os.write(session["fd"], b"\x03")
    
    def resize(self, data):
        session_id = data.get("id", None)
        if session_id is None:
            return
        if session_id not in self.sessions:
            return
        session = self.sessions[session_id]
        if session["fd"]:
            dims = data.get("dims", {})
            logger.debug(f"Resizing window to {dims['rows']}x{dims['cols']}")
            set_winsize(session["fd"], dims["rows"], dims["cols"])

    def connect(self, name, plugins, force_reconnect=False):
        apiclient = APIClient.getInstance()
        if force_reconnect:
            apiclient.disconnect()
        self.name = name
        apiclient.tryConnection()
        res = apiclient.tryAuth()
        if not res:
            consoleConnect()
        if apiclient.isConnected() is False or apiclient.getCurrentPentest() == "":
            return
        findPlugins = apiclient.getPlugins()
        if findPlugins is not None:
            for pluginFound in findPlugins:
                if pluginFound["plugin"] not in self.local_settings["my_commands"].keys():
                    # NOT CONFIGURED YET
                    if pluginFound["plugin"] == "auto-detect" or pluginFound["plugin"] == "Default":
                        # auto-detect is a special case, we don't want to configure it
                        continue
                    get_bin_path = utils.which_expand_aliases(pluginFound["default_bin_names"])
                    for value in get_bin_path.values():
                        if value is not None:
                            get_bin_path = value
                            break
                    if get_bin_path is not None:
                        # BUT TOOL IS INSTALLED
                        self.local_settings["my_commands"][pluginFound["plugin"]] = get_bin_path
                        utils.save_local_settings(self.local_settings)
                        plugins.append(pluginFound["plugin"])
                        print("[+] Found missing plugin : auto configuration "+pluginFound["plugin"]+" with path "+get_bin_path)
                    else:
                        print("[-] Missing plugin : "+pluginFound["plugin"]+" (not installed on this system?)")
        self.sio.connect(apiclient.api_url)
        self.sio.emit("registerAsTerminalWorker", {"token":apiclient.getToken(), "name":name, "supported_plugins":plugins, "pentest":apiclient.getCurrentPentest()})
        self.connected = False
        @self.sio.on("testTerminal")
        def test(data):
            print("Got terminal test "+str(data))

        @self.sio.on("consumer_connected")
        def consumer_connected(data):
            print("Got terminal consumer_connected "+str(data))
            self.connected = True

        @self.sio.on("consumer_disconnected")
        def consumer_disconnected(data):
            print("Got terminal consumer_disconnected "+str(data))
            self.connected = False

        @self.sio.on("proxy-term")
        def proxy_term(data):
            print("proxy-term "+str(data))
            if data.get("action", "") == "start-terminal-session":
                self.startTerminalSession(data)
            if data.get("action", "") == "stop-terminal-session":
                self.stopTerminalSession(data)
            if data.get("action", "") == "pty-input":
                self.sendInput(data)
            if data.get("action", "") == "pty-resize":
                self.resize(data)

        @self.sio.on("stop-terminal-command")
        def stop_terminal_command(data):
            print("Got stop-terminal-command "+str(data))
            for session_id, session_data in self.sessions.items():
                target = session_data.get("target_check_iid")
                print("Target is "+str(target))
                parts = target.split("|")
                if len(parts) >= 2:
                    tool_iid = parts[1]
                    print("If tool iid is "+str(tool_iid)+" == "+str(data.get("tool_iid")))
                    if tool_iid == data.get("tool_iid"):
                        print("SendingStop to session if fd")
                        self.sendStop(session_data)

        super().connect(name)