import tkinter as tk
import tkinter.ttk as ttk
import uuid
from customtkinter import *
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.application.paginable import Paginable
import pyperclip
from collections import OrderedDict


class ScrollableTreeview(Paginable):
    def __init__(self, root, columns, **kwargs):
        if not kwargs.get("paginate", True):
            maxPerPage = -1
        else:
            maxPerPage = kwargs.get("maxPerPage", 10)
        super().__init__(root, self.insert_items, self.empty_treeview, self.callback_get_value, lambda: 0, height=0, maxPerPage=maxPerPage)
        self.root = root
        self.columns = columns
        self._detached = set()
        self.autoresize = kwargs.get("autoresize", True)
        self.sort_keys = kwargs.get("sort_keys", None)
        self.content_view = self.getContentView()
        self.treevw = ttk.Treeview(self.content_view, style=kwargs.get("style",None), height=max(kwargs.get("height", 10), maxPerPage))
        if len(columns) > 1:
            self.treevw['columns'] = columns[1:]
        settings = Settings()
        self.treevw.tag_configure("odd", background=utils.getBackgroundSecondColor())
        lbl = CTkLabel(self)
        self.f = tk.font.Font(lbl, "Sans", bold=True, size=10)
        width = kwargs.get("width", None)
        if width is not None:
            w_per_column = width // len(self.columns)
        self.columnsLen = [self.f.measure(column) for column in self.columns]
        listOfLambdas = [self.column_clicked("#"+str(i), False) for i in range(len(self.columns))]
        for h_i, header in enumerate(self.columns):
            self.treevw.heading("#"+str(h_i), text=header, anchor="w", command=listOfLambdas[h_i])
            if width is not None:
                self.treevw.column("#"+str(h_i), anchor='w',
                                   stretch=tk.YES, minwidth=w_per_column, width=w_per_column)
            else:
                self.treevw.column("#"+str(h_i), anchor='w',
                               stretch=tk.YES, minwidth=self.columnsLen[h_i])
        self.treevw.grid(row=0, column=0, sticky=tk.NSEW)
        for bindName, callback in kwargs.get("binds", {}).items():
            self.treevw.bind(bindName, callback)
        scbVSel = CTkScrollbar(self.content_view,
                                orientation=tk.VERTICAL,
                                command=self.treevw.yview)
        scbHSel = CTkScrollbar(
            self.content_view, orientation=tk.HORIZONTAL, command=self.treevw.xview)
        self.treevw.configure(yscrollcommand=scbVSel.set)
        self.treevw.configure(xscrollcommand=scbHSel.set)
        scbVSel.grid(row=0, column=1, sticky=tk.NS)
        scbHSel.grid(row=1, column=0, sticky=tk.EW)
        self.setPaginationPanel()
        
       
        self.treevw.bind("<Control-c>", self.copy)
        self.treevw.bind('<Control-a>', self.selectAll)
        self.treevw.bind("<Escape>", self.unselect)
        self._initContextualMenu(self.treevw)

    def empty_treeview(self):
        for item in self.treevw.get_children():
            self.treevw.delete(item)

    def unselect(self, event=None):
        for item in self.treevw.selection():
            self.treevw.selection_remove(item)
            
    def callback_get_value(self, item, column):
        if column == 0:
            return item["text"]
        else:
            return item["values"][column-1]

    def selectAll(self, event=None):
        self.treevw.selection_set(self.treevw.get_children())

    def bind(self, event_name, func):
        self.treevw.bind(event_name, func)

    def insert(self, parent, index, iid, text="",values=(), tags=(), image=None, auto_update_pagination=True):
        res = None
        if iid is None:
            iid = str(uuid.uuid4())
        if str(iid) not in self.infos:
            res = self.addPaginatedInfo({"parent":parent,"iid":iid, "index":index, "text":text,"values":values,"tags":tags, "image":image}, auto_update_pagination=auto_update_pagination)
        return res
    
    def insert_items(self, items):
        res = None
        for t in items:
            res = self._insert(t["parent"], t["index"], t["iid"], t["text"], t["values"], t["tags"], t["image"])
        return res
    
    def _insert(self, parent, index, iid, text="",values=(), tags=(), image=None):
        kwargs = {}
        if image is not None:
            kwargs["image"] =image
        try:
            res = self.treevw.insert(parent, index, iid, text=text, values=values, tags=tags, **kwargs)
        except tk.TclError as e:
            return None
            
        if self.autoresize:
            self.columnsLen[0] = max(self.columnsLen[0], self.f.measure(text))
            self.treevw.column("#0", anchor='w',
                                stretch=tk.YES, minwidth=self.columnsLen[0], width=self.columnsLen[0])
            for i, val in enumerate(values):
                self.columnsLen[i+1] = min(1000, max(self.columnsLen[i+1], self.f.measure(str(val))))
                self.treevw.column("#"+str(i+1), anchor='w',
                                stretch=tk.YES, minwidth=self.columnsLen[i+1], width=self.columnsLen[i+1])
            # self.treevw.grid_forget()
            # self.treevw.grid(row=0, column=0, sticky=tk.NSEW) # TODO : DO BETTER FOR redraw...
        self.resetOddTags()
        return res

    def item(self, iid, **kwargs):
        try:
            self.treevw.item(iid, **kwargs)
        except tk.TclError as e:
            pass
        try:
            self.infos[str(iid)].update(kwargs)
        except ValueError as e:
            raise tk.TclError(e)
        return self.infos[str(iid)]
        
        
    def _initContextualMenu(self, parent):
        """Initialize the contextual menu for paperclip.
        Args:
            parent: the tkinter parent widget for the contextual menu
        """
        self.contextualMenu = utils.craftMenuWithStyle(parent)
        parent.bind("<Button-3>", self.popup)
        self.contextualMenu.add_command(label="Copy", command=self.copy)
        self.contextualMenu.add_command(label="Close", command=self.close)

        
    def addContextMenuCommand(self, label, command, replace=False):
        found = False
        for i in range(self.contextualMenu.index('end')+1):
            labelStr = str(self.contextualMenu.entrycget(i,'label') )
            if labelStr == label and not replace:
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
            it = self.item(item)
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
        self.contextualMenu.bind('<FocusOut>', self.popupFocusOut)

    def popupFocusOut(self, _event=None):
        """Callback for focus out event. Destroy contextual menu
        Args:
            _event: not used but mandatory
        """
        self.contextualMenu.unpost()

    

    

    def detach(self, item_id):
        try:
            self.treevw.detach(item_id)
            self._detached.add(item_id)
        except tk.TclError:
            pass

    def reattach(self, item_id, parent, index):
        try:
            self.treevw.reattach(item_id, parent, index)
            self._detached.discard(item_id)
        except tk.TclError:
            pass
    
    @classmethod
    def date_compare(cls, start, end, toCompare):
        dated = utils.stringToDate(start)
        datef = utils.stringToDate(end)
        toCompare = utils.stringToDate(toCompare)
        if dated is None or datef is None:
            return True
        return dated <= toCompare <= datef

    def column_clicked(self, col, reverse):
        return lambda : self.sort_column(self.treevw, col, reverse)

    def sort_column(self, tv, col, reverse):
        sort_key = None
        if self.sort_keys:
            sort_key = self.sort_keys[int(col[1:])]
        if sort_key is None:
            sort_key = str
        if col == "#0":
            sorted_values = sorted(self.infos.values(), key=lambda info: sort_key(info["text"]), reverse=reverse)
        else:
            sorted_values = sorted(self.infos.values(), key=lambda info: sort_key(str(info["values"][int(col[1:])-1])), reverse=reverse)
        new_infos = OrderedDict()
        for info in sorted_values:
            new_infos[info["iid"]] = info
        self.infos = new_infos
        tv.heading(col, command=self.column_clicked(col, not reverse))
        self.goToPage("first", force=True)

    def reset(self):
        """Reset the treeview values (delete all lines)"""
        for item in self.treevw.get_children():
            self.treevw.delete(item)
        self.infos = OrderedDict()
        self._detached = set()
        self.resetPagination()


    def resetOddTags(self):
        for i, child in enumerate(self.treevw.get_children()):
            odd_tag = ("odd") if i%2 != 0 else ()
            current_tags = self.item(child)["tags"]
            current_tags = [current_tags] if isinstance(current_tags, str) else list(current_tags)
            if "odd" in current_tags:
                current_tags.remove("odd")
            self.item(child, tags=[odd_tag]+current_tags)

    def delete(self, _event=None):
        """Callback for <Del> event
        Remove the selected item in the treeview
        Args:
            _event: not used but mandatory"""
        for selected in self.treevw.selection():
            try:
                item = self.item(selected)
                if item["text"].strip() != "":
                    self.treevw.delete(selected)
                    try:
                        del self.infos[selected]
                    except ValueError as e:
                        pass
            except tk.TclError:
                pass
        self.resetOddTags()

    def selection(self):
        return self.treevw.selection()
    
    def get_children(self, all=False):
        if all:
            return list(self.infos.keys())
        return self.treevw.get_children()
    
    def identify(self, *args, **kwargs):
        return self.treevw.identify(*args, **kwargs)
    
    def identify_column(self, *args, **kwargs):
        return self.treevw.identify_column(*args, **kwargs)

    def parent(self, item):
        return self.treevw.parent(item)

    

        