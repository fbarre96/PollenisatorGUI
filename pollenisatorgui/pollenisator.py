#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@author: Fabien Barré for AlgoSecure
# Date: 11/07/2017
# Major version released: 09/2019
# @version: 1.0
"""
from pollenisatorgui.core.Models.Command import Command
import time
import tkinter as tk
import os
import sys
import shlex
import signal
from pollenisatorgui.core.Components.apiclient import APIClient
from pollenisatorgui.core.Application.Appli import Appli
import pollenisatorgui.core.Components.Utils as Utils
import tempfile


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
    
    execCmd = shlex.join(sys.argv[1:])
    bin_name = shlex.split(execCmd)[0]
    if bin_name in ["echo", "print", "vim", "vi", "tmux", "nano", "code"]:
        return
    cmdName = os.path.splitext(os.path.basename(execCmd.split(" ")[0]))[0]
    apiclient = APIClient.getInstance()
    apiclient.tryConnection()
    cmdName +="::"+str(time.time()).replace(" ","-")
    commands = Command.fetchObjects({"bin_path":{'$regex':bin_name}})
    choices = set()
    if commands is not None:
        for command in commands:
            choices.add(command.plugin)
    if len(choices) == 0:
        plugin = "Default"
    elif len(choices) == 1:
        plugin = choices.pop()
    else:
        choice = -1
        while choice == -1:
            print("Choose plugin:")
            for i, choice in enumerate(choices):
                print(f"{i+1}. {choice}")
            try:
                choice_str = input()
                choice = int(choice_str)
            except ValueError as e:
                print("You must type a valid number")
            if choice > len(choices) or choice < 1:
                choice = -1
                print("You must type a number between 1 and "+str(len(choices)))
        plugin = list(choices)[choice-1]
    print("INFO : Executing plugin "+str(plugin))
    success, comm, fileext = apiclient.getDesiredOutputForPlugin(execCmd, plugin)
    if not success:
        print("ERROR : An error as occured : "+str(comm))
        return
    with tempfile.TemporaryDirectory() as tmpdirname:
        outputFilePath = os.path.join(tmpdirname, cmdName)
        comm = comm.replace("|outputDir|", outputFilePath)
        returncode, stdout = Utils.execute(comm, None, True)
        if stdout.strip() != "":
            print(stdout.strip())
        if not os.path.exists(outputFilePath):
            if os.path.exists(outputFilePath+fileext):
                outputFilePath+=fileext
            else:
                print(f"ERROR : Expected file was not generated {outputFilePath}")
                return
        print(f"INFO : Uploading results {outputFilePath}")
        msg = apiclient.importExistingResultFile(outputFilePath, plugin, os.environ.get("POLLENISATOR_DEFAULT_TARGET", ""))
        print(msg)
        

def main():
    """Main function. Start pollenisator application
    """
    
    print("""
.__    ..              ,       
[__) _ || _ ._ * __ _.-+- _ ._.
|   (_)||(/,[ )|_) (_] | (_)[  
                               
""")
   
    
    gc = None
    app = Appli()
    try:
        
        gc = GracefulKiller(app)
        if not app.quitting:
            app.mainloop()
        print("Exiting tkinter main loop")
    except tk.TclError:
        pass
    try:
        app.destroy()
        print("Destroying app window")
    except tk.TclError:
        pass
    app.onClosing()
    if gc is not None:
        gc.kill_now = True


if __name__ == '__main__':
    main()
