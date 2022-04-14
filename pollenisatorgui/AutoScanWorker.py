"""worker module. Execute code and store results in database, files in the SFTP server.
"""

from distutils import command
import errno
import os
import time
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from pollenisatorgui.core.Components.apiclient import APIClient
import pollenisatorgui.core.Components.Utils as Utils
from pollenisatorgui.core.Models.Interval import Interval
from pollenisatorgui.core.Models.Tool import Tool
from pollenisatorgui.core.Models.Command import Command

def executeCommand(apiclient, toolId, local=True, allowAnyCommand=False):
    """
     remote task
    Execute the tool with the given toolId on the given calendar name.
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
    # Connect to given calendar
    APIClient.setInstance(apiclient)
    toolModel = Tool.fetchObject({"_id":ObjectId(toolId)})
    command_dict = toolModel.getCommand()
    if command_dict is None and toolModel.text != "":
        command_dict = {"plugin":toolModel.plugin_used, "timeout":0}
    msg = ""
    success, comm, fileext = apiclient.getCommandLine(toolId)
    if not success:
        print(str(comm))
        toolModel.setStatus(["error"])
        return False, str(comm)
    
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
            toolModel.setStatus(["error"])
            return False, str(exc)
    outputDir = os.path.join(outputDir, toolFileName)
    comm = comm.replace("|outputDir|", outputDir)
    # Get tool's wave time limit searching the wave intervals
    if toolModel.wave == "Custom commands" or local:
        timeLimit = None
    else:
        timeLimit = getWaveTimeLimit(toolModel.wave)
    # adjust timeLimit if the command has a lower timeout
    if command_dict is not None and timeLimit is not None:
        timeLimit = min(datetime.now()+timedelta(0, int(command_dict.get("timeout", 0))), timeLimit)
    ##
    try:
        print(('TASK STARTED:'+toolModel.name))
        print("Will timeout at "+str(timeLimit))
        # Execute the command with a timeout
        returncode, stdout = Utils.execute(comm, timeLimit, True)
        if returncode == -1:
            toolModel.setStatus(["timedout"])
            return False, "timedout"
    except Exception as e:
        print(str(e))
        toolModel.setStatus(["error"])
        return False, str(e)
    # Execute found plugin if there is one
    outputfile = outputDir+fileext
    plugin = "auto-detect" if command_dict["plugin"] == "" else command_dict["plugin"] 
    msg = apiclient.importToolResult(toolId, plugin, outputfile)
    if msg != "Success":
        #toolModel.markAsNotDone()
        print(str(msg))
        toolModel.setStatus(["error"])
        return False, str(msg)
          
    # Delay
    if command_dict is not None:
        if float(command_dict.get("sleep_between", 0)) > 0.0:
            msg += " (will sleep for " + \
                str(float(command_dict.get("sleep_between", 0)))+")"
        print(msg)
        time.sleep(float(command_dict.get("sleep_between", 0)))
    return True, outputfile
    
def getWaveTimeLimit(waveName):
    """
    Return the latest time limit in which this tool fits. The tool should timeout after that limit

    Returns:
        Return the latest time limit in which this tool fits.
    """
    intervals = Interval.fetchObjects({"wave": waveName})
    furthestTimeLimit = datetime.now()
    for intervalModel in intervals:
        if Utils.fitNowTime(intervalModel.dated, intervalModel.datef):
            endingDate = intervalModel.getEndingDate()
            if endingDate is not None:
                if endingDate > furthestTimeLimit:
                    furthestTimeLimit = endingDate
    return furthestTimeLimit


