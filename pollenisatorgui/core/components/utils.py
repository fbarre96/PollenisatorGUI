"""Provide useful functions"""
import multiprocessing
from pathlib import Path
import select
import sys
import os
import socket
import subprocess
import time
from datetime import datetime
from threading import Timer
import json
from typing import Tuple
from netaddr import IPNetwork
import pty
from netaddr.core import AddrFormatError
from bson import ObjectId
import signal
from shutil import which
import shlex
import psutil

from pollenisatorgui.core.components.logger_config import logger


from os.path import expanduser
settings = None



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

    def decode_object(self, dct, max_depth=4):
        if isinstance(dct, dict):
            for k,v in dct.items():
                dct[k] = self.decode_object(v, max_depth-1)
        elif isinstance(dct, list):
            for i, v in enumerate(dct):
                dct[i] = self.decode_object(v, max_depth-1)
        elif isinstance(dct, str):
            if dct.startswith("ObjectId|"):
                return ObjectId(dct.split("|")[1])
            try:
                return datetime.strptime(dct, '%d/%m/%Y %H:%M:%S')
            except ValueError:
                return dct
        else:
            return dct
        return dct

    def object_hook(self, dct):
        return self.decode_object(dct)

def cacheSettings():
    """
    Cache the settings in a file.
    """
    global settings
    if settings is None:
        from pollenisatorgui.core.components.settings import Settings
        settings = Settings()
    return settings

def load_local_settings():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    confdir = os.path.join(dir_path, "../../config/settings.cfg")
    local_settings = {}
    try:
        with open(confdir, mode="r") as f:
            local_settings = json.loads(f.read())
    except:
        pass
    return local_settings

def save_local_settings(local_settings):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    confdir = os.path.join(dir_path, "../../config/settings.cfg")
    with open(confdir, "w") as f:
        f.write(json.dumps(local_settings))


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
    from pollenisatorgui.core.models.tool import Tool
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

def dateToString(date):
    """Converts a date to a string with format '%d/%m/%Y %H:%M:%S'
    Args:
        datestring: Returns the str if the given datetime is successfully converted, None otherwise"""
    ret = None
    if isinstance(date, datetime):
        ret = date.strftime('%d/%m/%Y %H:%M:%S')
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
    if isinstance(dated, str):
        date_start = stringToDate(dated)
    else:
        date_start = dated
    if isinstance(datef, str):
        date_end = stringToDate(datef)
    else:
        date_end = datef
    if date_start is None or date_end is None:
        return False
    return today > date_start and date_end > today

def handleProcKill(proc):
    logger.debug(f"Utils execute: handleProcKill {proc}")
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    proc._killed = True

