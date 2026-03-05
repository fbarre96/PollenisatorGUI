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
    from pollenisatorgui.core.components.cli_args import build_common_parser, apply_common_args
    parser = build_common_parser(description='Start a Pollenisator terminal worker')
    parser.add_argument('--reconnect', action='store_true',
                        help='Force reconnection to server even if a session is already saved')
    args = parser.parse_args()
    apply_common_args(args)

    local_settings = utils.load_local_settings()
    sm = TerminalWorker(local_settings)
    myname = os.getenv('POLLENISATOR_WORKER_NAME', str(uuid.uuid4())+"@"+socket.gethostname())
    plugins = list(set(local_settings.get("my_commands",{}).keys()))

    sm.connect(myname, plugins, force_reconnect=args.reconnect)

    sm.wait()

if __name__ == "__main__":
    pollterminal()