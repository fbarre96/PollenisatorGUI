import os
import uuid
import socket
from pollenisatorgui.core.components.scanworker import ScanWorker
from pollenisatorgui.core.components.settings import Settings

def pollworker():
    """Starts a worker that receives scan orders from the server and upload results
    """
    settings = Settings()
    settings.reloadLocalSettings()
    sm = ScanWorker(settings)
    myname = os.getenv('POLLENISATOR_WORKER_NAME', str(uuid.uuid4())+"@"+socket.gethostname())
    sm.connect(myname)
    sm.wait()    
