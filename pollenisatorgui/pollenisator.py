#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@author: Fabien Barré for AlgoSecure
# Date: 12/10/2022
# Major version released: 09/2019
# @version: 2.2
"""

import time
import tkinter as tk
import os
import sys
import git
import pipx
import signal

import requests
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.application.appli import Appli
import pollenisatorgui.core.components.utils as utils
import threading
from getpass import getpass
from pollenisatorgui.core.components.logger_config import logger
import customtkinter
import subprocess

event_obj = threading.Event()
customtkinter.set_default_color_theme(utils.getColorTheme())

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
        #import traceback
        #traceback.print_stack(_frame)
        self.app.onClosing()
        event_obj.set()
        self.kill_now = True


#######################################
############## MAIN ###################
#######################################

def get_local_git_version():
    try:
        repo = git.Repo(search_parent_directories=True)
        latest_tag = repo.tags[-1]
        latest_version = latest_tag.name
        return latest_version
    except Exception as e:
        print("Error fetching latest version from Git:", e)
        return None


def get_latest_github_version():
    try:
        # Make a GET request to GitHub's releases endpoint
        url = f"https://api.github.com/repos/fbarre96/PollenisatorGUI/releases/latest"
        response = requests.get(url)
        if response.status_code == 200:
            latest_version = response.json()["tag_name"]
            return latest_version
        else:
            print("Error fetching latest version from GitHub:", response.text)
            return None
    except Exception as e:
        print("Error fetching latest version from GitHub:", e)
        return None
    
def checkForUpdates():
    latest = get_latest_github_version()
    local = get_local_git_version()
    if local is None or latest is None:
        return False
    if local != latest:
        return True
    return False

def update():
    try:
        # Use pipx to install the latest version of the package
        subprocess.run(['pipx', 'upgrade', 'pollenisatorgui'])
        print("Package updated successfully!")
    except Exception as e:
        print("Error updating package:", e)

def consoleConnect(force=False, askPentest=True):    
    apiclient = APIClient.getInstance()
    abandon = False
    if force:
        apiclient.disconnect()
    
    while (not apiclient.tryConnection(force=force) or not apiclient.isConnected()) and not abandon:
        success = promptForConnection() is None
    if apiclient.isConnected() and askPentest:
        promptForPentest()
    return not abandon
        
def promptForConnection():
   
    clientCfg = utils.loadClientConfig()
    host = clientCfg.get("host", "")
    port = clientCfg.get("port", "5000")
    https = str(clientCfg.get("https", "True")).title() == "True"

    host_result = input(f'Server hostname (defaut {host}):')
    if host_result.strip() == "":
        host_result = host
    port_result = input(f'Server Port (default  {port}):')
    if port_result.strip() == "":
        port_result = port
    https_result = input(f'Use HTTPS (y/N)?').strip() == 'y'
    
    apiclient = APIClient.getInstance()
    apiclient.reinitConnection()
    res = apiclient.tryConnection({"host":host_result, "port":port_result, "https":https_result})
    if res:
        username_result = input(f'Please input username:')
        password_result = getpass(prompt=f'Please input password:')
        #  pylint: disable=len-as-condition
        loginRes = apiclient.login(username_result, password_result)
        return loginRes
    else:
        print("Failed to contact this server.")
    return False

def promptForPentest():
    apiclient = APIClient.getInstance()
    pentests = apiclient.getPentestList()
    if pentests is None:
        pentests = []
    else:
        pentests.sort(key=lambda x: x["creation_date"], reverse=True)
    i = 0
    while i<=0:
        for i_p, pentest in enumerate(pentests):
            print(f"{i_p+1} : {pentest.get('nom', '')}")
        try:
            i = int(input("Selection (1-"+str(len(pentests))+"): "))
            if i <= 0 or i > len(pentests):
                print("Invalid selection, input must be between 1 and "+str(len(pentests)))
                i = 0
        except ValueError:
            i = 0
    apiclient.setCurrentPentest(pentests[i-1]["uuid"])

def parseDefaultTarget(stringToParse):
    if "|" in stringToParse:
        parts = stringToParse.split("|")
        ret = {}
        ret["check_iid"] = parts[0]
        ret["tool_iid"] = parts[1]
        ret["lvl"] = "import"
        return ret

    else:
        return {"check_iid":str(stringToParse), "lvl":"import"}


def pollup():
    """Send a file to pollenisator backend for analysis
    """
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        plugin = "auto-detect"
    elif len(sys.argv) == 3:
        filename = sys.argv[1]
        plugin = sys.argv[2]
    else:
        print("Usage : pollup <filename> [plugin or auto-detect]")
        sys.exit(1)
    uploadFile(filename, plugin)

def uploadFile(filename, plugin='auto-detect'):
    apiclient = APIClient.getInstance()
    apiclient.tryConnection()
    res = apiclient.tryAuth()
    if not res:
        consoleConnect()
    print(f"INFO : Uploading results {filename}")
    msg = apiclient.importExistingResultFile(filename, plugin, parseDefaultTarget(os.environ.get("POLLENISATOR_DEFAULT_TARGET", "")), "")
    print(msg)

def pollwatch():
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    class Handler(FileSystemEventHandler):
        @staticmethod
        def on_any_event(event):
            if event.is_directory:
                return None
            elif event.event_type == 'created':
                # Event is created, you can process it now
                uploadFile(event.src_path)
    apiclient = APIClient.getInstance()
    apiclient.tryConnection()
    res = apiclient.tryAuth()
    if not res:
        consoleConnect()
    observer = Observer()
    observer.schedule(Handler(), '.', recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(5)
    finally:
        observer.stop()
        observer.join()

    

def main():
    """Main function. Start pollenisator application
    """
    
    print("""
.__    ..              ,       
[__) _ || _ ._ * __ _.-+- _ ._.
|   (_)||(/,[ )|_) (_] | (_)[  
                               
""")
    event_obj.clear() 
    gc = None
    update_available = checkForUpdates()
    if update_available:
        ask_update = input("An update is available, do you want to update now (y/N)?").strip().lower() == "y"
        if ask_update:
            update()
    app = Appli()
    try:
        gc = GracefulKiller(app)
        if not app.quitting:
            app.mainloop()
        print("Exiting tkinter main loop")
    except tk.TclError:
        pass
    try:
        try:
            app.destroy()
            print("Destroying app window")
        except tk.TclError:
            pass
        if gc is not None:
            gc.kill_now = True
        event_obj.set()
        app.onClosing()
    except Exception as e:
        print("Error while closing app")
        print(e)
if __name__ == '__main__':
    main()
