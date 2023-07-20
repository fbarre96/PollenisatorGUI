import sys
import shlex


def pollex():
    """Send a command to execute for pollenisator-gui running instance
    """
    verbose = False
    if len(sys.argv) <= 1:
        print("Usage : pollex [-v] <command to execute>")
        sys.exit(1)
    if sys.argv[1] == "-v":
        verbose = True
        execCmd = shlex.join(sys.argv[2:])
    else:
        execCmd = shlex.join(sys.argv[1:])
    bin_name = shlex.split(execCmd)[0]
    if bin_name in ["echo", "print", "vim", "vi", "tmux", "nano", "code", "cd", "pwd", "cat", "export"]:
        return
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
    cmdName +="::"+str(time.time()).replace(" ","-")
    res = apiclient.getDesiredOutputForPlugin(execCmd, "auto-detect")
    (success, data) = res
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
    returncode = utils.execute(comm, None, cwd=tmpdirname, printStdout=True)
    if len(plugin_results) == 1 and "Default" in plugin_results:
        if (verbose):
            print("INFO : Only default plugin found")
        response = input("No plugin matched, do you want to use default plugin to log the command and stdout ? (Y/n) :")
        if str(response).strip().lower() == "n":
            shutil.rmtree(tmpdirname)
            return
    for plugin,ext in plugin_results.items():
        outputFilePath = os.path.join(tmpdirname, cmdName) + ext
        if not os.path.exists(outputFilePath):
            if os.path.exists(outputFilePath+ext):
                outputFilePath+=ext
            else:
                print(f"ERROR : Expected file was not generated {outputFilePath}")
                continue
        print(f"INFO : Uploading results {outputFilePath}")
        msg = apiclient.importExistingResultFile(outputFilePath, plugin, parseDefaultTarget(os.environ.get("POLLENISATOR_DEFAULT_TARGET", "")), comm)
        print(msg)
    shutil.rmtree(tmpdirname)
