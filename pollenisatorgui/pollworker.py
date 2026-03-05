import os
import sys
import uuid
import socket
from pollenisatorgui.core.components.scanworker import ScanWorker
from pollenisatorgui.core.components.settings import Settings

def pollworker():
    """Starts a worker that receives scan orders from the server and upload results
    """
    from pollenisatorgui.core.components.cli_args import build_common_parser, apply_common_args
    parser = build_common_parser(description='Start a Pollenisator scan worker')
    args = parser.parse_args()
    apply_common_args(args)

    settings = Settings()
    settings.reloadLocalSettings()
    sm = ScanWorker(settings)
    myname = os.getenv('POLLENISATOR_WORKER_NAME', str(uuid.uuid4())+"@"+socket.gethostname())
    sm.connect(myname)
    sm.wait()