def check_pid(pid):        
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def read_and_forward_pty_output(fd, child_pid, queue, queueResponse, printStdout):
    max_read_bytes = 1024 * 20
    continue_reading = True
    while continue_reading:
        time.sleep(0.01)
        if queue is not None and queue.qsize() > 0:
            key = queue.get(block=False)
            if key == "kill":
                parent = psutil.Process(child_pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
                break
            else:
                try:
                    os.write(fd, key.encode())
                except OSError:
                    pass
        if fd:
            (data_ready, _, _) = select.select([fd], [], [], 0.5)
            if data_ready:
                try:
                    output = os.read(fd, max_read_bytes).decode(
                        errors="ignore"
                    )
                
                    output = output.replace("\r","")
                    if queue is not None:
                        if "Y/n" in output:
                            queue.put("Y\n", block=False)
                        elif "y/N" in output:
                            queue.put("N\n", block=False)
                    if printStdout:
                        print(output)
                    if queueResponse is not None:
                        queueResponse.put(output, block=False)
                except OSError:
                    break
    if fd:
        os.close(fd)
    try:
        if queue:
            while queue.qsize() > 0:
                queue.get(block=False)
            queue.close()
            queue.join_thread()
        if queueResponse:
            while queueResponse.qsize() > 0 and queueResponse.empty() is False:
                queueResponse.get(block=False)
            queueResponse.close()
    except Exception as e:
        logger.error(f"Utils execute: read_and_forward_pty_output {e}")
    continue_reading = False
    return

def execute(command, timeout=None, queue=None, queueResponse=None, cwd=None, printStdout=False):
    """
    Execute a bash command and print output

    Args:
        command: A bash command
        timeout: a date in the futur when the command will be stopped if still running or None to not use this option, default as None.

    Returns:
        Return the return code of this command

    Raises:
        Raise a KeyboardInterrupt if the command was interrupted by a KeyboardInterrupt (Ctrl+c)
    """
    if isinstance(timeout, int):
        timeout = float(timeout)
    elif isinstance(timeout, float):
        timeout = timeout
    elif timeout is not None:
        if timeout.year < datetime.now().year+1:
            timeout = (timeout-datetime.now()).total_seconds()
        else:
            timeout = None
    
    (child_pid, fd) = pty.fork()
    if child_pid == 0:
        try:
            proc = subprocess.run(
                command, shell=True, cwd=cwd, timeout=timeout) #, preexec_fn=os.setsid
            sys.exit(0)
        except subprocess.TimeoutExpired:
            logger.debug("Timeout expired for command "+str(command))
            sys.exit(-1)
        except Exception as e:
            logger.debug("Exception occured for command "+str(command))
            sys.exit(1)
        finally:
            logger.debug("Exit finally for command "+str(command))
            sys.exit(0)
    else:
        p = multiprocessing.Process(target=read_and_forward_pty_output, args=[fd, child_pid, queue, queueResponse, printStdout])
        p.start()
        p.join()
    info = os.waitpid(child_pid, 0)
    try:
        if os.WIFEXITED(info[1]):
            returncode = os.WEXITSTATUS(info[1])
        else:
            returncode = -1
    except Exception as e:
        return -1
    return returncode




def execute_no_fork(command, timeout=None, printStdout=True, queue=None, queueResponse=None, cwd=None):
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
        time.sleep(1) #HACK Break if not there when launching fast custom tools on local host for unknown reason

        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, cwd=cwd)
        proc._killed = False
        signal.signal(signal.SIGINT, lambda _signum, _frame: handleProcKill(proc))
        signal.signal(signal.SIGTERM, lambda _signum, _frame: handleProcKill(proc))
        try:
            timer = None
            if timeout is not None:
                if isinstance(timeout, int):
                    timeout = float(timeout)
                if isinstance(timeout, float):
                    timer = Timer(timeout, proc.kill)
                    timer.start()
                    logger.debug("Utils execute: timer start "+str(timeout))
                else:
                    if timeout.year < datetime.now().year+1:
                        timeout = (timeout-datetime.now()).total_seconds()
                        timer = Timer(timeout, proc.kill)
                        timer.start()
                        logger.debug("Utils execute: timer start "+str(timeout))
                    else:
                        timeout = None
            logger.debug(f"Utils execute: timeout:{timeout} command:{command}")
            output = b""
            os.set_blocking(proc.stdout.fileno(), False)
            os.set_blocking(proc.stdin.fileno(), False)
            while proc.poll() is None and queue is not None and queueResponse is not None:
                if queue is not None and queue.qsize() > 0:
                    print("queue not empty")
                    key = queue.get(block=False)
                    if not key:
                        continue
                    proc.stdin.write(key.encode())
                    data = proc.stdout.read()
                    queueResponse.put(data)
                    time.sleep(3)
            stdout, stderr = proc.communicate(None, timeout)
            if queueResponse is not None:
                queueResponse.put(stdout)
            if proc._killed:
                logger.debug(f"Utils execute: command killed command:{command}")
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
            import traceback
            logger.debug(f"Utils execute: command ended with exception {repr(e)}")
            traceback.print_exc(file=sys.stdout)
            print(repr(e))
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
        with open(cfgfile, mode="r") as f:
            cf_infos = json.loads(f.read())
    except FileNotFoundError as e:
        raise e
    except json.JSONDecodeError as e:
        raise e
    return cf_infos

def getConfigFolder():
    home = expanduser("~")
    config = os.path.join(home,".config/pollenisator-gui/")
    return config

def getDataFolder():
    home = expanduser("~")
    data = os.path.join(home,".pollenisator-gui/results/")
    os.makedirs(data, exist_ok=True)
    return data

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
    with open(configFile, mode="w") as f:
        f.write(json.dumps(configDict))
  


def getLocalDir():
    """Returns:
        the pollenisator local folder
    """
    p = getMainDir()+"local/"
    return p

def getExportDir():
    """Returns:
        the pollenisator export folder
    """
    p = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../../exports/")
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

