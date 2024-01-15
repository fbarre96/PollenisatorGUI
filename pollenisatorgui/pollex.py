import sys
import shlex
import multiprocessing
from pollenisatorgui.core.components.logger_config import logger

def pollex():
    if len(sys.argv) <= 1:
        print("Usage : pollex [-v] <command to execute>")
        sys.exit(1)
    verbose = False
    if sys.argv[1] == "-v":
        verbose = True
        execCmd = shlex.join(sys.argv[2:])
    else:
        execCmd = shlex.join(sys.argv[1:])
    pollex_exec(execCmd, verbose)

def pollex_exec(execCmd, verbose=False):
    """Send a command to execute for pollenisator-gui running instance
    """
    
    bin_name = shlex.split(execCmd)[0]
    if bin_name in ["echo", "print", "vim", "vi", "tmux", "nano", "code", "cd", "ls","pwd", "cat", "export"]:
        sys.exit(-1)
    import os
    import shutil
    import tempfile
    import time
    from pollenisatorgui.core.components.apiclient import APIClient
    from pollenisatorgui.pollenisator import consoleConnect, parseDefaultTarget
    import pollenisatorgui.core.components.utils as utils

    cmdName = os.path.splitext(os.path.basename(execCmd.split(" ")[0]))[0]
    apiclient = APIClient.getInstance()
    apiclient.tryConnection()
    res = apiclient.tryAuth()
    if not res:
        consoleConnect()
    res = apiclient.getDesiredOutputForPlugin(execCmd, "auto-detect")
    (success, data) = res
    if not success:
        print(msg)
        consoleConnect()
    res = apiclient.getDesiredOutputForPlugin(execCmd, "auto-detect")
    (success, data) = res
    if not success:
        print(msg)
        return
    cmdName +="::"+str(time.time()).replace(" ","-")
    default_target = parseDefaultTarget(os.environ.get("POLLENISATOR_DEFAULT_TARGET", ""))
    if default_target.get("tool_iid") is not  None:
        apiclient.setToolStatus(default_target.get("tool_iid"), ["running"])
    
    if not success:
        print("ERROR : "+data)
        return
    if not data:
        print("ERROR : An error as occured : "+str(data))
        return
    comm = data["command_line_options"]
    plugin_results = data["plugin_results"]
    if (verbose):
        print("INFO : Matching plugins are "+str(data["plugin_results"]))
    
    tmpdirname = tempfile.mkdtemp() ### HACK: tempfile.TemporaryDirectory() gets deleted early because a fork occurs in execute and atexit triggers.
    for plugin,ext in plugin_results.items():
        outputFilePath = os.path.join(tmpdirname, cmdName) + ext
        comm = comm.replace(f"|{plugin}.outputDir|", outputFilePath)
    if (verbose):
        print("Executing command : "+str(comm))
        print("output should be in "+str(outputFilePath))
    queue = multiprocessing.Queue()
    queueResponse = multiprocessing.Queue()
    #if comm.startswith("sudo "):
    #    returncode = utils.execute_no_fork(comm, None, True, queue, queueResponse, cwd=tmpdirname)
    #else:
    try:
        returncode = utils.execute(comm, None, queue, queueResponse, cwd=tmpdirname, printStdout=True)
    except KeyboardInterrupt:
        logger.debug("pollex KeyboardInterrupt for comm "+str(comm))
    except Exception as e:
        logger.debug("pollex Exception for comm "+str(comm)+" "+str(e))
    queue.put("kill", block=False)
    if len(plugin_results) == 1 and "Default" in plugin_results:
        if (verbose):
            print("INFO : Only default plugin found")
        response = input("No plugin matched, do you want to use default plugin to log the command and stdout ? (Y/n) :")
        if str(response).strip().lower() == "n":
            shutil.rmtree(tmpdirname)
            return
    logger.debug("pollex detect plugins "+str(plugin_results))
    atLeastOne = False
    error = ""
    for plugin,ext in plugin_results.items():
        outputFilePath = os.path.join(tmpdirname, cmdName) + ext
        if not os.path.exists(outputFilePath):
            if os.path.exists(outputFilePath+ext):
                outputFilePath+=ext
            else:
                print(f"ERROR : Expected file was not generated {outputFilePath}")
                error = "ERROR : Expected file was not generated"
                continue
        print(f"INFO : Uploading results {outputFilePath}")
        msg = apiclient.importExistingResultFile(outputFilePath, plugin, default_target, comm)
        print(msg)
        atLeastOne = True
    if not atLeastOne:
        notes = b""
        while not queueResponse.empty():
            q = queueResponse.get(block=False)
            if q:
                if isinstance(q, str):
                    notes += q.encode()
        apiclient.setToolStatus(default_target.get("tool_iid"), ["error"], error+"\nSTDOUT:\n"+notes.decode())
    shutil.rmtree(tmpdirname)
