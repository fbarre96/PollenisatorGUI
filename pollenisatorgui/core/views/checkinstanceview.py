"""View for checkitem object. Handle node in treeview and present forms to user when interacted with."""

import tkinter.ttk as ttk
import webbrowser
from customtkinter import *
from pollenisatorgui.core.application.dialogs.ChildDialogDefectView import ChildDialogDefectView
from pollenisatorgui.core.application.dialogs.ChildDialogProgress import ChildDialogProgress
from pollenisatorgui.core.application.dialogs.ChildDialogToast import ChildDialogToast
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.components.scriptmanager import ScriptManager
from pollenisatorgui.core.components.tag import TagInfos
from pollenisatorgui.core.controllers.checkinstancecontroller import CheckInstanceController
from pollenisatorgui.core.controllers.defectcontroller import DefectController
from pollenisatorgui.core.controllers.toolcontroller import ToolController
from pollenisatorgui.core.models.defect import Defect
from pollenisatorgui.core.views.checkinstancemultiview import CheckInstanceMultiView
from pollenisatorgui.core.views.defectview import DefectView
from pollenisatorgui.core.views.toolview import ToolView
from pollenisatorgui.core.views.viewelement import ViewElement
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.models.tool import Tool
import pollenisatorgui.core.components.utils as utils
from PIL import ImageTk, Image
from pollenisatorgui.core.components.logger_config import logger
from bson import ObjectId
import os
import tkinter as tk


