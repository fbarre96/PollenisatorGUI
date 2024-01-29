"""Hold functions to interact with the settings"""
import json
import os
import tkinter as tk
import tkinter.messagebox
import tkinter.ttk as ttk
from shutil import which

from customtkinter import *
from PIL import Image

import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.scrollableframexplateform import ScrollableFrameXPlateform
from pollenisatorgui.core.components.apiclient import APIClient, ErrorHTTP
from pollenisatorgui.core.forms.formpanel import FormPanel
from pollenisatorgui.core.views.viewelement import ViewElement
from pollenisatorgui.core.application.pollenisatorentry import PopoEntry

class Settings:
    """
    Represents the settings of pollenisator.
    There are three level of settings:
        * local settings: stored in a file under ../../config/settings.cfg
        * pentest db settings: stored in the pentest database under settings collection
        * global settings: stored in the pollenisator database under settings collection
    """
    tags_cache = None
    __pentest_types = None
    def __init__(self):
        """
        Load the tree types of settings and stores them in dictionnaries
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.confdir = os.path.join(dir_path, "../../config/settings.cfg")

        self.local_settings = {}
        try:
            with open(self.confdir, mode="r") as f:
                self.local_settings = json.loads(f.read())
        except json.JSONDecodeError:
            self.local_settings = {}
        except IOError:
            self.local_settings = {}
        self.db_settings = {}
        self.global_settings = {}
        self.text_pentest_types = None
        self.text_tags = None
        self.text_db_tags = None
        self.box_pentest_type = None
        self.visual_include_domains_with_ip_in_scope = None
        self.visual_include_domains_with_topdomain_in_scope = None
        self.visual_search_show_hidden = None
        self.visual_search_exact_match = None
        self.visual_include_all_domains = None
        self.visual_dark_mode = None
        #self.text_pentesters = None
        self.box_favorite_term = None
        self.visual_trap_commands = None
        self.pentesters_treevw = None
        from pollenisatorgui.core.components.datamanager import DataManager
        DataManager.getInstance().attach(self)

    @classmethod
    def getPentestTags(cls):
        apiclient = APIClient.getInstance()
        db_tags = apiclient.find("settings", {"key":"tags"}, False)
        if db_tags is None:
            db_tags = {}
        else:
            db_tags = db_tags["value"]
        return db_tags

    @classmethod
    def getTags(cls, onlyGlobal=False, **kwargs):
        """
        Returns tags defined in settings.
        Returns:
            If none are defined returns default
            otherwise returns a dict with defined key values
        """
        apiclient = APIClient.getInstance()
        if kwargs.get("ignoreCache", False): #Check if ignore cache is true
            cls.tags_cache = None
        if cls.tags_cache is not None and not onlyGlobal:
            return cls.tags_cache
        cls.tags_cache = {"todo":{"color":"orange", "level":"todo"}, "pwned":{"color":"red", "level":"high"}, "Interesting":{"color":"dark green", "level":"medium"}, "Uninteresting":{"color":"sky blue", "level":"low"}, "neutral":{"color":"transparent", "level":""}}
        try:
            global_tags = apiclient.getSettings({"key": "tags"})
        except ErrorHTTP:
            global_tags = None
        if global_tags is not None:
            if isinstance(global_tags["value"], dict):
               global_tags = global_tags["value"]
            elif isinstance(global_tags["value"], str):
                global_tags = json.loads(global_tags["value"])
        if global_tags is None:
            global_tags = {}
        if isinstance(global_tags, str):
            global_tags = json.loads(global_tags)
        if not onlyGlobal:
            try:
                db_tags = cls.getPentestTags()
            except ErrorHTTP:
                db_tags = {}
            cls.tags_cache = {**global_tags, **db_tags}
            return cls.tags_cache
        return global_tags

    @classmethod
    def getPentestTypes(cls):
        """
        Returns pentest types and associeted defect type defined in settings.
        Returns:
            If none are defined returns {"Web":["Base", "Application", "Data", "Policy"], "LAN":["Infrastructure", "Active Directory", "Data", "Policy"]}
            otherwise returns a dict with defined key values
        """
        apiclient = APIClient.getInstance()
        if cls.__pentest_types is None:
            pentest_types = apiclient.getSettings({"key": "pentest_types"})
            if pentest_types is not None:
                if isinstance(pentest_types["value"], str):
                    cls.__pentest_types = json.loads(pentest_types["value"])
                elif isinstance(pentest_types["value"], dict):
                    cls.__pentest_types = pentest_types["value"]
                else:
                    cls.__pentest_types = {"Web":["Base", "Application", "Data", "Policy"], "LAN":["Infrastructure", "Active Directory", "Data", "Policy"]}
            else:
                cls.__pentest_types = {"Web":["Base", "Application", "Data", "Policy"], "LAN":["Infrastructure", "Active Directory", "Data", "Policy"]}
        return cls.__pentest_types

    def getClientName(self):
        return self.db_settings.get("client_name", "")
    
    def getMissionName(self):
        return self.db_settings.get("mission_name", "")

   
    
    def is_hide_oos(self):
        return self.local_settings.get("hide_oos", False)
    
    def is_checklist_view(self):
        return self.local_settings.get("checklist_view", True)

    def is_show_only_todo(self):
        return self.local_settings.get("show_only_todo", False)

    def is_show_only_manual(self):
        return self.local_settings.get("show_only_manual", False)

    def isTrapCommand(self):
        return self.local_settings.get("trap_commands", True)

    def is_dark_mode(self):
        return self.local_settings.get("dark_mode", False)

    def setTrapCommand(self):
        self.local_settings["trap_commands"] = self.visual_trap_commands.get()
        self.saveLocalSettings()


    
    def reloadLocalSettings(self):
        """
        Reload local settings from local conf file
        """
        try:
            with open(self.confdir, mode="r") as f:
                self.local_settings = json.loads(f.read())
        except json.JSONDecodeError:
            self.local_settings = {}
        except IOError:
            self.local_settings = {}

    def _reloadDbSettings(self):
        """
        Reload pentest database settings from pentest database
        """
        apiclient = APIClient.getInstance()
        dbSettings = apiclient.find("settings", {})
        if dbSettings is None:
            dbSettings = {}
        self.__class__.tags_cache = None
        for settings_dict in dbSettings:
            try:
                self.db_settings[settings_dict["key"]] = settings_dict["value"]
            except KeyError:
                pass

    def _reloadGlobalSettings(self):
        """
        Reload pentest database settings from pollenisator database
        """
        apiclient = APIClient.getInstance()
        globalSettings = apiclient.getSettings()
        self.__class__.tags_cache = None
        for settings_dict in globalSettings:
            self.global_settings[settings_dict["key"]] = settings_dict["value"]

    def reloadSettings(self):
        """
        Reload local, database and global settings.
        """
        self.reloadLocalSettings()
        self._reloadDbSettings()
        self._reloadGlobalSettings()

    def reloadUI(self):
        """
        Reload all settings and refresh view with values
        """
        self.reloadSettings()
        self.visual_include_all_domains.set(
            self.db_settings.get("include_all_domains", False))
        self.visual_include_domains_with_ip_in_scope.set(
            self.db_settings.get("include_domains_with_ip_in_scope", False))
        self.visual_include_domains_with_topdomain_in_scope.set(
            self.db_settings.get("include_domains_with_topdomain_in_scope", False))
        self.text_pentest_name.delete("0", tk.END)
        apiclient = APIClient.getInstance()
        self.text_pentest_name.insert("0", apiclient.getCurrentPentestName())
        self.text_mission_name.delete("0", tk.END)
        self.text_mission_name.insert("0",
            self.db_settings.get("mission_name", ""))
        self.text_client_name.delete("0", tk.END)
        self.text_client_name.insert("0",
            self.db_settings.get("client_name", ""))
        self.combo_lang.set(self.db_settings.get("lang", "en"))
        self.visual_search_show_hidden.set(
            self.local_settings.get("search_show_hidden", True))
        self.visual_search_exact_match.set(
            self.local_settings.get("search_exact_match", False))
        self.visual_dark_mode.set(
            self.local_settings.get("dark_mode", False))
        self.visual_trap_commands.set(self.local_settings.get("trap_commands", False))
        #self.text_pentesters.delete('1.0', tk.END)
        #self.text_pentesters.insert(
        #    tk.INSERT, "\n".join(
        #        self.db_settings.get("pentesters", [])))
        self.pentesters_treevw.reset()
        pentesters_as_list = self.db_settings.get("pentesters", [""])
        dict_for_tw = {}
        for pentester in pentesters_as_list:
            dict_for_tw[pentester] = tuple([pentester])
        self.pentesters_treevw.recurse_insert(dict_for_tw)
        self.box_pentest_type.set(self.db_settings.get("pentest_type", "None"))
        self.text_pentest_types.delete('1.0', tk.END)
        pentestTypes = Settings.getPentestTypes()
        buffer = ""
        for pentestType, pentestTypeDefectTypes in pentestTypes.items():
            buffer += pentestType +" : "+ (", ".join(pentestTypeDefectTypes))+"\n"
        self.text_pentest_types.insert(
            tk.INSERT, buffer)
        self.text_tags.delete('1.0', tk.END)
        tagsRegistered = Settings.getTags(onlyGlobal=True)
        buffer = json.dumps(tagsRegistered, indent=4)
        self.text_tags.insert(
            tk.INSERT, buffer)
        self.text_db_tags.delete('1.0', tk.END)
        tagsPentestRegistered = Settings.getPentestTags()
        buffer = json.dumps(tagsPentestRegistered, indent=4)
        self.text_db_tags.insert(
            tk.INSERT, buffer)
        
    def saveLocalSettings(self):
        """
        Save local settings to conf file
        """
        with open(self.confdir, mode="w") as f:
            f.write(json.dumps(self.local_settings))

    def setPentestSetting(self, key, val):
        apiclient = APIClient.getInstance()
        self.db_settings[key] = val
        apiclient.updatePentestSetting({"key":key, "value": json.dumps(val)})

    def savePentestSettings(self):
        apiclient = APIClient.getInstance()
        settings = apiclient.find("settings")
        existing_settings = {}
        for setting in settings:
            existing_settings[setting["key"]] = setting
        for k, v in self.db_settings.items():
            if k in existing_settings:
                if k == "tags":
                    for line_key, line_value in v.items():
                        tag, tag_infos = line_key, line_value
                        if tag not in existing_settings["tags"]["value"]:
                            apiclient.registerTag(apiclient.getCurrentPentest(), tag, tag_infos["color"], tag_infos["level"])
                        else:
                            apiclient.updateTag(tag, tag_infos["color"], tag_infos["level"], False)
                    for tag in existing_settings["tags"].get("value",{}):
                        if tag not in v:
                            apiclient.unregisterTag(apiclient.getCurrentPentest(), tag)
                else:
                    apiclient.updatePentestSetting({"key":k, "value": json.dumps(v)})

    def save(self):
        """
        Save all the settings (local, database and global)
        """
        apiclient = APIClient.getInstance()

        for k, v in self.global_settings.items():
            if apiclient.getSettings({"key": k}) is None:
                apiclient.createSetting(k, v)
            else:
                apiclient.updateSetting(k, v)
        self.savePentestSettings()
        self.saveLocalSettings()
        self.reloadUI()

    def initUI(self, parent):
        """Create settings widgets and initialize them
        Args:
            parent: parent tkinter container widget"""
        if self.visual_include_all_domains is not None:  # Already built
            self.reloadUI()
            return
        self.parent = parent
        self.image_save = CTkImage(Image.open(utils.getIcon("save.png")))

        self.settingsFrame = ScrollableFrameXPlateform(parent)
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        self.visual_include_all_domains = tk.BooleanVar()
        self.visual_dark_mode = tk.BooleanVar()
        self.visual_include_domains_with_ip_in_scope = tk.BooleanVar()
        self.visual_include_domains_with_topdomain_in_scope = tk.BooleanVar()
        self.visual_search_show_hidden = tk.BooleanVar()
        self.visual_search_exact_match = tk.BooleanVar()
        self.visual_trap_commands = tk.BooleanVar()
        chkbox_dark_mode = CTkSwitch(self.settingsFrame, text="Dark mode",
                                                     variable=self.visual_dark_mode)
        chkbox_dark_mode.pack(
            padx=10, pady=10, side=tk.TOP, anchor=tk.W)
        lbl_domains = ttk.LabelFrame(
            self.settingsFrame, text="Discovered domains options")
        
        chkbox_include_domains_with_ip_in_scope = CTkSwitch(lbl_domains, text="Check if discovered subdomains ips are in scope",
                                                                  variable=self.visual_include_domains_with_ip_in_scope)
        chkbox_include_domains_with_ip_in_scope.pack(
            padx=10, pady=10, side=tk.TOP, anchor=tk.W)

        chkbox_include_domains_with_topdomain_in_scope = CTkSwitch(lbl_domains, text="Check if discovered subdomains have a top domain already in scope",
                                                                         variable=self.visual_include_domains_with_topdomain_in_scope)
        chkbox_include_domains_with_topdomain_in_scope.pack(
            padx=10, pady=10, side=tk.TOP, anchor=tk.W)
        chkbox_include_all_domains = CTkSwitch(lbl_domains, text="/!\\ Include every domain found in scope",
                                                     variable=self.visual_include_all_domains)
        chkbox_include_all_domains.pack(
            padx=10, pady=10, side=tk.TOP, anchor=tk.W)
        lbl_domains.pack(padx=10, pady=10, side=tk.TOP,
                         anchor=tk.CENTER, fill=tk.X, expand=tk.YES)
        frame_term = ttk.LabelFrame(self.settingsFrame, text="Local terminal configuration")
        chkbox_trap_commands = CTkSwitch(frame_term, text="Trap every command (instead of using pollex)", variable=self.visual_trap_commands)
        chkbox_trap_commands.pack(side=tk.TOP, pady=5)
        frame_term.pack(padx=10, pady=10, side=tk.TOP,
                           anchor=tk.CENTER, fill=tk.X, expand=tk.YES)
        lbl_SearchBar = ttk.LabelFrame(self.settingsFrame, text="Search settings")
        
        chkbox_search_show_hidden = CTkSwitch(lbl_SearchBar, text="Show hidden objects",
                                                    variable=self.visual_search_show_hidden)
        chkbox_search_show_hidden.pack(
            padx=10, pady=10, side=tk.TOP, anchor=tk.W)
        chkbox_search_exact_match = CTkSwitch(lbl_SearchBar, text="Exact match",
                                                    variable=self.visual_search_exact_match)
        chkbox_search_exact_match.pack(
            padx=10, pady=10, side=tk.TOP, anchor=tk.W)
        lbl_SearchBar.pack(padx=10, pady=10, side=tk.TOP,
                           anchor=tk.CENTER, fill=tk.X, expand=tk.YES)
        lblframe_pentest_params = ttk.LabelFrame(
            self.settingsFrame, text="Pentest parameters")
        lbl_pentest_name = CTkLabel(lblframe_pentest_params, text="Pentest name")
        lbl_pentest_name.grid(row=0, column=0, sticky=tk.E)
        self.text_pentest_name = PopoEntry(lblframe_pentest_params)
        self.text_pentest_name.grid(row=0, column=1, sticky=tk.W)
        lbl_client_name = CTkLabel(lblframe_pentest_params, text="Client's name")
        lbl_client_name.grid(row=1, column=0, sticky=tk.E)
        self.text_client_name = PopoEntry(lblframe_pentest_params)
        self.text_client_name.grid(row=1, column=1, sticky=tk.W)
        
        lbl_mision_name = CTkLabel(lblframe_pentest_params, text="Mission name")
        lbl_mision_name.grid(row=2, column=0, sticky=tk.E)
        self.text_mission_name = PopoEntry(lblframe_pentest_params)
        self.text_mission_name.grid(row=2, column=1, sticky=tk.W)
        lbl_report_lang =  CTkLabel(lblframe_pentest_params, text="Report language")
        lbl_report_lang.grid(row=3, column=0, sticky=tk.E)
        langs = APIClient.getInstance().getLangList()
        self.combo_lang = CTkComboBox(lblframe_pentest_params, values=langs)
        self.combo_lang.grid(row=3, column=1, sticky=tk.W)
        lbl_pentest_type = CTkLabel(
            lblframe_pentest_params, text="Pentest type")
        lbl_pentest_type.grid(row=4, column=0, sticky=tk.E)
        self.box_pentest_type = CTkComboBox(
            lblframe_pentest_params, values=tuple(Settings.getPentestTypes().keys()))
        self.box_pentest_type.grid(row=4, column=1, sticky=tk.W)
        # self.text_pentesters = CTkTextbox(
        #     lblframe_pentest_params, height=3, font = ("Sans", 10))
        # lbl_pentesters = CTkLabel(
        #     lblframe_pentest_params, text="Pentester names")
        # lbl_pentesters.grid(row=2, column=0, sticky=tk.E)
        # self.text_pentesters.grid(row=2, column=1, sticky=tk.W, pady=5)
        lblframe_pentest_params.pack(
            padx=10, pady=10, side=tk.TOP, anchor=tk.CENTER, fill=tk.X, expand=tk.YES)
        form_pentesters_panel = CTkFrame(self.settingsFrame)
        self.form_pentesters = FormPanel(side=tk.TOP, fill=tk.X, pady=5)
        self.form_pentesters.addFormSearchBar("Pentester search", self.searchCallback, self.form_pentesters, side=tk.TOP)
        self.pentesters_treevw = self.form_pentesters.addFormTreevw(
            "Additional pentesters names", ["Additional pentesters names"], (""), add_empty_row=True, height=20, width=100, pady=5, side=tk.LEFT)
        
        self.form_pentesters.constructView(form_pentesters_panel)
        form_pentesters_panel.pack(
            padx=10, pady=10, side=tk.TOP, anchor=tk.CENTER, fill=tk.X, expand=tk.YES)
        lblframe_global_params = ttk.LabelFrame(
            self.settingsFrame, text="Other parameters")
        lblframe_global_params.columnconfigure(1, weight=2)
        lbl_pentest_types = CTkLabel(
            lblframe_global_params, text="Pentests possible types")
        lbl_pentest_types.grid(row=0, column=0, sticky=tk.E, pady=10, padx=5)
        self.text_pentest_types = CTkTextbox(
            lblframe_global_params,  wrap="word")
        self.text_pentest_types.grid(row=0, column=1, sticky=tk.W+tk.E, pady=10, padx=5)
        lbl_tags = CTkLabel(
            lblframe_global_params, text="Registered tags")
        lbl_tags.grid(row=1, column=0, sticky=tk.E, pady=10, padx=5)
        self.text_tags = CTkTextbox(
            lblframe_global_params,wrap="word")
        self.text_tags.grid(row=1, column=1, sticky=tk.W+tk.E)
        lbl_db_tags = CTkLabel(
            lblframe_global_params, text="Pentest only tags")
        lbl_db_tags.grid(row=2, column=0, sticky=tk.E, pady=10, padx=5)
        self.text_db_tags = CTkTextbox(
            lblframe_global_params, wrap="word")
        
        self.text_db_tags.grid(row=2, column=1, sticky=tk.W+tk.E, pady=10)
        lblframe_global_params.pack(
            padx=10, pady=10, side=tk.TOP, anchor=tk.CENTER, fill=tk.X, expand=tk.YES)
        btn_save = CTkButton(parent, text="Save", command=self.on_ok, image=self.image_save)
        btn_save.grid(row=3, column=0, padx=10, pady=10, sticky="s")
        self.settingsFrame.grid(column=0, row=0, sticky="nsew")
        #self.settingsFrame.pack(fill=tk.BOTH, expand=1)
        #self.reloadUI()

    def searchCallback(self, searchreq):
        apiclient = APIClient.getInstance()
        users = apiclient.searchUsers(searchreq)
        if users is None:
            return [], "Invalid response from API"
        ret = [{"TITLE":user, "additional pentesters names":{"text":user}} for user in users]
        return ret, ""

    def on_ok(self):
        """Callback on click save button. loads some data and calls save.
        Args:
            parent: parent tkinter container widget"""
        info = "Settings saved"
        self.db_settings["include_all_domains"] = self.visual_include_all_domains.get(
        ) == 1
        self.db_settings["include_domains_with_ip_in_scope"] = self.visual_include_domains_with_ip_in_scope.get(
        ) == 1
        pentest_name = self.text_pentest_name.get().strip()
        apiclient = APIClient.getInstance()
        if apiclient.getCurrentPentestName() != pentest_name:
            apiclient.updatePentest(pentest_name)
        self.db_settings["mission_name"] = self.text_mission_name.get().strip()
        self.db_settings["client_name"] = self.text_client_name.get().strip()
        self.db_settings["lang"] = self.combo_lang.get().strip()
        self.db_settings["pentest_type"] = self.box_pentest_type.get()
        self.db_settings["include_domains_with_topdomain_in_scope"] = self.visual_include_domains_with_topdomain_in_scope.get(
        ) == 1
        self.db_settings["pentesters"] = []
        form_values = self.form_pentesters.getValue()
        form_values_as_dicts = ViewElement.list_tuple_to_dict(form_values)
        self.db_settings["pentesters"] = [x for x in form_values_as_dicts["Additional pentesters names"] if x.strip() != ""]
        self.db_settings["tags"] = json.loads(self.text_db_tags.get('1.0', tk.END))
       

        self.local_settings["search_show_hidden"] = self.visual_search_show_hidden.get(
        ) == 1
        self.local_settings["search_exact_match"] = self.visual_search_exact_match.get(
        ) == 1
        old = self.local_settings.get("dark_mode", False)
        self.local_settings["dark_mode"] = self.visual_dark_mode.get(
        ) == 1
        if old != self.local_settings["dark_mode"]:
            info = "Dark mode changed. You need to restart the application to see the changes."
        self.local_settings["trap_commands"] = self.visual_trap_commands.get() == 1
        self.global_settings["pentest_types"] = {}
        for type_of_pentest in self.text_pentest_types.get('1.0', tk.END).split(
                "\n"):
            if type_of_pentest.strip() != "":
                line_splitted = type_of_pentest.strip().split(":")
                if len(line_splitted) == 2:
                    typesOfDefects = list(map(lambda x: x.strip(), line_splitted[1].split(",")))
                    self.global_settings["pentest_types"][line_splitted[0].strip()] = typesOfDefects
        self.global_settings["tags"] = json.loads(self.text_tags.get('1.0', tk.END))
        self.save()
        tkinter.messagebox.showinfo(
            "Settings", info)

    def getPentestType(self):
        """Return selected database pentest type.
        Returns:
            Open database pentest type. string "None" if not defined"""
        return self.db_settings.get("pentest_type", "None")

    def getPentesters(self):
        """Return a list of pentesters registered for open pentest database
        Returns:
            List of pentesters names"""
        return self.db_settings.get("pentesters", [])

    def update_received(self, dataManager, notif, obj, old_obj):
        if notif["collection"] != "settings":
            return
        if notif["db"] == "pollenisator":
            self._reloadGlobalSettings()
        else:
            self._reloadDbSettings()

    
        

        