def openPathForUser(path, folder_only=False):
    path_to_open = os.path.dirname(path) if folder_only else path
    path_to_open = os.path.normpath(path_to_open)
    cmd = ""
    if which("xdg-open"):
        cmd = "xdg-open "+path_to_open
    elif which("explorer"):
        cmd = "explorer "+path_to_open
    elif which("open"):
        cmd = "open "+path_to_open
    if cmd != "":
        subprocess.Popen(shlex.split(cmd))
    else: # windows
        try: 
            os.startfile(path_to_open)
        except Exception:
            return False
    return True

# def executeInExternalTerm(command, with_bash=True, default_target=None):
#     from pollenisatorgui.core.components.settings import Settings
#     settings = Settings()
#     favorite = settings.getFavoriteTerm()
#     if favorite is None:
#         tk.messagebox.showerror(
#             "Terminal settings invalid", "None of the terminals given in the settings are installed on this computer.")
#         return False
#     if which(favorite) is not None:
#         env = {}
#         if default_target is not None:
#             env["POLLENISATOR_DEFAULT_TARGET"] = default_target
#         env = {**os.environ, **env}
#         terms = settings.getTerms()
#         terms_dict = {}
#         for term in terms:
#             terms_dict[term.split(" ")[0]] = term
#         command_term = terms_dict.get(favorite, None)
#         if command_term is not None:
#             if not command_term.endswith(" "):
#                 command_term += " "
#             command_term += command
#             print(command_term)
#             subprocess.Popen(command_term, shell=True, env=env, cwd=getExportDir())
#         else:
#             tk.messagebox.showerror(
#                 "Terminal settings invalid", "Check your terminal settings")
#     else:
#         tk.messagebox.showerror(
#             "Terminal settings invalid", f"{favorite} terminal is not available on this computer. Choose a different one in the settings module.")
#     return True

def which_expand_aliases(whats):
    whats = list(set(whats))
    res = expand_alias(shlex.join(whats))
    if res is None:
        return res
    aliases = {}
    for i, result in enumerate(res.split("\n")):
        if "not found" in result:
            aliases[whats[i]] = None
        elif "aliased to " in result:
            aliases[whats[i]] = result.split("aliased to ")[1].strip()
        else:
            aliases[whats[i]] = result
    return aliases

def which_expand_alias(what):
    res = which(what)
    if res is not None:
        return res
    stdout = expand_alias(what)
    if stdout is None:
        return None
    if "not found" in stdout:
        return None
    elif "aliased to " in stdout:
        return stdout.split("aliased to ")[1].strip()
    else:
        return stdout.strip()
    
def checkPaths(appnames):
    if isinstance(appnames, str):
        appnames = [appnames]
    for appname in appnames:
        path = which_expand_alias(appname)
        if path is not None:
            return True, path
    return False, "App name not found, create an alias or install it. ("+", ".join(appnames)+" were tested)"

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

def getPreferedShell() -> Tuple[str, str]:
    """
    Return the prefered shell of the user and the rc_file if configured.
    The search order is:
        1. the terminal in the local settings (key = terminal)
        2. the SHELL environment variable
        3. ZSH if the ZSH environment variable is set
        4. /bin/bash
    
    Then , the rc file is searched in the local settings (key = rc_file) or in the home directory of the user .$shell_name.rc

    Returns:
        Tuple[str, str]: the shell and the rc file path
    """
    local_settings = load_local_settings()
    is_there_zsh = os.environ.get("ZSH",None) is not None or os.path.isfile("/usr/bin/zsh")
    default_shell = "zsh" if is_there_zsh else "/bin/bash"

    terminal = local_settings.get("terminal", os.environ.get("SHELL",default_shell))
    rc_file = local_settings.get("rc_file", "")
    if rc_file == "":
        home = expanduser("~")
        rc_file = os.path.join(home,"."+os.path.basename(terminal)+"rc") # rc file is not loaded automatically
    return terminal, rc_file

def expand_alias(what):
    shell, rcfile = getPreferedShell()
    proc = subprocess.run(f"source {rcfile} && which {what}", executable=shell, shell=True, stdout=subprocess.PIPE)
    if proc.returncode == 0 or proc.returncode == 1:
        stdout = proc.stdout.decode("utf-8")
        return stdout.strip()
    return None

def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True