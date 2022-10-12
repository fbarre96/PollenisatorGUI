import tkinter as tk
import tkinter.ttk as ttk
import pyperclip


class ScrollableTreeview(ttk.Frame):
    def __init__(self, root, columns, **kwargs):
        super().__init__(root)
        self.root = root
        self.columns = columns
        self.infos = []
        self.maxPerPage = kwargs.get("height", 10)
        self.currentPage = 0
        self.lastPage = 0
        self.pagePanel = None
        self.treevw = ttk.Treeview(self, style=kwargs.get("style",None), height=kwargs.get("height", 10))
        self.treevw['columns'] = columns
        self.treevw.tag_configure("odd", background='light gray')
        lbl = ttk.Label()
        self.f = tk.font.Font(lbl, "Sans", bold=True, size=10)
        self.columnsLen = [self.f.measure(column) for column in self.columns]
        listOfLambdas = [self.column_clicked("#"+str(i), False) for i in range(len(self.columns))]
        for h_i, header in enumerate(self.columns):
            self.treevw.heading("#"+str(h_i), text=header, anchor="w", command=listOfLambdas[h_i])
            self.treevw.column("#"+str(h_i), anchor='w',
                               stretch=tk.YES, minwidth=self.columnsLen[h_i]) # ,width=self.columnsLen[h_i]
        self.treevw.grid(row=0, column=0, sticky=tk.NSEW)
        for bindName, callback in kwargs.get("binds", {}).items():
            self.treevw.bind(bindName, callback)
        scbVSel = ttk.Scrollbar(self,
                                orient=tk.VERTICAL,
                                command=self.treevw.yview)
        scbHSel = ttk.Scrollbar(
            self, orient=tk.HORIZONTAL, command=self.treevw.xview)
        self.treevw.configure(yscrollcommand=scbVSel.set)
        self.treevw.configure(xscrollcommand=scbHSel.set)
        scbVSel.grid(row=0, column=1, sticky=tk.NS)
        scbHSel.grid(row=1, column=0, sticky=tk.EW)
        self.setPaginationPanel()
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.treevw.bind("<Control-c>", self.copy)
        self.treevw.bind('<Control-a>', self.selectAll)
        self.treevw.bind("<Escape>", self.unselect)
        self._initContextualMenu(self.treevw)

    def setPaginationPanel(self):
        if self.pagePanel is not None:
            for widget in self.pagePanel.winfo_children():
                widget.grid_forget()
            self.pagePanel.forget()
        self.pagePanel = ttk.Frame(self)
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
        self.pagePanel.grid(row=2, column=0)

    def unselect(self, event=None):
        for item in self.treevw.selection():
            self.treevw.selection_remove(item)

    def selectAll(self, event=None):
        self.treevw.selection_set(self.treevw.get_children())

    def bind(self, event_name, func):
        self.treevw.bind(event_name, func)

    def insert(self, parent, index, iid, text="",values=(), tags=()):
        if iid not in [x["iid"] for x in self.infos]:
            self.infos.append({"parent":parent,"iid":iid, "index":index, "text":text,"values":values,"tags":tags})
        nbLig = len(self.infos)
        prevLastPage = self.lastPage
        self.lastPage = int(nbLig / self.maxPerPage)
        if prevLastPage != self.lastPage:
            self.setPaginationPanel()
        res = None
        if int(nbLig % self.maxPerPage) == 0:
            self.lastPage -= 1
        if self.currentPage == self.lastPage:
            shown = nbLig % self.maxPerPage
            if shown < self.maxPerPage:
                res = self._insert(parent, index, iid, text, values, tags)
            
        return res
    
    def _insert(self, parent, index, iid, text="",values=(), tags=()):
        try:
            res = self.treevw.insert(parent, index, iid, text=text, values=values, tags=tags)
        except tk.TclError:
            return None
        self.columnsLen[0] = max(self.columnsLen[0], self.f.measure(text))
        self.treevw.column("#0", anchor='w',
                               stretch=tk.YES, minwidth=self.columnsLen[0], width=self.columnsLen[0])
        for i, val in enumerate(values):
            self.columnsLen[i+1] = min(1000, max(self.columnsLen[i+1], self.f.measure(str(val))))
            self.treevw.column("#"+str(i+1), anchor='w',
                            stretch=tk.YES, minwidth=self.columnsLen[i+1], width=self.columnsLen[i+1])
        self.resetOddTags()
        return res

    def item(self, iid, **kwargs):
        try:
            return self.treevw.item(iid, **kwargs)
        except tk.TclError as e:
            raise e
        
    def _initContextualMenu(self, parent):
        """Initialize the contextual menu for paperclip.
        Args:
            parent: the tkinter parent widget for the contextual menu
        """
        self.contextualMenu = tk.Menu(parent, tearoff=0, background='#A8CF4D',
                                      foreground='white', activebackground='#A8CF4D',
                                      activeforeground='white')
        parent.bind("<Button-3>", self.popup)
        self.contextualMenu.add_command(label="Copy", command=self.copy)
        self.contextualMenu.add_command(label="Close", command=self.close)

    def addContextMenuCommand(self, label, command):
        found = False
        for i in range(self.contextualMenu.index('end')+1):
            labelStr = str(self.contextualMenu.entrycget(i,'label') )
            if labelStr == label:
                found = True
                break
        if not found:
            self.contextualMenu.add_command(label=label, command=command)

    def close(self):
        """Option of the contextual menu : Close the contextual menu by doing nothing
        """
        pass

    def copy(self, _event=None):
        """Option of the contextual menu : Copy entry text to clipboard
        """
        selected = self.treevw.selection()
        texts = []
        for item in selected:
            it = self.treevw.item(item)
            texts.append(it.get("text", "") + " " +
                         " ".join(map(str,it.get("values", []))))

        pyperclip.copy("\n".join(texts))

    def popup(self, event):
        """
        Fill the self.widgetMenuOpen and reraise the event in the editing window contextual menu

        Args:
            event: a ttk Treeview event autofilled.
            Contains information on what treeview node was clicked.
        """
        self.widgetMenuOpen = event.widget
        self.contextualMenu.tk_popup(event.x_root, event.y_root)
        self.contextualMenu.focus_set()
        #self.contextualMenu.bind('<FocusOut>', self.popupFocusOut)

    def popupFocusOut(self, _event=None):
        """Callback for focus out event. Destroy contextual menu
        Args:
            _event: not used but mandatory
        """
        self.contextualMenu.unpost()

    def column_clicked(self, col, reverse):
        """A lambda to call the statusbarController.statusbarClicked with the tag name clicked
        Args:
            name: the tag name clicked
        """
        return lambda : self.sort_column(self.treevw, col, reverse)

    def sort_column(self, tv, col, reverse):
        if col == "#0":
            self.infos.sort(key=lambda info: info["text"], reverse=reverse)
        else:
            self.infos.sort(key=lambda info: str(info["values"][int(col[1:])-1]), reverse=reverse)
        tv.heading(col, command=self.column_clicked(col, not reverse))
        self.goToPage("first", force=True)

    def reset(self):
        """Reset the treeview values (delete all lines)"""
        for item in self.treevw.get_children():
            self.treevw.delete(item)
        self.infos = []
        self.setPaginationPanel()


    def resetOddTags(self):
        for i, child in enumerate(self.treevw.get_children()):
            tags = ("odd") if i%2 != 0 else ()
            self.treevw.item(child, tags=tags)

    def delete(self, _event=None):
        """Callback for <Del> event
        Remove the selected item in the treeview
        Args:
            _event: not used but mandatory"""
        for selected in self.treevw.selection():
            item = self.treevw.item(selected)
            if item["text"].strip() != "":
                self.treevw.delete(selected)
                try:
                    ind = [x["iid"] for x in self.infos].index(selected)
                    del self.infos[ind]
                except ValueError as e:
                    print(e)
        self.resetOddTags()

    def selection(self):
        return self.treevw.selection()
    
    def get_children(self):
        return self.treevw.get_children()

    def parent(self, item):
        return self.treevw.parent(item)

    def goToPage(self, p, force=False):
        if not isinstance(p, str):
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
        toInsert = self.infos[self.currentPage*self.maxPerPage:self.currentPage*self.maxPerPage+self.maxPerPage]
        for item in self.treevw.get_children():
            self.treevw.delete(item)
        for t in toInsert:
            self._insert(t["parent"], t["index"], t["iid"], t["text"], t["values"], t["tags"])
        self.setPaginationPanel()