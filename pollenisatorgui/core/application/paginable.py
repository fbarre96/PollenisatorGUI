from collections import OrderedDict
from customtkinter import *
import tkinter.ttk as ttk


class Paginable(CTkFrame):

    def __init__(self, parent, callback_insert, callback_resetview, callback_get_value, callback_update_content_view, **kwargs) -> None:
        self.maxPerPage = kwargs.get("maxPerPage", 10)
        if "maxPerPage" in kwargs:
            del kwargs["maxPerPage"]
        super().__init__(parent, **kwargs)
        self.disablePagination = self.maxPerPage < 1
        self.currentPage = 0
        self.lastPage = 0
        self.pagePanel = None
        self.infos = OrderedDict()
        self._save_infos = None
        self.contentview = CTkFrame(self, height=0)
        self.contentview.grid(row=0, column=0, sticky="nsew")
        self.contentview.columnconfigure(0, weight=1)
        self.contentview.rowconfigure(0, weight=1)
        self.pagePanel = CTkFrame(self, height=0)
        self.pagePanel.grid(row=1, column=0, sticky="sew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=0)
        self.callback_insert = callback_insert
        self.callback_get_value = callback_get_value
        self.callback_resetview = callback_resetview
        self.update_contentview = callback_update_content_view

    def addPaginatedInfo(self, info, auto_update_pagination=True):
        if "iid" not in info:
            raise ValueError("iid key not found in info")
        self.infos[str(info["iid"])] = info
        if self.disablePagination:
            return self.callback_insert([info])
        nbLig = len(self.infos)
        prevLastPage = self.lastPage
        self.lastPage = int(nbLig / self.maxPerPage)
        if prevLastPage != self.lastPage and self.currentPage +5 < self.lastPage and auto_update_pagination:
            self.setPaginationPanel()
        if int(nbLig % self.maxPerPage) == 0:
            self.lastPage -= 1
        res = None
        if self.currentPage == self.lastPage:
            shown = nbLig % self.maxPerPage
            if shown < self.maxPerPage:
                res = self.callback_insert([info])
        return res  

    def getShownInfos(self):
        if self.disablePagination:
            return self.infos.values()
        start = self.currentPage * self.maxPerPage
        end = start + self.maxPerPage
        keys = list(self.infos.keys())[start:end]
        return [self.infos[key] for key in keys]
    
    def getContentView(self):
        return self.contentview
    
    def getInfos(self):
        return self.infos.values()

    def setPaginationPanel(self):
        if self.disablePagination:
            return 
        if self.pagePanel is not None:
            for widget in self.pagePanel.winfo_children():
                widget.grid_forget()
            self.pagePanel.forget()
        self.pagePanel = CTkFrame(self,  height=0) # adjust auto
        btn = ttk.Label(self.pagePanel, text="<<", style="Pagination.TLabel")
        btn.bind('<Button-1>', lambda event:self.goToPage("first"))
        btn.grid(padx=3)
        btn = ttk.Label(self.pagePanel, text="<", style="Pagination.TLabel")
        btn.bind('<Button-1>', lambda event:self.goToPage("previous"))
        btn.grid(row=0, column=1, padx=3)
        col = 2
        start = max(self.currentPage - 2, 0)
        i = start 
        while i <= self.lastPage and i <= start + 5:
            if i == self.currentPage:
                btn = ttk.Label(self.pagePanel, text=str(i), style="CurrentPagination.TLabel")
                btn.grid(column=col,row=0, padx=3)
            else:
                btn = ttk.Label(self.pagePanel, text=str(i), style="Pagination.TLabel")
                btn.bind('<Button-1>', lambda event:self.goToPage(event))
                btn.grid(column=col,row=0, padx=3)
            col +=1
            i += 1
        btn = ttk.Label(self.pagePanel, text=">", style="Pagination.TLabel")
        btn.bind('<Button-1>', lambda event:self.goToPage("next"))
        btn.grid(row=0, column=col, padx=3)
        btn = ttk.Label(self.pagePanel, text=">>", style="Pagination.TLabel")
        btn.bind('<Button-1>', lambda event:self.goToPage("last"))
        btn.grid(row=0, column=col+1, padx=3)
        self.pagePanel.grid(row=1, column=0)

    def resetPagination(self):
        self.currentPage = 0
        self.lastPage = 0
        self.setPaginationPanel()

    def goToPage(self, p, force=False):
        if self.disablePagination:
            return
        if not isinstance(p, int) and not isinstance(p, str):
            p = p.widget.cget("text")
        if p == "first":
            p = 0
        elif p == "last":
            p = self.lastPage
        elif p == "previous":
            p = max(self.currentPage - 1, 0)
        elif p == "next":
            p = min(self.currentPage + 1, self.lastPage)
        else:
            p = int(p)
        if p == self.currentPage and not force:
            return
        self.currentPage = p
        toInsert = self.getShownInfos()
        self.reset_contentview()
        self.insert_items(toInsert)
        self.setPaginationPanel()
        self.update_contentview()

    def reset_contentview(self):
        self.callback_resetview() 


    def insert_items(self, items):
        self.callback_insert(items)

    def filter(self, *args, **kwargs):
        if self._save_infos is not None:
            self.infos = self._save_infos
        subset_items = self._brut_searcher(self.infos, *args, **kwargs)
        self._save_infos = self.infos
        self.infos = OrderedDict()
        self.reset_contentview()
        for item in subset_items:
            self.addPaginatedInfo(self._save_infos[item], auto_update_pagination=False)
        self.setPaginationPanel()
        self.goToPage(0, force=True)
        self.update_contentview()

    def _brut_searcher(self, infos, *args, **kwargs):
        i_r = -1
        ret = []
        check_case = kwargs.get("check_case", True)
        for info_iid, info_value in infos.items():
            allValid = True
            oneValid = False
            for iarg, arg in enumerate(args):
                text = self.callback_get_value(info_value, iarg)
                check_all = kwargs.get("check_all", True)
                if isinstance(arg, str):
                    if not check_case:
                        text = str(text).lower()
                        arg = str(arg).lower()
                    is_valid = arg in str(text)
                
                elif isinstance(arg, bool):
                    is_valid = arg
                elif isinstance(arg, list):
                    is_valid = str(text) in arg
                if not is_valid:
                    allValid = False
                    if check_all:
                        break
                else:
                    oneValid = True
                    if not check_all:
                        break
            if allValid and check_all:
                i_r += 1
                ret.append(info_iid)
            elif oneValid and not check_all:
                i_r += 1
                ret.append(info_iid)
            
        return ret
        