import tkinter as tk
import tkinter.ttk as ttk
import pyperclip


class ScrollableTreeview(ttk.Frame):
    def __init__(self, root, columns, **kwargs):
        super().__init__(root)
        self.root = root
        self.columns = columns
        self.treevw = ttk.Treeview(self, style=kwargs.get("style",None), height=kwargs.get("height", None))
        self.treevw['columns'] = columns
        self.treevw.tag_configure("odd", background='light gray')
        lbl = tk.Label()
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
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.treevw.bind("<Control-c>", self.copy)
        self.treevw.bind('<Control-a>', self.selectAll)
        self.treevw.bind("<Escape>", self.unselect)
        self._initContextualMenu(self.treevw)

    def unselect(self, event=None):
        for item in self.treevw.selection():
            self.treevw.selection_remove(item)

    def selectAll(self, event=None):
        self.treevw.selection_set(self.treevw.get_children())

    def bind(self, event_name, func):
        self.treevw.bind(event_name, func)

    def insert(self, parent, index, iid, text="",values=(), tags=()):
        try:
            res = self.treevw.insert(parent, index, iid, text=text, values=values, tags=tags)
        except tk.TclError as e:
            raise e
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
        if col != "#0":
            l = [(tv.set(k, col), k) for k in tv.get_children('')]
        else:
            l = [(k, k)for k in tv.get_children('')]
        l.sort(reverse=reverse)
        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
            if index % 2 != 0:
                tv.item(k, tags=("odd"))
            else:
                tv.item(k, tags=())

        # reverse sort next time
        tv.heading(col, command=self.column_clicked(col, not reverse))

    def reset(self):
        """Reset the treeview values (delete all lines)"""
        for item in self.treevw.get_children():
            self.treevw.delete(item)

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
        self.resetOddTags()

    def selection(self):
        return self.treevw.selection()
    
    def get_children(self):
        return self.treevw.get_children()

    def parent(self, item):
        return self.treevw.parent(item)