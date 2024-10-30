import sys
import shlex
import multiprocessing
from pollenisatorgui.core.components.logger_config import logger

def pollex():
    if len(sys.argv) <= 1:
        print("Usage : pollex [-v] [--checkinstance <checkinstance_id> | <Plugin name> <command options> | <command to execute>]")
        sys.exit(1)
    verbose = False
    if sys.argv[1] == "-v":
        verbose = True
        execCmd = shlex.join(sys.argv[2:])
    if "--checkinstance" in sys.argv:
        try:
            index_check = sys.argv.index("--checkinstance")
            script_checkinstance_id = sys.argv[index_check+1]
            pollscript_exec(script_checkinstance_id,  verbose)
            return
        except IndexError as e:
            print("ERROR : --checkinstance option must be followed by a checkinstance id")
            sys.exit(1)
    else:
        execCmd = shlex.join(sys.argv[1:])
    pollex_exec(execCmd, verbose)

def pollscript_exec(script_checkinstance_id, verbose=False):
    import os
    import tempfile
    import time
    import shutil
    from pollenisatorgui.core.components.apiclient import APIClient
    from pollenisatorgui.core.models.checkitem import CheckItem
    from pollenisatorgui.core.models.checkinstance import CheckInstance
    from bson import ObjectId
    from pollenisatorgui.pollenisator import consoleConnect, parseDefaultTarget
    import pollenisatorgui.core.components.utils as utils
    import importlib

    apiclient = APIClient.getInstance()
    apiclient.tryConnection()
    res = apiclient.tryAuth()
    if not res:
        consoleConnect()
    check_instance = CheckInstance.fetchObject({"_id":ObjectId(script_checkinstance_id)})
    if check_instance is None:
        print("ERROR : CheckInstance not found")
        return
    script_checkitem_id = check_instance.check_iid
    check_o = CheckItem.fetchObject({"_id":ObjectId(script_checkitem_id)})
    if check_o is None:
        print("ERROR : Check not found")
        return
    if check_o.check_type != "script":
        print("ERROR : Check is not a script check")
        return
    
    script_name = os.path.normpath(check_o.title).replace(" ", "_").replace("/", "_").replace("\\", "_")+".py"
    default_target = parseDefaultTarget(os.environ.get("POLLENISATOR_DEFAULT_TARGET", ""))
    tmpdirname = tempfile.mkdtemp() ### HACK: tempfile.TemporaryDirectory() gets deleted early because a fork occurs in execute and atexit triggers.
    script_path = os.path.normpath(os.path.join(tmpdirname, script_name))
    with open(script_path, "w") as f:
        f.write(check_o.script)
    spec = importlib.util.spec_from_file_location("pollenisatorgui.scripts."+str(script_name), script_path)
    script_module = importlib.util.module_from_spec(spec)
    sys.modules["pollenisatorgui.scripts."+str(script_name)] = script_module
    spec.loader.exec_module(script_module)
    data = check_instance.getData()
    data["default_target"] = str(check_instance.getId())
    success, res = script_module.main(APIClient.getInstance(), None, **data)
    if success:
        print(f"Script {script_name} finished.\n{res}")
    else:
        print(f"Script {script_name} failed.\n{res}")

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

    cmdName = os.path.splitext(os.path.basename(bin_name))[0]
    apiclient = APIClient.getInstance()
    apiclient.tryConnection()
    res = apiclient.tryAuth()
    if not res:
        consoleConnect()
    res = apiclient.getDesiredOutputForPlugin(execCmd, "auto-detect")
    (success, data) = res
    if not success:
        print(data)
        consoleConnect()
    res = apiclient.getDesiredOutputForPlugin(execCmd, "auto-detect")
    (success, data) = res
    if not success:
        print(data)
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
    local_settings = utils.load_local_settings()
    my_commands = local_settings.get("my_commands", {})
    path_to_check = set()
    bin_path = my_commands.get(bin_name, None)
    if bin_path is not None:
        path_to_check.add(bin_path)
    path_to_check.add(bin_name)
    plugin_results = data["plugin_results"]
    for plugin, plugin_data in plugin_results.items():
        if os.path.splitext(plugin)[0] in execCmd:
            path_to_check = path_to_check.union(plugin_data.get("common_bin_names", []))
    bin_path_found, result_msg = utils.checkPaths(list(path_to_check))
    if not bin_path_found:
        print("ERROR : "+result_msg)
        return
    new_bin_path = result_msg
    comm = data["command_line_options"].replace(bin_name, new_bin_path, 1)
    
    if (verbose):
        print("INFO : Matching plugins are "+str(data["plugin_results"]))
    
    tmpdirname = tempfile.mkdtemp() ### HACK: tempfile.TemporaryDirectory() gets deleted early because a fork occurs in execute and atexit triggers.
    for plugin, plugin_data in plugin_results.items():
        ext = plugin_data.get("expected_extension", ".log.txt")

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
    for plugin, plugin_data in plugin_results.items():
        ext = plugin_data.get("expected_extension", ".log.txt")
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
