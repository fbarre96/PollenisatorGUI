import os
import uuid
import socket
import sys
from pollenisatorgui.core.components.terminalworker import TerminalWorker
import pollenisatorgui.core.components.utils as utils
import json

def pollterminal():
    """Starts a worker that receives scan orders from the server and upload results
    """
    force_reconnect = False
    if len(sys.argv) > 2:
        print("Usage : pollterminal [--reconnect]")
        sys.exit(1)
    elif len(sys.argv) == 2:
        if sys.argv[1] == "--reconnect":
            print("Reconnecting to server")
            force_reconnect = True
        else:
            print("Invalid option : "+sys.argv[1]+"\nUsage : pollterminal [--reconnect]")
            sys.exit(1)
    verbose = False
    local_settings = utils.load_local_settings()
    sm = TerminalWorker(local_settings)
    myname = os.getenv('POLLENISATOR_WORKER_NAME', str(uuid.uuid4())+"@"+socket.gethostname())
    plugins = list(set(local_settings.get("my_commands",{}).keys()))
    
    sm.connect(myname, plugins, force_reconnect=force_reconnect)
    
    sm.wait()
