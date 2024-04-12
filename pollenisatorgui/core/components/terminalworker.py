import threading
import time
import socketio

from bson import ObjectId
from pollenisatorgui.core.components.apiclient import APIClient
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.components.logger_config import logger
from pollenisatorgui.pollenisator import consoleConnect
import pty
import os
import subprocess
import select
import termios
import struct
import fcntl
import shlex
import uuid

def set_winsize(fd, row, col, xpix=0, ypix=0):
    logger.debug("setting window size with termios")
    winsize = struct.pack("HHHH", row, col, xpix, ypix)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

class TerminalWorker:
    
    def __init__(self, settings):
        self.settings = settings
        self.sio = socketio.Client()
        self.name = ""
        self.pid = None
        self.fd = None
        self.timer = None
        self.local_scans = dict()
        terminal, rc_file = utils.getPreferedShell()
        if rc_file != "":
            self.cmd = [terminal, "--rcfile", rc_file]
        else:
            self.cmd = [terminal]

    def wait(self):
        self.sio.wait() 

         
    def read_and_forward_pty_output(self):
        max_read_bytes = 1024 * 20
        while True:
            time.sleep(0.01)
            if self.fd:
                timeout_sec = 0
                (data_ready, _, _) = select.select([self.fd], [], [], timeout_sec)
                if data_ready:
                    output = os.read(self.fd, max_read_bytes).decode(
                        errors="ignore"
                    )
                    self.sio.emit("pty-output", {"output": output}, namespace="/pty")


    def connect(self, name):
        apiclient = APIClient.getInstance()
        apiclient.tryConnection()
        res = apiclient.tryAuth()
        if not res:
            consoleConnect()
        if apiclient.isConnected() is False or apiclient.getCurrentPentest() == "":
            return
        self.sio.connect(apiclient.api_url)
        self.sio.emit("registerAsTerminalWorker", {"token":apiclient.getToken(), "pentest":apiclient.getCurrentPentest()})
        @self.sio.on("testTerminal")
        def test(data):
            print("Got terminal test "+str(data))

        # @self.sio.on("pty-input", namespace="/pty")
        # def pty_input(data):
        #     """write to the child pty. The pty sees this as if you are typing in a real
        #     terminal.
        #     """
        #     if self.fd:
        #         logger.debug("received input from browser: %s" % data["input"])
        #         os.write(self.fd, data["input"].encode())
        
        # @self.sio.on("resize", namespace="/pty")
        # def resize(data):
        #     if self.fd:
        #         logger.debug(f"Resizing window to {data['rows']}x{data['cols']}")
        #         set_winsize(self.fd, data["rows"], data["cols"])
        
        # # create child process attached to a pty we can read from and write to
        # (child_pid, fd) = pty.fork()
        # if child_pid == 0:
        #     # this is the child process fork.
        #     # anything printed here will show up in the pty, including the output
        #     # of this subprocess
        #     subprocess.run(self.cmd)
        # else:
        #     # this is the parent process fork.
        #     # store child fd and pid
        #     self.fd = fd
        #     self.pid = child_pid
        #     set_winsize(fd, 50, 50)
        #     cmd = " ".join(shlex.quote(c) for c in self.cmd)
        #     # logging/print statements must go after this because... I have no idea why
        #     # but if they come before the background task never starts
        #     t = threading.Thread(target=self.read_and_forward_pty_output)
        #     t.start()

        #     logger.info("child pid is " + child_pid)
        #     logger.info(
        #         f"starting background task with command `{cmd}` to continously read "
        #         "and forward pty output to client"
        #     )
        #     logger.info("task started")
        #     t.join()
