"""Provide useful functions"""
import sys
import os
import socket
import subprocess
import time
from datetime import datetime
from threading import Timer
import json
from netaddr import IPNetwork
from netaddr.core import AddrFormatError
from bson import ObjectId
import signal

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return "ObjectId|"+str(o)
        elif isinstance(o, datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)

class JSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
        
    def object_hook(self, dct):
        for k,v in dct.items():
            if isinstance(v, list):
                new_lst = []
                for item in v:
                    if 'ObjectId|' in str(item):
                        new_lst.append(ObjectId(item.split('ObjectId|')[1]))
                    else:
                        new_lst.append(item)
                    dct[k] = new_lst
            else:
                if 'ObjectId|' in str(v):
                    dct[k] = ObjectId(v.split('ObjectId|')[1])
        return dct


def loadPlugin(pluginName):
    """
    Load a the plugin python corresponding to the given command name.
    The plugin must start with the command name and be located in plugins folder.
    Args:
        pluginName: the command name to load a plugin for

    Returns:
        return the module plugin loaded or default plugin if not found.
    """
    from pollenisatorgui.core.plugins.plugin import REGISTRY
    # Load plugins
    dir_path = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(dir_path, "../plugins/")
    # Load plugins
    sys.path.insert(0, path)
    try:
        # Dynamic import, raises ValueError if not found
        if not pluginName.endswith(".py"):
            pluginName += ".py"
        # trigger exception if plugin does not exist
        __import__(pluginName[:-3])
        return REGISTRY[pluginName[:-3]]  # removes the .py
    except ValueError:
        __import__("Default")
        return REGISTRY["Default"]
    except FileNotFoundError:
        __import__("Default")
        return REGISTRY["Default"]
    except ModuleNotFoundError:
        __import__("Default")
        return REGISTRY["Default"]


def isIp(domain_or_networks):
    """
    Check if the given scope string is a network ip or a domain.
    Args:
        domain_or_networks: the domain string or the network ipv4 range string
    Returns:
        Returns True if it is a network ipv4 range, False if it is a domain (any other possible case).
    """
    import re
    regex_network_ip = r"((?:[0-9]{1,3}\.){3}[0-9]{1,3})$"
    ipSearch = re.match(regex_network_ip, domain_or_networks)
    return ipSearch is not None


def isNetworkIp(domain_or_networks):
    """
    Check if the given scope string is a network ip or a domain.
    Args:
        domain_or_networks: the domain string or the network ipv4 range string
    Returns:
        Returns True if it is a network ipv4 range, False if it is a domain (any other possible case).
    """
    try:
        IPNetwork(domain_or_networks)
    except AddrFormatError:
        return False
    return True


def splitRange(rangeIp):
    """
    Check if the given range string is bigger than a /24, if it is, splits it in many /24.
    Args:
        rangeIp: network ipv4 range string
    Returns:
        Returns a list of IpNetwork objects corresponding to the range given as /24s.
        If the entry range is smaller than a /24 (like /25 ... /32) the list will be empty.
    """
    ip = IPNetwork(rangeIp)
    subnets = list(ip.subnet(24))
    return subnets


def resetUnfinishedTools():
    """
    Reset all tools running to a ready state. This is useful if a command was running on a worker and the auto scanning was interrupted.
    """
    # test all the cases if datef is defined or not.
    # Normally, only the first one is necessary
    from pollenisatorgui.core.Models.Tool import Tool
    tools = Tool.fetchObjects({"datef": "None", "scanner_ip": {"$ne": "None"}})
    for tool in tools:
        tool.markAsNotDone()
    tools = Tool.fetchObjects({"datef": "None", "dated": {"$ne": "None"}})
    for tool in tools:
        tool.markAsNotDone()
    tools = Tool.fetchObjects(
        {"datef": {"$exists": False}, "dated": {"$ne": "None"}})
    for tool in tools:
        tool.markAsNotDone()
    tools = Tool.fetchObjects(
        {"datef": {"$exists": False}, "scanner_ip": {"$ne": "None"}})
    for tool in tools:
        tool.markAsNotDone()


def stringToDate(datestring):
    """Converts a string with format '%d/%m/%Y %H:%M:%S' to a python date object.
    Args:
        datestring: Returns the date python object if the given string is successfully converted, None otherwise"""
    ret = None
    if isinstance(datestring, str):
        if datestring != "None":
            ret = datetime.strptime(
                datestring, '%d/%m/%Y %H:%M:%S')
    return ret


def fitNowTime(dated, datef):
    """Check the current time on the machine is between the given start and end date.
    Args:
        dated: the starting date for the interval
        datef: the ending date for the interval
    Returns:
        True if the current time is between the given interval. False otherwise.
        If one of the args is None, returns False."""
    today = datetime.now()
    date_start = stringToDate(dated)
    date_end = stringToDate(datef)
    if date_start is None or date_end is None:
        return False
    return today > date_start and date_end > today

def handleProcKill(proc):
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    proc._killed = True

