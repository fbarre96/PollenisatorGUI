import re
import sys
import shlex
import multiprocessing
from pollenisatorgui.core.components.logger_config import logger
from pollenisatorgui.core.components.utils import getDataFolder

def pollex():
    if len(sys.argv) <= 1:
        print("Usage : pollex [-v] [--checkinstance <checkinstance_id> | <Plugin name> <command options> | <command to execute>]")
        sys.exit(1)
    verbose = False
    if sys.argv[1] == "-v":
        verbose = True
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
        if sys.argv[1] == "-v":
            execCmd = shlex.join(sys.argv[2:])
        else:
            execCmd = shlex.join(sys.argv[1:])
    output = pollex_exec(execCmd, verbose)
    if output is not None:
        print("Result file : "+str(output))

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
        # Check if we have a current pentest configured before asking for one
        current_pentest = apiclient.getCurrentPentest()
        ask_pentest = not current_pentest or current_pentest.strip() == ""
        consoleConnect(askPentest=ask_pentest)
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
    results_folder = getDataFolder() ### HACK: tempfile.TemporaryDirectory() gets deleted early because a fork occurs in execute and atexit triggers.
    script_path = os.path.normpath(os.path.join(results_folder, script_name))
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
    from pollenisatorgui.core.components.apiclient import APIClient
    from pollenisatorgui.pollenisator import consoleConnect, parseDefaultTarget
    from datetime import datetime
    import pollenisatorgui.core.components.utils as utils

    cmdName = os.path.splitext(os.path.basename(bin_name))[0]
    apiclient = APIClient.getInstance()
    apiclient.tryConnection()
    res = apiclient.tryAuth()
    if not res:
        consoleConnect()
    if apiclient.isConnected() is False or apiclient.getCurrentPentest() == "":
        return
    res = apiclient.getDesiredOutputForPlugin(execCmd, "auto-detect")
    (success, data) = res
    if not success:
        print(data)
        return
    cmdName += "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    default_target = parseDefaultTarget(os.environ.get("POLLENISATOR_DEFAULT_TARGET", ""))
    tools_iids = default_target.get("tool_iid") 
    if tools_iids is not None:
        if not isinstance(tools_iids, list):
            tools_iids = [tools_iids]
        for tool_iid in tools_iids:
            apiclient.setToolStatus(tool_iid, ["running"])
    
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

    files_attached = re.findall(r'\|file\_[a-f0-9\-]+\|', comm)
    for f in files_attached:
        file_id = f.replace("|file_", "").replace("|", "")
        file_path = apiclient.downloadById("file", file_id, file_id, "/tmp/"+file_id)
        comm = comm.replace(f"|file_{file_id}|", file_path)
    
    result_dir = getDataFolder() 
    
    for plugin, plugin_data in plugin_results.items():
        ext = plugin_data.get("expected_extension", ".log.txt")
    
        outputFileDir= os.path.join(result_dir, os.path.splitext(plugin)[0])
        os.makedirs(outputFileDir, exist_ok=True)
        outputFilePath = os.path.join(outputFileDir, cmdName) + ext
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
        # getcwd is needed to have a valid cwd in case of relative paths in the command (filepath to a userlist for example)
        returncode = utils.execute(comm, None, queue, queueResponse, cwd=os.getcwd(), printStdout=True)
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
            return
    logger.debug("pollex detect plugins "+str(plugin_results))
    atLeastOne = False
    error = ""
    for plugin, plugin_data in plugin_results.items():
        ext = plugin_data.get("expected_extension", ".log.txt")
        outputFilePath = os.path.join(result_dir, os.path.splitext(plugin)[0], cmdName) + ext
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
        for tool_iid in tools_iids:
            apiclient.setToolStatus(tool_iid, ["error"], error+"\nSTDOUT:\n"+notes.decode())
    return outputFilePath
