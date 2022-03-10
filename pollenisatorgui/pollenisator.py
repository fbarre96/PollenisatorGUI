#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@author: Fabien Barré for AlgoSecure
# Date: 11/07/2017
# Major version released: 09/2019
# @version: 1.0
"""
from datetime import datetime
from pollenisatorgui.AutoScanWorker import executeCommand
from pollenisatorgui.core.Models.Tool import Tool
from pollenisatorgui.core.Models.Wave import Wave
import time
import tkinter as tk
import os
import sys
import shlex
import signal
from multiprocessing.connection import Client
from pollenisatorgui.core.Components.apiclient import APIClient
from pollenisatorgui.core.Application.Appli import Appli


class GracefulKiller:
    """
    Signal handler to shut down properly.

    Attributes:
        kill_now: a boolean that can checked to know that it's time to stop.
    """
    kill_now = False

    def __init__(self, app):
        """
        Constructor. Hook the signals SIGINT and SIGTERM to method exitGracefully

        Args:
            app: The appli object to stop
        """
        signal.signal(signal.SIGINT, self.exitGracefully)
        signal.signal(signal.SIGTERM, self.exitGracefully)
        # signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        self.app = app

    def exitGracefully(self, _signum, _frame):
        """
        Set the kill_now class attributes to True. Call the onClosing function of the application given at init.

        Args:
            signum: not used
            frame: not used
        """
        print('You pressed Ctrl+C!')
        self.app.onClosing()
        self.kill_now = True


#######################################
############## MAIN ###################
#######################################
def pollex():
    """Send a command to execute for pollenisator-gui running instance
    """
    apiclient = APIClient.getInstance()
    apiclient.tryConnection()
    execCmd = shlex.join(sys.argv[1:])
    cmdName = os.path.splitext(os.path.basename(execCmd.split(" ")[0]))[0]
    args = shlex.join(shlex.split(execCmd)[1:])
    cmdName +="::"+str(time.time()).replace(" ","-")
    wave = Wave().initialize("Custom commands")
    wave.addInDb()
    tool = Tool()
    tool.initialize(cmdName, "Custom commands", "", None, None, None, "wave", execCmd, dated=datetime.now().strftime("%d/%m/%Y %H:%M:%S"), datef="None", scanner_ip="localhost")
    tool.updateInfos({"args":args})
    res, iid = tool.addInDb()
    if res:
        ret_code, outputstr = executeCommand(apiclient, str(iid), "auto-detect", True, True)
        if not ret_code:
            print(outputstr)
        else:
            print(f"Output created here : {outputstr}")
            

def main():
    """Main function. Start pollenisator application
    """
    
    print("""
.__    ..              ,       
[__) _ || _ ._ * __ _.-+- _ ._.
|   (_)||(/,[ )|_) (_] | (_)[  
                               
""")
    root = tk.Tk()
    root.resizable(True, True)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.join(dir_path, "icon/favicon.png")
    img = tk.PhotoImage(file=dir_path)
    root.iconphoto(True, img)

    root.minsize(width=400, height=400)
    root.resizable(True, True)
    root.title("Pollenisator")
    root.geometry("1220x830")
    gc = None
    app = Appli(root)
    try:
        root.protocol("WM_DELETE_WINDOW", app.onClosing)
        gc = GracefulKiller(app)
        if not app.quitting:
            root.mainloop()
        print("Exiting tkinter main loop")
    except tk.TclError:
        pass
    try:
        root.destroy()
        print("Destroying app window")
    except tk.TclError:
        pass
    app.onClosing()
    if gc is not None:
        gc.kill_now = True


if __name__ == '__main__':
    main()
