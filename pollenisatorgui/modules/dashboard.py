import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from PIL import Image
from pollenisatorgui.core.application.dialogs.ChildDialogSelectChecks import ChildDialogSelectChecks
from pollenisatorgui.core.components import utils
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.components.tag import TagInfos
from pollenisatorgui.core.models.checkitem import CheckItem
from pollenisatorgui.modules.module import Module
from pollenisatorgui.core.forms.formpanel import FormPanel
import threading


class Dashboard(Module):
    """
    Shows information about ongoing pentest. 
    """
    iconName = "tab_dashboard.png"
    tabName = "Dashboard"
    order_priority = Module.FIRST_PRIORITY

    def __init__(self, parent, settings, tkApp):
        """
        Constructor
        """
        super().__init__()
        self.timer = None
        self.mainApp = parent
        self.parent = None
        self.parent = parent
        
        self.tkApp = tkApp
        self.treevwApp = None
        self.autoscan_slider = None
        self.settings = settings
        self.label_count_vuln = None
        self.inited = False

    def open(self, view, topviewframe, treevw):
        apiclient = APIClient.getInstance()
        self.treevwApp = treevw
        if self.inited is False:
            self.initUI(view)
        if apiclient.getCurrentPentest() is not None:
            self.refreshUI()

        return True

    def close(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

    def refreshUI(self):
        """
        Reload data and display them
        """
        if self.tkApp.quitting:
            return
        self.loadData()
        self.displayData()
        #self.timer = threading.Timer(3.0, self.refreshUI)
        # self.timer.start()

    def loadData(self):
        """
        Fetch data from database
        """

        self.infos = APIClient.getInstance().getGeneralInformation()

    def displayData(self):
        """
        Display loaded data in treeviews
        """
        self.set_vuln_count()
        self.set_autoscan_status()
        self.set_scan_progression()
        self.set_cheatsheet_progression()
        self.set_results()

    
    def initUI(self, parent):
        """
        Build UI
        Args:
            parent: its parent widget
        """
        self.inited = True
        self.moduleFrame = CTkFrame(parent)
        vuln_frame = CTkFrame(self.moduleFrame, height=0)
        self.populate_vuln_frame(vuln_frame)
        vuln_frame.pack(side=tk.TOP, anchor=tk.W, ipady=10)
        autoscan_frame = CTkFrame(self.moduleFrame, height=0)
        self.populate_autoscan_frame(autoscan_frame)
        autoscan_frame.pack(side=tk.TOP, ipady=10, pady=10)
        results_frame = CTkFrame(self.moduleFrame, height=0)
        self.populate_results_frame(results_frame)
        results_frame.pack(side=tk.TOP, ipady=10, pady=10,
                           fill=tk.BOTH, expand=True)
        self.moduleFrame.pack(padx=10, pady=10, side="top",
                              fill=tk.BOTH, expand=True)

    def populate_vuln_frame(self, vuln_frame):
        self.vuln_image = CTkImage(Image.open(utils.getIcon("defect.png")))
        self.host_image = CTkImage(Image.open(utils.getIcon("ip.png")))
        self.label_host_count = CTkLabel(
            vuln_frame, text="X Hosts", image=self.host_image, compound="left")
        self.label_host_count.pack(padx=10, pady=3, side=tk.TOP, anchor=tk.W)
        self.label_count_vuln = CTkLabel(
            vuln_frame, image=self.vuln_image, compound="left", text="X Vulnerabilities")
        self.label_count_vuln.pack(padx=10, pady=3, side=tk.TOP, anchor=tk.W)
        sub_frame = CTkFrame(vuln_frame)
        self.label_count_vuln_critical = CTkLabel(
            sub_frame, text="X Critical", fg_color="black", text_color="white")
        self.label_count_vuln_critical.cget("font").configure(weight="bold")
        self.label_count_vuln_major = CTkLabel(
            sub_frame, text="X Major", fg_color="red", text_color="white")
        self.label_count_vuln_major.cget("font").configure(weight="bold")
        self.label_count_vuln_important = CTkLabel(
            sub_frame, text="X Important", fg_color="orange", text_color="white")
        self.label_count_vuln_important.cget("font").configure(weight="bold")
        self.label_count_vuln_minor = CTkLabel(
            sub_frame, text="X Minor", fg_color="yellow", text_color="black")
        self.label_count_vuln_minor.cget("font").configure(weight="bold")
        self.label_count_vuln_critical.pack(side="left", padx=3, ipadx=3)
        self.label_count_vuln_major.pack(side="left", padx=3, ipadx=3)
        self.label_count_vuln_important.pack(side="left", padx=3, ipadx=3)
        self.label_count_vuln_minor.pack(side="left", padx=3, ipadx=3)
        sub_frame.pack(padx=3, pady=1, side=tk.TOP, anchor=tk.W)

    def set_vuln_count(self):
        try:
            self.label_count_vuln.configure(
                text=str(self.infos.get("defect_count", 0))+" Vulnerabilities")
            self.label_count_vuln_critical.configure(
                text=str(self.infos.get("defect_count_critical", 0))+" Critical")
            self.label_count_vuln_major.configure(
                text=str(self.infos.get("defect_count_major", 0))+" Major")
            self.label_count_vuln_important.configure(
                text=str(self.infos.get("defect_count_important", 0))+" Important")
            self.label_count_vuln_minor.configure(
                text=str(self.infos.get("defect_count_minor", 0))+" Minor")
        except tk.TclError:
            return

    def slider_event(self, event):
        val = self.autoscan_slider.get()
        val = int(val)
        self.autoscan_threads_lbl.configure(
            text=str(val) + " thread"+("s" if val > 1 else ""))
        self.settings.setPentestSetting("autoscan_threads", val)

    def update_thread_label(self, event):
        val = self.autoscan_slider.get()
        # behavior is weird .set(4) then .get() return 3.7
        val = int(round(val))
        self.autoscan_threads_lbl.configure(
            text=str(val) + " thread"+("s" if val > 1 else ""))

    def populate_autoscan_frame(self, frame):
        self.image_auto = CTkImage(Image.open(utils.getIcon("auto.png")))
        self.image_start = CTkImage(Image.open(utils.getIcon("start.png")))
        self.image_stop = CTkImage(Image.open(utils.getIcon("stop.png")))
        self.image_pentest = CTkImage(Image.open(utils.getIcon("hacker.png")))
        frame_status = FormPanel(side=tk.TOP, fill=tk.X)
        frame_status.addFormButton("Go to pentest", self.go_to_pentest, image=self.image_pentest, width=200, height=50, padx=5, side=tk.LEFT, font=CTkFont("Calibri", 20, 'bold', "roman", True),anchor="center")
        frame_status.addFormSeparator(orient="vertical", padx=0, fill=tk.Y, side=tk.LEFT)
        autoscan_panel = frame_status.addFormPanel(side=tk.LEFT, fill=tk.X, padx=0, pady=0, anchor="center")
        autoscan_action_panel = autoscan_panel.addFormPanel(side=tk.TOP, fill=tk.X, padx=0, pady=0, anchor="n")
        autoscan_action_panel.addFormLabel("Autoscan", image=self.image_auto, compound="left" , padx=5, side=tk.LEFT )
        self.btn_autoscan = autoscan_action_panel.addFormButton("autoscan", self.set_autoscan_status, text="", image=self.image_auto, padx=0, side=tk.LEFT)
        self.set_autoscan_status()
        autoscan_action_panel.addFormHelper("Autoscan will launch queued scans on available workers automatically. Queueing scan must be done manually.", padx=0, pady=0, side=tk.RIGHT)
        frame_status.constructView(frame)
        frame_settings = CTkFrame(autoscan_panel.panel)
        self.autoscan_slider = CTkSlider(
            frame_settings, from_=1, to=10, number_of_steps=10, command=self.update_thread_label)
        self.autoscan_slider.bind("<ButtonRelease-1>", self.slider_event)
        self.autoscan_slider.pack(side=tk.LEFT, padx=5)
        threads = int(self.settings.db_settings.get("autoscan_threads", 4))
        self.autoscan_slider.set(threads)
        self.autoscan_threads_lbl = CTkLabel(frame_settings, text=str(
            threads)+" thread"+("s" if threads > 1 else ""))
        self.autoscan_threads_lbl.pack(side=tk.LEFT, padx=5)
        frame_settings.pack(side=tk.BOTTOM, fill=tk.X)
        
        
        frame_progress = CTkFrame(frame)
        lbl = CTkLabel(frame_progress, text="Scan Progression")
        lbl.pack(side=tk.LEFT, padx=5)
        self.scan_progressbar = CTkProgressBar(
            frame_progress, mode='determinate')
        self.scan_progressbar.pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.label_scan_progress = CTkLabel(frame_progress, text="X/X")
        self.label_scan_progress.pack(side=tk.LEFT, padx=2)
        frame_progress.pack(side=tk.TOP, pady=5)
        frame_progress_cheatsheet = CTkFrame(frame)
        lbl = CTkLabel(frame_progress_cheatsheet,
                       text="Cheatsheet Progression")
        lbl.pack(side=tk.LEFT, padx=5)
        self.cheatsheet_progressbar = CTkProgressBar(
            frame_progress_cheatsheet, mode='determinate')
        self.cheatsheet_progressbar.pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.label_cheatsheet_progress = CTkLabel(
            frame_progress_cheatsheet, text="X/X")
        self.label_cheatsheet_progress.pack(side=tk.LEFT, padx=2)
        frame_progress_cheatsheet.pack(side=tk.TOP, pady=5)

    def set_autoscan_status(self, event=None):
        apiclient = APIClient.getInstance()
        status = apiclient.getAutoScanStatus()
        if status:
            self.btn_autoscan.configure(
                text="Stop autoscan", command=self.click_stop_autoscan, image=self.image_stop)
        else:
            self.btn_autoscan.configure(
                text="Start autoscan", command=self.click_start_autoscan, image=self.image_start)
        if self.autoscan_slider:
            value = int(self.settings.db_settings.get("autoscan_threads", 4))
            self.autoscan_slider.set(value)
            self.update_thread_label(value)

    def click_stop_autoscan(self):
        res = self.tkApp.stop_autoscan()
        if res:
            self.set_autoscan_status()

    def click_start_autoscan(self):

        res = self.tkApp.start_autoscan()
        if res:
            self.set_autoscan_status()

    def go_to_pentest(self, event=None):
        self.tkApp.nbk.select("Main View")


    def set_scan_progression(self):
        done = self.infos.get("tools_done_count", 0)
        total = float(self.infos.get("tools_count", 0))
        if total > 0:
            self.scan_progressbar.set(float(done)/float(total))
        self.scan_progressbar.update_idletasks()
        self.label_scan_progress.configure(text=str(done)+"/"+str(int(total)))
        self.label_scan_progress.update_idletasks()

    def set_cheatsheet_progression(self):
        done = self.infos.get("checks_done", 0)
        total = float(self.infos.get("checks_total", 0))
        if total > 0:
            self.cheatsheet_progressbar.set(float(done)/float(total))
        self.cheatsheet_progressbar.update_idletasks()
        self.label_cheatsheet_progress.configure(
            text=str(done)+"/"+str(int(total)))
        self.label_cheatsheet_progress.update_idletasks()

    def populate_results_frame(self, frame):
        self.form = FormPanel(fill="x",pady=0)
        form_top = self.form.addFormPanel(grid=True, side="top", fill="x", pady=0, anchor="s")
        form_top.addFormLabel("Text filter", row=0, column=0, sticky="s")
        self.str_filter = form_top.addFormStr("text_filter", placeholder="high", binds={"<KeyRelease>":self.filter}, width=300, row=0, column=1, sticky="S")
        form_bottom = self.form.addFormPanel(side="bottom", fill="x", pady=0)
        values = ["Critical", "Major", "Important", "Minor"]
        tags_registered = Settings.getTags()
        for tag_info in tags_registered.values():
            if tag_info["level"] not in values and tag_info["level"] != "":
                values.append(tag_info["level"])
        check_panel = form_top.addFormPanel(row=0, column=2,fill=None)
        self.severity_btns = check_panel.addFormChecklist("Severity", list(values), command=self.filter)

        self.treeview = form_bottom.addFormTreevw(
            "results", ("Result type", "Time", "Severity", "Title", "Target"), binds={"<Double-Button-1>": self.on_result_double_click},status="readonly", height=10, fill="x", side="top", expand=True)  
        self.form.constructView(frame)
        
    def filter(self, event=None):
        str_filter = self.str_filter.getValue()
        risks_checked = [k for k,v in self.severity_btns.getValue().items() if v == 1]
        self.treeview.filter(str_filter, str_filter, str_filter, str_filter, str_filter, check_all=False)
        if len(risks_checked) > 0:
            self.treeview.filter(True, True, risks_checked, True, True, reset=False)

    def on_result_double_click(self, event):
        if self.treeview is not None:
            tv = event.widget
            item = tv.identify("item", event.x, event.y)
            if tv.item(item)["text"] == "Tag":
                tag = self.datamanager.get("tags", item.split("|")[0])
                id_to_show = tag.item_id
            else:
                id_to_show = item
            self.mainApp.search("id == \""+str(id_to_show)+"\"")

    def set_results(self):
        self.datamanager = DataManager.getInstance()
        self.label_host_count.configure(
            text="Hosts : "+str(self.infos.get("hosts_count", 0)))
        defects = self.datamanager.get("defects", '*')
        self.treeview.reset()
        for defect in defects:
            if defect.isAssigned():
                self.treeview.addItem("", tk.END, defect.getId(), text="Security Defect", values=(
                    defect.creation_time, defect.risk, defect.title, defect.getDetailedString(onlyTarget=True)))
        tags = self.infos.get("tagged", [])
        tags_registered = Settings.getTags()
        for tag_infos in tags:
            for tag in tag_infos.get("tags", []):
                tag = TagInfos(tag)
                tag_name = tag.name
                
                if tags_registered.get(tag_name, {}).get("level", "") != "":
                    self.treeview.addItem("", tk.END, tag_infos["_id"]+"|"+tag_name, text="Tag", values=(
                        tag_infos["date"], tags_registered[tag_name]["level"], tag_name,  tag_infos["detailed_string"]))
        self.treeview.auto_resize_columns()