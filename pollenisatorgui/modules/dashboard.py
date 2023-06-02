import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from PIL import Image
from pollenisatorgui.core.application.dialogs.ChildDialogSelectChecks import ChildDialogSelectChecks
from pollenisatorgui.core.components import utils
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.datamanager import DataManager
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
    
    def __init__(self, parent, settings):
        """
        Constructor
        """
        super().__init__()
        self.timer = None
        self.parent = None
        self.settings = settings
        self.label_count_vuln = None

    def open(self):
        apiclient = APIClient.getInstance()
        
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
        #self.timer.start()


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

    def initUI(self, parent, nbk, treevw, tkApp):
        """
        Initialize Dashboard widgets
        Args:
            parent: its parent widget
        """
        if self.parent is not None:  # Already initialized
            return
        self.parent = parent
        self.tkApp = tkApp
        self.treevwApp = treevw
        self.autoscan_slider = None
        self.moduleFrame = CTkFrame(parent)
        vuln_frame = CTkFrame(self.moduleFrame, height=0)
        self.populate_vuln_frame(vuln_frame)
        vuln_frame.pack(side=tk.TOP, anchor=tk.W, ipady=10)
        autoscan_frame = CTkFrame(self.moduleFrame, height=0)
        self.populate_autoscan_frame(autoscan_frame)
        autoscan_frame.pack(side=tk.TOP, ipady=10, pady=10)
        results_frame = CTkFrame(self.moduleFrame, height=0)
        self.populate_results_frame(results_frame)
        results_frame.pack(side=tk.TOP, ipady=10, pady=10, fill=tk.BOTH , expand=True)
        self.moduleFrame.pack(padx=10, pady=10, side="top", fill=tk.BOTH, expand=True)

    def populate_vuln_frame(self, vuln_frame):
        self.vuln_image = CTkImage(Image.open(utils.getIcon("defect.png")))
        self.host_image = CTkImage(Image.open(utils.getIcon("ip.png")))
        self.label_host_count = CTkLabel(vuln_frame, text="X Hosts", image=self.host_image, compound="left")
        self.label_host_count.pack(padx=10, pady=3, side=tk.TOP, anchor=tk.W)
        self.label_count_vuln = CTkLabel(vuln_frame, image=self.vuln_image, compound="left", text="X Vulnerabilities")
        self.label_count_vuln.pack(padx=10, pady=3, side=tk.TOP, anchor=tk.W)
        sub_frame = CTkFrame(vuln_frame)
        self.label_count_vuln_critical = CTkLabel(sub_frame, text="X Critical", fg_color="black", text_color="white")
        self.label_count_vuln_critical.cget("font").configure(weight="bold")
        self.label_count_vuln_major = CTkLabel(sub_frame, text="X Major", fg_color="red", text_color="white")
        self.label_count_vuln_major.cget("font").configure(weight="bold")
        self.label_count_vuln_important = CTkLabel(sub_frame, text="X Important", fg_color="orange", text_color="white")
        self.label_count_vuln_important.cget("font").configure(weight="bold")
        self.label_count_vuln_minor = CTkLabel(sub_frame, text="X Minor", fg_color="yellow", text_color="black")
        self.label_count_vuln_minor.cget("font").configure(weight="bold")
        self.label_count_vuln_critical.pack(side="left", padx=3, ipadx=3)
        self.label_count_vuln_major.pack(side="left", padx=3, ipadx=3)
        self.label_count_vuln_important.pack(side="left", padx=3, ipadx=3)
        self.label_count_vuln_minor.pack(side="left", padx=3, ipadx=3)
        sub_frame.pack(padx=3, pady=1, side=tk.TOP, anchor=tk.W)

    def set_vuln_count(self):
        try:
            self.label_count_vuln.configure(text=str(self.infos.get("defect_count", 0))+" Vulnerabilities")
            self.label_count_vuln_critical.configure(text=str(self.infos.get("defect_count_critical", 0))+" Critical")
            self.label_count_vuln_major.configure(text=str(self.infos.get("defect_count_major", 0))+" Major")
            self.label_count_vuln_important.configure(text=str(self.infos.get("defect_count_important", 0))+" Important")
            self.label_count_vuln_minor.configure(text=str(self.infos.get("defect_count_minor", 0))+" Minor")
        except tk.TclError:
            return
        
    def slider_event(self, event):
        val = self.autoscan_slider.get()
        val = int(val)
        self.autoscan_threads_lbl.configure(text=str(val) + " thread"+("s" if val > 1 else ""))
        self.settings.setPentestSetting("autoscan_threads", val)

    def update_thread_label(self, event):
        val = self.autoscan_slider.get()
        val = int(round(val)) #behavior is weird .set(4) then .get() return 3.7
        self.autoscan_threads_lbl.configure(text=str(val) + " thread"+("s" if val > 1 else ""))

    def populate_autoscan_frame(self, frame):
        self.image_auto = CTkImage(Image.open(utils.getIcon("auto.png")))
        self.image_start = CTkImage(Image.open(utils.getIcon("start.png")))
        self.image_stop = CTkImage(Image.open(utils.getIcon("stop.png")))
        frame_status = CTkFrame(frame)
        lbl = CTkLabel(frame_status, text="Autoscan", image=self.image_auto, compound="left")
        self.btn_autoscan = CTkButton(
            frame_status, text="", image=self.image_auto)
        self.set_autoscan_status()
        self.btn_autoscan.pack(side=tk.LEFT, padx=5)
        frame_status.pack(side=tk.TOP)
        frame_settings = CTkFrame(frame)
        self.autoscan_slider = CTkSlider(frame_settings, from_=1, to=10, number_of_steps=10, command=self.update_thread_label)
        self.autoscan_slider.bind("<ButtonRelease-1>", self.slider_event)
        self.autoscan_slider.pack(side=tk.LEFT, padx=5)
        threads = int(self.settings.db_settings.get("autoscan_threads", 4))
        self.autoscan_slider.set(threads)
        self.autoscan_threads_lbl = CTkLabel(frame_settings, text=str(threads)+" thread"+("s" if threads > 1 else ""))
        self.autoscan_threads_lbl.pack(side=tk.LEFT, padx=5)
        frame_settings.pack(side=tk.TOP)
        frame_progress = CTkFrame(frame)
        lbl = CTkLabel(frame_progress, text="Scan Progression")
        lbl.pack(side=tk.LEFT, padx=5)
        self.scan_progressbar = CTkProgressBar(frame_progress, mode='determinate')
        self.scan_progressbar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.label_scan_progress = CTkLabel(frame_progress, text="X/X")
        self.label_scan_progress.pack(side=tk.LEFT, padx=2)
        frame_progress.pack(side=tk.TOP, pady=5)
        frame_progress_cheatsheet = CTkFrame(frame)
        lbl = CTkLabel(frame_progress_cheatsheet, text="Cheatsheet Progression")
        lbl.pack(side=tk.LEFT, padx=5)
        self.cheatsheet_progressbar = CTkProgressBar(frame_progress_cheatsheet, mode='determinate')
        self.cheatsheet_progressbar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.label_cheatsheet_progress = CTkLabel(frame_progress_cheatsheet, text="X/X")
        self.label_cheatsheet_progress.pack(side=tk.LEFT, padx=2)
        frame_progress_cheatsheet.pack(side=tk.TOP, pady=5)

    def set_autoscan_status(self):
        apiclient = APIClient.getInstance()
        status = apiclient.getAutoScanStatus()
        if status : 
            self.btn_autoscan.configure(text="Stop autoscan", command=self.click_stop_autoscan, image=self.image_stop)
        else:
            self.btn_autoscan.configure(text="Start autoscan", command=self.click_start_autoscan, image=self.image_start)
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
        self.label_cheatsheet_progress.configure(text=str(done)+"/"+str(int(total)))
        self.label_cheatsheet_progress.update_idletasks()

    
    def populate_results_frame(self, frame):
        self.form = FormPanel()
        
        self.treeview = self.form.addFormTreevw("results", ("Result type", "Time", "Criticity", "Target"), status="readonly", fill="both", side="top",expand=True)
        self.form.constructView(frame)

    def set_results(self):
        self.datamanager = DataManager.getInstance()
        self.label_host_count.configure(text="Hosts : "+str(self.infos.get("hosts_count", 0)))
        defects = self.datamanager.get("defects", '*', {}).values()
        self.treeview.reset()
        for defect in defects:
            self.treeview.addItem("", tk.END, defect.getId(), text="Security Defect", values=(defect.creation_time, defect.risk, defect.getDetailedString(onlyTarget=True)))