def execute(command, timeout=None, printStdout=True):
    """
    Execute a bash command and print output

    Args:
        command: A bash command
        timeout: a date in the futur when the command will be stopped if still running or None to not use this option, default as None.
        printStdout: A boolean indicating if the stdout should be printed. Default to True.

    Returns:
        Return the return code of this command

    Raises:
        Raise a KeyboardInterrupt if the command was interrupted by a KeyboardInterrupt (Ctrl+c)
    """
   
    try:
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        proc._killed = False
        signal.signal(signal.SIGINT, lambda _signum, _frame: handleProcKill(proc))
        signal.signal(signal.SIGTERM, lambda _signum, _frame: handleProcKill(proc))
        time.sleep(1) #HACK Break if not there when launching fast custom tools on local host
        try:
            timer = None
            if timeout is not None:
                if isinstance(timeout, float):
                    timeout = (timeout-datetime.now()).total_seconds()
                    timer = Timer(timeout, proc.kill)
                    timer.start()
                else:
                    if timeout.year < datetime.now().year+1:
                        timeout = (timeout-datetime.now()).total_seconds()
                        timer = Timer(timeout, proc.kill)
                        timer.start()
            stdout, stderr = proc.communicate(None, timeout)
            if proc._killed:
                if timer is not None:
                    timer.cancel()
                return -1, ""
            if printStdout:
                stdout = stdout.decode('utf-8')
                stderr = stderr.decode('utf-8')
                if str(stdout) != "":
                    print(str(stdout))
                if str(stderr) != "":
                    print(str(stderr))
        except Exception as e:
            print(str(e))
            proc.kill()
            return -1, ""
        finally:
            if timeout is not None:
                if isinstance(timeout, float):
                    timer.cancel()
                else:
                    if timeout.year < datetime.now().year+1:
                        timer.cancel()
        return proc.returncode, stdout
    except KeyboardInterrupt as e:
        raise e


def performLookUp(domain):
    """
    Uses the socket module to get an ip from a domain.

    Args:
        domain: the domain to look for in dns

    Returns:
        Return the ip found from dns records, None if failed.
    """
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None


def loadCfg(cfgfile):
    """
    Load a json config file.
    Args:
        cfgfile: the path to a json config file
    Raises:
        FileNotFoundError if the given file does not exist
    Returns:
        Return the json converted values of the config file.
    """
    cf_infos = dict()
    try:
        with open(cfgfile, "r") as f:
            cf_infos = json.loads(f.read())
    except FileNotFoundError as e:
        raise e
    except json.JSONDecodeError as e:
        raise e
    return cf_infos

def getConfigFolder():
    from os.path import expanduser
    home = expanduser("~")
    config = os.path.join(home,".config/pollenisator-gui/")
    return config

def loadClientConfig():
    """Return data converted from json inside config/client.cfg
    Returns:
        Json converted data inside config/client.cfg
    """
    config = os.path.join(getConfigFolder(), "client.cfg")
    try:
        res = loadCfg(config)
        return res

    except:
        return {"host":"127.0.0.1", "port":"5000", "https":"False"}

def saveClientConfig(configDict):
    """Saves data in configDict to config/client.cfg as json
    Args:
        configDict: data to be stored in config/client.cfg
    """
    config_folder = getConfigFolder()
    try:
        os.makedirs(config_folder)
    except:
        pass
    configFile = os.path.join(config_folder, "client.cfg")
    with open(configFile, "w") as f:
        f.write(json.dumps(configDict))
        
def getValidMarkIconPath():
    """Returns:
         a validation mark icon path
    """
    p = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../../icon/done_tool.png")
    return p


def getBadMarkIconPath():
    """Returns:
         a bad mark icon path
    """
    p = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../../icon/cross.png")
    return p


def getWaitingMarkIconPath():
    """Returns:
         a waiting icon path
    """
    p = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../../icon/waiting.png")
    return p

def getIcon(name):
    """Returns : the path to an specified icon name
    """
    return os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../../icon/", name)
        
def getHelpIconPath():
    """Returns:
         a help icon path
    """
    p = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../../icon/help.png")
    return p


def getIconDir():
    """Returns:
        the icon directory path
    """
    p = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../../icon/")
    return p


def getMainDir():
    """Returns:
        the pollenisator main folder
    """
    p = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../../")
    return p

def drop_file_event_parser(event):
    """Parse event Callback of python-tkdnd on file drop event
    event.data is built weirdly:
        - Each file dropped in will be space-separated in a long string.
        - If a directory/file contains a space, the whole filename will be wrapped by curly brackets.
        - If a filename contains a curly brackets it will be escaped by backslashes and
        - If a filename contains an opening and a closing curly brackets, they might not be escaped
        - If a filename contains a space and a curly brackets, the filename is is not wrapped by curly brackets.
            but the space and curly brackets will be escaped by backslashes
        Returns:
            list of valid filename for python
        Exceptions:
            raise FileNotFoundError if a filename is not valid
    """
    parts = event.data.split(" ")
    data = []
    cumul = ""
    expect_closing_bracket = False
    for part in parts:
        if part.startswith("{") and not expect_closing_bracket:
            cumul += part[1:]+" "
            expect_closing_bracket = True
        elif part.endswith("\\"):
            cumul += part+" "
        elif part.endswith("}") and not part.endswith("\\}") and expect_closing_bracket:
            cumul += part[:-1]
            data.append(cumul)
            cumul = ""
            expect_closing_bracket = False
        else:
            if expect_closing_bracket:
                cumul += part+" "
            else:
                cumul += part
                data.append(cumul)
                cumul = ""
    # check existance 
    sanitized_path = []
    for d in data:
        # remove espacing as python does not expect spaces and brackets to be espaced
        d = d.replace("\\}", "}").replace("\\{", "{").replace("\\ "," ")
        if not os.path.exists(d):
            raise FileNotFoundError(d)
        sanitized_path.append(d)
    return sanitized_path
