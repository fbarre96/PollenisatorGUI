import socketio
from core.Components.Utils import loadClientConfig

cfg = loadClientConfig()
sio = socketio.Client()
sio.connect("http://"+cfg["host"]+":"+cfg["port"])


@sio.on("notification")
def notification(arg):
    print("Notification:"+arg)

def disconnect():
    sio.disconnect()