class CheckInstanceView(ViewElement):
    """
    View for CheckInstanceView object. Handle node in treeview and present forms to user when interacted with.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory.
    """
    done_icon = 'checked.png'
    running_icon = 'running.png'
    not_done_icon = 'unchecked.png'
    icon = 'checklist.png'

    cached_icon = None
    cached_done_icon = None
    cached_running_icon = None
    cached_not_ready_icon = None

    multiview_class = CheckInstanceMultiView

    @classmethod
    def getStatusIcon(cls, status):
        if "todo" in status: # order is important as "done" is not_done but not the other way
            ui = cls.not_done_icon
            cache = cls.cached_not_ready_icon
            iconStatus = "not_done"
        elif "running" in status:
            ui = cls.running_icon
            cache = cls.cached_running_icon
            iconStatus = "running"
        else:
            cache = cls.cached_done_icon
            ui = cls.done_icon
            iconStatus = "done"
        if cache is None:
            from PIL import Image, ImageTk
            if iconStatus == "done":
                cls.cached_done_icon = utils.loadIcon(ui, resize=(16,16))
                return cls.cached_done_icon
            elif iconStatus == "running":
                cls.cached_running_icon =  utils.loadIcon(ui, resize=(16,16))
                return cls.cached_running_icon
            else:
                cls.cached_not_ready_icon =  utils.loadIcon(ui, resize=(16,16))
                return cls.cached_not_ready_icon
        return cache

    def getIcon(self, check_infos=None):
        """
        Load the object icon in cache if it is not yet done, and returns it

        Return:
            Returns the icon representing this object.
        """
        
        status = self.controller.getStatus()
        iconStatus = "todo"
        if "todo" in status or "" == status: # order is important as "done" is not_done but not the other way
            ui = self.__class__.not_done_icon
            cache = self.__class__.cached_not_ready_icon
            iconStatus = "not_done"
        elif "running" in status:
            ui = self.__class__.running_icon
            cache = self.__class__.cached_running_icon
            iconStatus = "running"
        elif "done" in status:
            cache = self.__class__.cached_done_icon
            ui = self.__class__.done_icon
            iconStatus = "done"
        # FIXME, always get triggered
        # if status == [] or iconStatus not in status :
        #     print("status is "+str(status)+ " or "+str(iconStatus)+" not in "+str(status))
        #     self.controller.setStatus([iconStatus])

        if cache is None:
            from PIL import Image, ImageTk
            if iconStatus == "done":
                self.__class__.cached_done_icon = utils.loadIcon(ui, resize=(16,16))
                return self.__class__.cached_done_icon
            elif iconStatus == "running":
                self.__class__.cached_running_icon =  utils.loadIcon(ui, resize=(16,16))
                return self.__class__.cached_running_icon
            else:
                self.__class__.cached_not_ready_icon =  utils.loadIcon(ui, resize=(16,16))
                return self.__class__.cached_not_ready_icon
        return cache

    def getStatus(self, check_infos=None):
        modelData = self.controller.getData()
        if modelData.get("status", "") == "done":
            status = "done"
        else:
            if check_infos is None:
                check_infos = self.controller.getCheckInstanceStatus()
            status = check_infos.get("status", "")
        if status == "":
            status = modelData.get("status", "")
        if status == "":
            status = "todo"
        return status

    def __init__(self, appTw, appViewFrame, mainApp, controller):
        """Constructor
        Args:
            appTw: a PollenisatorTreeview instance to put this view in
            appViewFrame: an view frame to build the forms in.
            mainApp: the Application instance
            controller: a CommandController for this view.
        """
        self.menuContextuel = None
        self.widgetMenuOpen = None
        
        super().__init__(appTw, appViewFrame, mainApp, controller)

    
            
    def openModifyWindow(self, **kwargs):
        """
        Creates a tkinter form using Forms classes. This form aims to update or delete an existing Command
        """
       
        self.form.clear()
        infos = self.controller.getCheckInstanceInfo()
        modelData = self.controller.getData()
        check_m = self.controller.getCheckItem()
        self._initContextualMenu()
        self.form.addFormHidden("parent", modelData.get("parent"))
        panel_top = self.form.addFormPanel(grid=True)
        
        
        #panet_top_sub = panel_top.addFormPanel(grid=True, row=3, column=0, columnspan=2)
        panel_top.addFormLabel("Target", row=0, column=0)
        panel_top.addFormButton(self.controller.target_repr, self.openTargetDialog, row=0, column=1, style="link.TButton", pady=5)
        panel_top.addFormLabel("Status", row=0, column=2)
        default_status = self.getStatus(infos)
        self.image_terminal = CTkImage(Image.open(utils.getIcon('terminal_small.png')))
        self.form_status = panel_top.addFormCombo("Status", ["todo", "running","done"], default=default_status, command=self.status_change, row=0, column=3, pady=5)
        #panet_top_sub.addFormButton("Attack", callback=self.attackOnTerminal, image=self.image_terminal, row=0, column=2)
        
        #if "commands" in check_m.check_type:

        self.buttonExecuteImage = CTkImage(Image.open(utils.getIcon('execute.png')))
        self.buttonQueueImage = CTkImage(Image.open(utils.getIcon('exec_cloud.png')))
        self.buttonRunImage = CTkImage(Image.open(utils.getIcon('terminal_small.png')))
        self.buttonDownloadImage = CTkImage(Image.open(utils.getIcon("download.png")))
        self.image_download = utils.loadIcon("download.png")
        self.image_reset = utils.loadIcon("reset_small.png")
        self.image_delete = utils.loadIcon("delete.png")
        self.image_defect = utils.loadIcon("defect.png")
        dict_of_tools_not_done = infos.get("tools_not_done", {})
        dict_of_tools_error = infos.get("tools_error", {})
        dict_of_tools_running = infos.get("tools_running", {})
        dict_of_tools_done = infos.get("tools_done", {})
        #create lambdas indirection for each button
        lambdas_lauch_tool_local = [self.launchToolLocalCallbackLambda(iid) for iid in dict_of_tools_not_done.keys()]
        lambdas_queue_tool_worker = [self.queueToolCallbackLambda(iid) for iid in dict_of_tools_not_done.keys()]
        lambdas_launch_tool_worker = [self.launchToolWorkerCallbackLambda(iid) for iid in dict_of_tools_not_done.keys()]
        lambdas_running = [self.peekToolCallbackLambda(iid) for iid in dict_of_tools_running.keys()]
        lambdas_running_stop = [self.stopToolCallbackLambda(iid) for iid in dict_of_tools_running.keys()]
        lambdas_done = [self.downloadToolCallbackLambda(iid) for iid in dict_of_tools_done.keys()]
        lambdas_del = [self.deleteToolCallbackLambda(iid) for iid in dict_of_tools_done.keys()]
        lambdas_error_reset = [self.resetToolCallbackLambda(iid) for iid in dict_of_tools_error.keys()]
        lambdas_defect_create = [self.createDefectCallbackLambda(iid) for iid in dict_of_tools_done.keys()]
        lambdas_reset = [self.resetToolCallbackLambda(iid) for iid in dict_of_tools_done.keys()]
        datamanager = DataManager.getInstance()
        apiclient = APIClient.getInstance()
        
        if dict_of_tools_not_done:
            self.form.addFormSeparator()
            self.form.addFormLabel("Command suggestions", font_size=20, side=tk.TOP, anchor=tk.W)
            formCommands = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5, grid=True)
            row=0
            for tool_iid, tool_string in dict_of_tools_not_done.items():
                success, data = apiclient.getCommandLine(tool_iid)
                if success:
                    comm, fileext = data["comm"], data["ext"]
                    toolModel =  Tool.fetchObject({"_id":ObjectId(tool_iid)})
                    if toolModel is None:
                        continue
                    formCommands.addFormButton(toolModel.name, self.openToolDialog, row=row, column=0, style="link.TButton", infos={"iid":tool_iid})
                    form_str = None
                    if success:
                        commandModel = datamanager.get("commands", toolModel.command_iid)
                        form_str_bin= formCommands.addFormStr("bin_path", "", commandModel.bin_path, status="disabled", width=80, row=row, column=1)
                        form_str= formCommands.addFormStr("commandline", "", comm, width=550, row=row, column=2)

                    formCommands.addFormButton("Execute", lambdas_lauch_tool_local[row], row=row, column=3, width=0, infos= {'formstr': form_str, "bin":form_str_bin}, image=self.buttonExecuteImage)
                    ready, msg = self.mainApp.scanManager.is_ready_to_queue(str(tool_iid))
                    if ready:
                        formCommands.addFormButton("Queue", lambdas_queue_tool_worker[row], row=row, column=4, width=0, infos= {'formstr': form_str, "bin":form_str_bin}, 
                                            state="normal" if ready else "disabled", image=self.buttonQueueImage)
                    ready, msg = self.mainApp.scanManager.is_ready_to_run_tasks()
                    if ready:
                        formCommands.addFormButton("Worker execute", lambdas_launch_tool_worker[row], row=row, column=5, width=0, infos= {'formstr': form_str, "bin":form_str_bin}, 
                                            state="normal" if ready else "disabled", image=self.buttonQueueImage)
                row+=1
        if dict_of_tools_running:
            formCommands = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5, grid=True)
            row=0
            for tool_iid, tool_string in dict_of_tools_running.items():
                formCommands.addFormSeparator(row=row, column=0, columnspan=3)
                formCommands.addFormButton(tool_string, self.openToolDialog, row=row*2+1, column=0,style="link.TButton", infos={"iid":tool_iid})
                tool_model = datamanager.get("tools", tool_iid)
                form_str = formCommands.addFormStr("commandline", "", tool_model.text, status="disabled", width=550, row=row*2+1, column=2)
                formCommands.addFormButton("Peek", lambdas_running[row], row=row*2+1, column=3, width=0, image=self.buttonRunImage)
                formCommands.addFormButton("Stop", lambdas_running_stop[row], row=row*2+1, column=4,  width=0, fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
                row+=1
        if dict_of_tools_done:
            self.form.addFormSeparator()
            self.form.addFormLabel("Results", font_size=20, side=tk.TOP, anchor=tk.CENTER)
            formCommands = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5)
            row=0
            for tool_iid, tool_data in dict_of_tools_done.items():
                tool_m = Tool(tool_data)
                tool_panel = formCommands.addFormPanel(side=tk.TOP, fill=tk.X, pady=0)
                #tool_panel.addFormSeparator(fill=tk.X)
                tool_panel.addFormButton(tool_m.getDetailedString(), self.openToolDialog, side=tk.TOP, anchor=tk.W, style="link.TButton", infos={"iid":tool_iid})
                tags = ToolController(tool_m).getTags()
                if tags:
                    for tag in tags:
                        tag = TagInfos(tag)
                        registeredTags = Settings.getTags()
                        keys = list(registeredTags.keys())
                        column = 0
                        item_no = 0
                        
                        s = ttk.Style(self.mainApp)
                        if tag.color is None or tag.color == "transparent":
                            tag_color = registeredTags.get(tag.name, {}).get("color"," gray97")
                        else:
                            tag_color = tag.color
                        try: # CHECK IF COLOR IS VALID
                            CTkLabel(self.mainApp, fg_color=tag_color)
                        except tk.TclError as e:
                            #color incorrect
                            tag_color = "gray97"
                        s.configure(""+tag_color+".Default.TLabel", background=tag_color, foreground="black", borderwidth=1, bordercolor="black")
                        tool_panel.addFormLabel(tag, text=tag.name, side="top", padx=1, pady=0)
                        column += 1
                        item_no += 1
                        if column == 4:
                            column = 0
                        if column == 0:
                            tool_panel = tool_panel.addFormPanel(pady=0,side=tk.TOP, anchor=tk.W)
                tool_panel.addFormText(str(tool_iid)+"_notes", "", default=tool_m.notes,  side=tk.LEFT, height=min(26*+len(tool_m.notes.split("\n")), 200))
                action_panel = tool_panel.addFormPanel(side=tk.LEFT, anchor=tk.CENTER, fill=tk.BOTH, grid=True)
                action_panel.rowconfigure(0, 2)
                action_panel.addFormButton("", lambdas_done[row], image=self.image_download, style="icon.TButton", tooltip="Download original result file generated by the tool")
                action_panel.addFormButton("", lambdas_defect_create[row],  image=self.image_defect, style="icon.TButton", tooltip="Create a security defect instance with this tool notes", column=1)
                action_panel.addFormButton("", lambdas_reset[row], image=self.image_reset, style="icon.TButton", tooltip="Reset the tool data. All data will be lost.", column=2)
                action_panel.addFormButton("", lambdas_del[row], image=self.image_delete, style="icon.TButton", tooltip="Delete the tool data. Tool results too.", column=3)
                row+=1
        if dict_of_tools_error:
            formCommands = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5, grid=True)
            row=0
            formCommands.addFormSeparator(row=row, column=0, columnspan=3)
            for tool_iid, tool_data in dict_of_tools_error.items():
                tool_m = Tool(tool_data)
                formCommands.addFormButton(tool_m.getDetailedString(), self.openToolDialog, row=row,column=0,  style="link.TButton", infos={"iid":tool_iid})
                
                formCommands.addFormText(str(tool_iid)+"_notes", "", default=tool_m.notes,  row=row, column=1 , height=min(26*+len(tool_m.notes.split("\n")), 200))
                formCommands.addFormButton("Reset", lambdas_error_reset[row], row=row, column=2,  width=0, fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
                row+=1
        
        upload_panel = self.form.addFormPanel(side=tk.TOP, fill=tk.X,pady=5, height=0)
        upload_panel.addFormLabel("Upload additional scan results", side=tk.LEFT, anchor=tk.N, pady=5)
        self.form_file = upload_panel.addFormFile("upload_tools", height=2, side=tk.LEFT, pady=5, command=self.mod_file_callback)
        self.upload_btn = upload_panel.addFormButton("Upload", callback=self.upload_scan_files, state="disabled", anchor=tk.N, side=tk.LEFT, pady=5)

        #for command, status in infos.get("tools_status", {}).items():
        if check_m and "script" in check_m.check_type:
            formTv = self.form.addFormPanel(side=tk.TOP, fill=tk.X, pady=5)
            formTv.addFormLabel("Script", side=tk.LEFT)
            self.textForm = formTv.addFormStr("Script", ".+", check_m.script)
            self.execute_icon = CTkImage(Image.open(utils.getIcon("execute.png")))
            self.edit_icon = CTkImage(Image.open(utils.getIcon("view_doc.png")))
            formTv.addFormButton("View", lambda _event: self.viewScript(check_m.script), image=self.edit_icon)
            formTv.addFormButton("Exec", lambda _event: self.execScript(check_m.script), image=self.execute_icon)
        self.defect_titles = {}
        for defect in check_m.defect_tags:
            d = apiclient.findInDb("pollenisator", "defects", {"_id":ObjectId(defect[1])}, False)
            if d is not None:
                if d.get("language", "") == self.mainApp.settings.db_settings.get("lang", "en"):
                    self.defect_titles[d.get("title")] = d
        self.form.addFormSeparator(fill=tk.X, pady=5)
        formDefects = self.form.addFormPanel(fill=tk.X, pady=5, grid=True)
        formDefects.addFormLabel("Add Security defects", pady=5,row=1)
        self.combo_defect = formDefects.addFormCombo("Defect", list(self.defect_titles.keys())+["Search other defect"], default=None, width=300, row=1, column=1)
        formDefects.addFormButton("Confirm", callback=self.defect_add_callback, row=1, column=2)
        self.form.addFormSeparator(fill=tk.X, pady=5)
        panel_detail = self.form.addFormPanel(grid=True, fill=tk.X)
        panel_detail.columnconfigure(1, weight=2)
        panel_detail.addFormLabel("Description", row=1, column=0)
        panel_detail.addFormText("Description", r"", default=check_m.description if check_m and check_m.description != "" else "No description", height=100, state="disabled", row=1, column=1, pady=5)
        panel_detail.addFormLabel("Notes", row=2, column=0)
        panel_detail.addFormText("Notes", r"", default=modelData.get("notes", ""), row=2, column=1, pady=5)
        self.completeModifyWindow(addTags=False)
        
    def mod_file_callback(self):
        if self.form_file.get_paths():
            self.upload_btn.configure(state="normal")
        else:
            self.upload_btn.configure(state="disabled")
    
    def attackOnTerminal(self, event=None):
        #import pollenisatorgui.modules.terminal as terminal
        #terminal.Terminal.openTerminal(str(self.controller.getDbId()))
        self.mainApp.open_terminal(str(self.controller.getDbId()), self.controller.target_repr)

    def defect_add_callback(self, event=None):
        defect_title = self.combo_defect.getValue()
        if defect_title == "Search other defect":
            d = Defect({"target_type":self.controller.model.target_type, "target_id":self.controller.model.target_iid})
            ChildDialogDefectView(self.mainApp, "Search defect", self.mainApp.settings, force_insert=True)
        else:
            defect = self.defect_titles.get(defect_title)
            if defect is not None:
                defect["target_type"] = self.controller.model.target_type
                defect["target_id"] = self.controller.model.target_iid
                
                dv = DefectView(self.appliTw, self.appliViewFrame, self.mainApp,
                                DefectController(Defect(defect)))
                dv.openInsertWindow(defect.get("notes", ""))

    def status_change(self, event):
        status = self.form_status.getValue()
        self.controller.doUpdate({"Status": status})
        caller = self.form_status.box
        #caller = widget.master
        #caller.update_idletasks()
        toast = ChildDialogToast(self.appliViewFrame, "Done" , x=caller.winfo_rootx(), y=caller.winfo_rooty()+caller.winfo_reqheight(), width=caller.winfo_reqwidth())
        toast.show()


    def upload_scan_files(self, event):
        files_paths = self.form_file.getValue()
        files = set()
        for filepath in files_paths:
            if os.path.isdir(filepath):
                # r=root, d=directories, f = files
                for r, _d, f in os.walk(filepath):
                    for fil in f:
                        files.add(os.path.join(r, fil))
            else:
                files.add(filepath)
        if not files:
            return
        dialog = ChildDialogProgress(self.mainApp, "Importing files", "Importing "+str(
            len(files)) + " files. Please wait for a few seconds.", 1/len(files)*50, "determinate")
        dialog.show(len(files))
        # LOOP ON FOLDER FILES
        results = {}
        apiclient = APIClient.getInstance()
        for f_i, file_path in enumerate(files):
            additional_results = apiclient.importExistingResultFile(file_path, "auto-detect", {"check_iid":str(self.controller.getDbId()), "lvl":"import"}, "")
            for key, val in additional_results.items():
                results[key] = results.get(key, 0) + val
            dialog.update()
        dialog.destroy()
        # DISPLAY RESULTS
        presResults = ""
        filesIgnored = 0
        for key, value in results.items():
            presResults += str(value) + " " + str(key)+".\n"
            if key == "Ignored":
                filesIgnored += 1
        if filesIgnored > 0:
            tk.messagebox.showwarning(
                "Auto-detect ended", presResults, parent=self.mainApp)
        else:
            tk.messagebox.showinfo("Auto-detect ended", presResults, parent=self.mainApp)
        self.openModifyWindow()

       
    
    def launchToolLocalCallbackLambda(self, tool_iid, **kwargs):
        return lambda event, kwargs: self.launchToolLocalCallback(tool_iid, **kwargs)
    
    def queueToolCallbackLambda(self, tool_iid, **kwargs):
        return lambda event, kwargs: self.queueToolWorkerCallback(tool_iid, **kwargs)

    def launchToolWorkerCallbackLambda(self, tool_iid, **kwargs):
        return lambda event, kwargs: self.launchToolWorkerCallback(tool_iid, **kwargs)

    def peekToolCallbackLambda(self, tool_iid):
        return lambda event=None: self.peekToolCallback(tool_iid)
    
    def stopToolCallbackLambda(self, tool_iid):
        return lambda event=None: self.stopToolCallback(tool_iid)

    def downloadToolCallbackLambda(self, tool_iid):
        return lambda event=None: self.downloadToolCallback(tool_iid)
    
    def deleteToolCallbackLambda(self, tool_iid):
        return lambda event=None: self.deleteToolCallback(tool_iid)
    
    def createDefectCallbackLambda(self, tool_iid):
        return lambda _event=None: self.createDefectToolCallback(tool_iid)
    
    def resetToolCallbackLambda(self, tool_iid):
        return lambda event=None: self.resetToolCallback(tool_iid)
    
    def resetToolCallbackLambda(self, tool_iid):
        return lambda event=None: self.resetToolCallback(tool_iid)
    
    def getAdditionalContextualCommands(self):
        ret = {}
        dataManager = DataManager.getInstance()
        target_m = dataManager.get(self.controller.model.target_type, self.controller.model.target_iid)
        if target_m is not None:
            if hasattr(target_m, "getURL"):
                url = target_m.getURL()
                if url != "":
                    ret["Open In Browser"] = self.openInBrowser
        ret["Attack from terminal"] = self.attackOnTerminal
        return ret
    
    def openInBrowser(self):
        dataManager = DataManager.getInstance()
        target_m = dataManager.get(self.controller.model.target_type, self.controller.model.target_iid)
        if target_m is not None:
            if hasattr(target_m, "getURL"):
                url = target_m.getURL()
                if url != "":
                    webbrowser.open_new_tab(url)

    def openToolDialog(self, event, infos):
        tool_iid = infos.get("iid")
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})
        tool_vw = ToolView(self.appliTw, None, self.mainApp, ToolController(tool_m))
        tool_vw.openInDialog()
        self.openModifyWindow()

    def onDoubleClick(self):
        self.controller.swapStatus()

    def openTargetDialog(self, event):
        data = self.controller.getData()
        datamanager = DataManager.getInstance()
        ret = datamanager.get(data["target_type"].lower(), data["target_iid"])
        if ret is None:
            tk.messagebox.showerror("Error", "Target not found")
            return
        view = self.mainApp.modelToView(data["target_type"], ret)
        if view:
            if hasattr(view, "openInDialog"): # If it is not a ChildDialog already, open it
                view.openInDialog()
        self.openModifyWindow()

    def launchToolLocalCallback(self, tool_iid, **kwargs):
        form_commandline = kwargs.get("formstr", None)
        command_bin = kwargs.get("bin", None)
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})

        if form_commandline is not None:
            command_line = form_commandline.getValue()
            tool_m.text = command_line
            tool_m.update({"text":command_line})
            settings = Settings()
            my_commands = settings.local_settings.get("my_commands", {})
            bin_path = my_commands.get(tool_m.name)
            if bin_path is None:
                bin_path = command_bin.getValue()
            bin_path_found = utils.which_expand_alias(bin_path)
            if bin_path_found and bin_path_found != "":
                self.mainApp.launch_tool_in_terminal(tool_m, bin_path_found+" "+command_line)
            else:
                tk.messagebox.showerror("Could not launch this tool", f"Binary path is not available ({bin_path}), is it not installed ?")
            #

    def launchToolWorkerCallback(self, tool_iid, **kwargs):
        apiclient = APIClient.getInstance()
        form_commandline = kwargs.get("formstr", None)
        
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})
        self.mainApp.subscribe_notification("tool_start", self.toolStartedEvent, pentest=apiclient.getCurrentPentest(), iid=tool_iid)
        if form_commandline is not None:
            command_line = form_commandline.getValue()
            tool_m.text = command_line
            tool_m.update({"text":command_line})
        results = apiclient.runTask(tool_iid)
        if not results:
            self.mainApp.unsubscribe_notification("tool_start", self.toolStartedEvent, pentest=apiclient.getCurrentPentest(), iid=tool_iid)
      

    def queueToolWorkerCallback(self, tool_iid, **kwargs):
        apiclient = APIClient.getInstance()
        form_commandline = kwargs.get("formstr", None)
        
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})

        if form_commandline is not None:
            command_line = form_commandline.getValue()
            tool_m.text = command_line
            tool_m.update({"text":command_line})
        results = apiclient.sendQueueTasks(tool_iid)
        if results.get("successes", []):
            self.mainApp.subscribe_notification("tool_start", self.toolStartedEvent, pentest=apiclient.getCurrentPentest(), iid=tool_iid)
            #self.mainApp.after(600, self.openModifyWindow)
        else:
            if results.get("failures", []):
                failure = results.get("failures", [])[0]
                tk.messagebox.showerror("Error", "Error while queueing task : "+str(failure.get("error", "unknown error")), parent=self.mainApp)

    def toolStartedEvent(self, notification):
        iid = notification.get("iid")
        if iid is None:
            return
        apiclient = APIClient.getInstance()
        self.mainApp.unsubscribe_notification("tool_start", pentest=apiclient.getCurrentPentest(), iid=iid)
        self.peekToolCallback(iid)

    def peekToolCallback(self, tool_iid):
        tool_controller = ToolController(Tool.fetchObject({"_id":ObjectId(tool_iid)}))
        self.mainApp.open_any_terminal(str(self.controller.getDbId())+"|"+str(tool_controller.getDbId()), tool_controller.getDetailedString(), tool_controller, self.mainApp.scanManager)
        
    def stopToolCallback(self, tool_iid):
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})
        tool_vw = ToolView(self.appliTw, self.appliViewFrame, self.mainApp, ToolController(tool_m))
        tool_vw.stopCallback()

    def downloadToolCallback(self, tool_iid):
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})
        tool_vw = ToolView(self.appliTw, self.appliViewFrame, self.mainApp, ToolController(tool_m))
        tool_vw.downloadResultFile()
        
    def deleteToolCallback(self, tool_iid):
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})
        tool_vw = ToolView(self.appliTw, self.appliViewFrame, self.mainApp, ToolController(tool_m))
        tool_vw.delete()


    def createDefectToolCallback(self, tool_iid):
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})
        tool_vw = ToolView(self.appliTw, self.appliViewFrame, self.mainApp, ToolController(tool_m))
        tool_vw.createDefectCallback()

    def resetToolCallback(self, tool_iid):
        tool_m = Tool.fetchObject({"_id":ObjectId(tool_iid)})
        tool_vw = ToolView(self.appliTw, self.appliViewFrame, self.mainApp, ToolController(tool_m))
        tool_vw.resetCallback(reload=False)

    def viewScript(self, script):
        ScriptManager.openScriptForUser(script)

    def execScript(self, script):
        data = self.controller.getData()
        data["default_target"] = str(self.controller.getDbId())
        scriptmanager = ScriptManager()
        scriptmanager.executeScript(self.mainApp, script, data, parent=self.mainApp)
    
    @classmethod
    def multiAddInTreeview(self, appliTw, appliViewFrame, mainApp, checkinstances, parent, **kwargs):
        ids = [str(checkinstance.getId()) for checkinstance in checkinstances]
        apiclient = APIClient.getInstance()
        targets_repr = apiclient.getCheckInstanceRepr(ids)
        for checkinstance in checkinstances:
            checkinstance_o = CheckInstanceController(checkinstance)
            checkinstance_o.target_repr = targets_repr.get(str(checkinstance_o.model.target_iid), "Target not found")
            checkinstance_vw = CheckInstanceView(
                appliTw, appliViewFrame, mainApp, checkinstance_o)
            checkinstance_vw.addInTreeview(parent, addChildren=False, detailed=True)
        

    def addInTreeview(self, parentNode=None, **kwargs):
        """Add this view in treeview. Also stores infos in application treeview.
        Args:
            parentNode: if None, will calculate the parent. If setted, forces the node to be inserted inside given parentNode.
        """
        addChildren = kwargs.get("addChildren", True)
        refresh_status = kwargs.get("refresh_status", False)
        self.appliTw.views[str(self.controller.getDbId())] = {"view": self}
        if parentNode is None:
            parentNode = self.getParentNode()
        if kwargs.get("detailed", False):
            text = self.controller.target_repr + " - " +str(self)
        else:
            text = self.controller.target_repr if self.mainApp.settings.is_checklist_view()  else str(self)
        if refresh_status:
            check_infos = self.controller.getCheckInstanceStatus()
        else:
            check_infos = {}
        if kwargs.get("insert_parents", False) and parentNode != "" and parentNode is not None:
            try:
                self.appliTw.insertViewById(parentNode)
            except tk.TclError as e:
                pass
        tags = kwargs.get("tags", None)
        if tags is None:
            tags = self.controller.getTags()
        try:
            self.appliTw.tk.call(self.appliTw, "insert", parentNode, "end", "-id", str(self.controller.getDbId()), "-text", text, "-tags", tags, "-image",self.getIcon(check_infos))
            # ABOVE IS FASTER self.appliTw.insert(parentNode, "end", str(
            #     self.controller.getDbId()), text=text, tags=self.controller.getTags(), image=self.getIcon(check_infos))
        except tk.TclError as e:
            pass
        # if addChildren:
        #     tools = self.controller.getTools()
        #     for tool in tools:
        #         tool_o = ToolController(Tool(tool))
        #         tool_vw = ToolView(
        #             self.appliTw, self.appliViewFrame, self.mainApp, tool_o)
        #         tool_vw.addInTreeview(str(self.controller.getDbId()))
    
        status = check_infos.get("status", "")
        if status == "":
            status = self.controller.model.status
        if status == "":
            status = "todo"
    
        if "hidden" in tags:
            self.hide("tags")
        if  (status != "todo" and self.mainApp.settings.is_show_only_todo()):
            self.hide("filter_todo")
        if self.mainApp.settings.is_show_only_manual() and self.controller.isAuto():
            self.hide("filter_manual")

    def getParentNode(self):
        """
        Return the id of the parent node in treeview.

        Returns:
            return the saved command_node node inside the Appli class.
        """
        if self.mainApp.settings.is_checklist_view():
            res = self._insertParentNode()
            return res
        else:
            parent = self.controller.getTarget()
            if parent is not None and parent != "":
                return parent
        return None

    def _insertParentNode(self):
        datamanager = DataManager.getInstance()
        checkitem = datamanager.get("checkitems", self.controller.model.check_iid)
        if checkitem is not None:
            view = self.mainApp.modelToView("checkitem", checkitem)
            if view:
                view.addInTreeview(tags=[])
        return str(self.controller.model.check_iid)
    
    def _initContextualMenu(self):
        """Initiate contextual menu with variables"""
        self.menuContextuel = utils.craftMenuWithStyle(self.appliViewFrame)

    def popup(self, event):
        """
        Fill the self.widgetMenuOpen and reraise the event in the editing window contextual menu

        Args:
            event: a ttk Treeview event autofilled. Contains information on what treeview node was clicked.
        """
        self.widgetMenuOpen = event.widget
        self.menuContextuel.tk_popup(event.x_root, event.y_root)
        self.menuContextuel.focus_set()
        self.menuContextuel.bind('<FocusOut>', self.popupFocusOut)

    def popupFocusOut(self, _event=None):
        """
        Called when the contextual menu is unfocused
        Args:
            _event: a ttk event autofilled. not used but mandatory.
        """
        self.menuContextuel.unpost()


    def updateReceived(self, obj=None, old_obj=None):
        """Called when a command update is received by notification.
        Update the command treeview item (resulting in icon reloading)
        """
        try:
            self.appliTw.item(str(self.controller.getDbId()), image=self.getIcon())
            self.appliTw.update()
        except tk.TclError as e:
            print(e)
            pass
            #print("WARNING: Update received for a non existing tool "+str(self.controller.getModelRepr()))
        super().updateReceived()

    def key(self):
        """Returns a key for sorting this node
        Returns:
            tuple, key to sort
        """
        return tuple([ord(c) for c in str(self.controller.getModelRepr()).lower()])
