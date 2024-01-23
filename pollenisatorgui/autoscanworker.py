"""worker module. Execute code and store results in database, files in the SFTP server.
"""

import errno
import os
import signal
import time
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import shutil
from pollenisatorgui.core.components.apiclient import APIClient
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.models.interval import Interval
from pollenisatorgui.core.models.tool import Tool
import threading
import sys

event_obj = threading.Event()


def sendKill(queue):
    queue.put("kill", block=False)

def executeTool(queue, queueResponse, apiclient, toolId, local=True, allowAnyCommand=False, setTimer=False, infos={}, logger_given=None, worker_name=""):
    """
     remote task
    Execute the tool with the given toolId on the given pentest name.
    Then execute the plugin corresponding.
    Any unhandled exception will result in a task-failed event in the class.

    Args:
        apiclient: the apiclient instance.
        toolId: the mongo Object id corresponding to the tool to execute.
        local: boolean, set the execution in a local context
    Raises:
        Terminated: if the task gets terminated
        OSError: if the output directory cannot be created (not if it already exists)
        Exception: if an exception unhandled occurs during the bash command execution.
        Exception: if a plugin considered a failure.
    """
    import logging
    import sys
    logging.basicConfig(filename='error.log', encoding='utf-8', level=logging.INFO)
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(handler)

    def handle_exception(exc_type, exc_value, exc_traceback):
        logger.debug("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            sys.exit(1)

        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        sys.exit(1)

    sys.excepthook = handle_exception
    #register signals
    signal.signal(signal.SIGTERM, lambda signum, sigframe: sendKill(queue))
    # Connect to given pentest
    logger.debug("executeTool: Execute tool locally:" +str(local)+" setTimer:"+str(setTimer)+" toolId:"+str(toolId))
    APIClient.setInstance(apiclient)
    toolModel = Tool.fetchObject({"_id":ObjectId(toolId)})
    logger.debug("executeTool: get command for toolId:"+str(toolId))
    command_dict = toolModel.getCommand()
    if command_dict is None and toolModel.text != "":
        command_dict = {"plugin":toolModel.plugin_used, "timeout":0}
    msg = ""
    success, data = apiclient.getCommandLine(toolId, toolModel.text)
    comm, fileext = data["comm_with_output"], data["ext"]
    logger.debug("executeTool: got command line for toolId:"+str(toolId))
    if not success:
        print(str(comm))
        logger.debug("Autoscan: Execute tool locally error in getting commandLine : "+str(toolId))
        toolModel.setStatus(["error"])
        sys.exit(1)
    
    outputRelDir = toolModel.getOutputDir(apiclient.getCurrentPentest())
    abs_path = os.path.dirname(os.path.abspath(__file__))
    toolFileName = toolModel.name+"_" + \
            str(time.time()) # ext already added in command
    outputDir = os.path.join(abs_path, "./results", outputRelDir)
    # Create the output directory
    try:
        os.makedirs(outputDir)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(outputDir):
            pass
        else:
            print(str(exc))
            logger.debug("Autoscan: Execute tool locally error in creating output directory : "+str(exc))
            toolModel.setStatus(["error"])
            sys.exit(1)
    outputPath = os.path.join(outputDir, toolFileName)
    comm = comm.replace("|outputDir|", outputPath)
    settings = Settings()
    my_commands = settings.local_settings.get("my_commands", {})
    bin_path = my_commands.get(toolModel.name)
    if bin_path is None:
        if utils.which_expand_alias(command_dict["bin_path"]):
            bin_path = command_dict["bin_path"]
        else:
            toolModel.setStatus(["error"])
            toolModel.notes = str(toolModel.name)+" : no binary path setted"
            logger.debug("Autoscan: Execute tool locally no bin path setted : "+str(toolModel.name))
            sys.exit(1)
    comm = bin_path + " " + comm
    toolModel.updateInfos({"cmdline":comm})
    if "timedout" in toolModel.status:
        timeLimit = None
    # Get tool's wave time limit searching the wave intervals
    elif toolModel.wave == "Custom commands" or (local and not setTimer):
        timeLimit = None
    else:
        timeLimit = getWaveTimeLimit()
    # adjust timeLimit if the command has a lower timeout
    if command_dict is not None and timeLimit is not None:
        timeLimit = min(datetime.now()+timedelta(0, int(command_dict.get("timeout", 0))), timeLimit)
    ##
    try:
        launchableToolId = toolModel.getId()
        name = worker_name
        toolModel.markAsRunning(name, infos)
        logger.debug(f"Mark as running tool_iid {launchableToolId}")
        logger.debug('Autoscan: TASK STARTED:'+toolModel.name)
        logger.debug("Autoscan: Will timeout at "+str(timeLimit))
        print(('TASK STARTED:'+toolModel.name))
        print("Will timeout at "+str(timeLimit))
        # Execute the command with a timeout
        returncode = utils.execute(comm, timeLimit, queue, queueResponse, cwd=outputDir)
        if returncode == -1:
            toolModel.setStatus(["timedout"])
            logger.debug("Autoscan: TOOL timedout at "+str(timeLimit))
            sys.exit(-1)
    except Exception as e:
        print(str(e))
        toolModel.setStatus(["error"])
        logger.debug("Autoscan: TOOL error "+str(e))
        return False, str(e)
    # Execute found plugin if there is one
    outputfile = outputPath+fileext
    plugin = "auto-detect" if command_dict["plugin"] == "" else command_dict["plugin"] 
    msg = apiclient.importToolResult(toolId, plugin, outputfile)
    if msg != "Success":
        #toolModel.markAsNotDone()
        print(str(msg))
        toolModel.setStatus(["error"])
        logger.debug("Autoscan: import tool result error "+str(msg))
        sys.exit(1)
          
    # Delay
    if command_dict is not None:
        print(msg)
    sys.exit(0)
    
def getWaveTimeLimit():
    """
    Return the latest time limit in which this tool fits. The tool should timeout after that limit

    Returns:
        Return the latest time limit in which this tool fits.
    """
    intervals = Interval.fetchObjects({})
    furthestTimeLimit = datetime.now()
    for intervalModel in intervals:
        if utils.fitNowTime(intervalModel.dated, intervalModel.datef):
            endingDate = intervalModel.getEndingDate()
            if endingDate is not None:
                if endingDate > furthestTimeLimit:
                    furthestTimeLimit = endingDate
    return furthestTimeLimit


