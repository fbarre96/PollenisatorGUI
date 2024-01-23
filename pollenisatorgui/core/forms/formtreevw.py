"""Widget "Table" using a ttk Treeview"""

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
from customtkinter import *
from pollenisatorgui.core.forms.form import Form
import pyperclip
from pollenisatorgui.core.application.dialogs.ChildDialogCombo import ChildDialogCombo
from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
import pollenisatorgui.core.components.utils as utils

class FormTreevw(Form):
    """
    Form field representing a multi-lined input.
    """

    def __init__(self, name, headings, default_values=None, **kwargs):
        """
        Constructor for a form text

        Args:
            name: the treeview name (id).
            headings: table headers
            default_values: default values for the Table as a dict, default is None
            kwargs: same keyword args as you would give to ttk.Treeview
                    Plus:
                        - doubleClickBinds : list of values to edit columns as:
                                        - None : Not editable
                                        - string : ask user to input a string
                                        - list : ask user to choose in a combo box one value in the list 

        """
        super().__init__(name)
        self.headings = headings
        self.default_values = default_values if default_values is not None else {}
        self.treevw = None
        self.kwargs = kwargs
        self.tvFrame = None
        self.scbVSel = None
        self.widgetMenuOpen = None
        self.contextualMenu = kwargs.get("contextualMenu", None)
        self.doubleClickBinds = kwargs.get("doubleClickBinds", None)
        self.f = None
        self._detached = set()
        self._cache = {}
        self.type = "dict"
        self.movingSelection = None
        self.lastMovedTo = None

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
        if self.contextualMenu is None:
            self._initContextualMenu(self.treevw)
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
            it = self.treevw.item(item)
            texts.append(it.get("text", "") + " " +
                         " ".join(it.get("values", [])))

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

    def recurse_insert(self, values, parent='', columnsLen=None, odd=False):
        """Recursive insert of a value in a table:
        Args:
            values: values to insert in the treeview
                    * If it is a dict : Recurse
                    * If it is a list : Add key without value and list values as subchildren
                    * If it is a str : Insert into parent
                    * If it is a tuple : Insert first value as text and other values as values in the same line
            parent: the parent node treeview id to insert values into
            columnsLen: a table with the width of each column as list of 2 int
            odd: insert value as an odd value (the line will be tagged odd and change color). Default is False
        Returns:
            Final size of columns as list of two int
        """
        child_odd = False
        if columnsLen is None:
            columnsLen = [self.f.measure(str(x)) for x in self.headings]
        if isinstance(values, dict):
            # treeview
            self.type = "dict"
            sorted_keys = sorted(list(values.keys()))
            for sorted_key in sorted_keys:
                key = sorted_key
                value = values[key]
                root = parent
                if isinstance(value, str):
                    self.treevw.insert(root, tk.END, None, text=key, values=[
                        str(value)], tags=("odd") if odd else ())
                    odd = not odd
                    columnsLen[0] = max(columnsLen[0], self.f.measure(key))
                    columnsLen[1] = min(
                        1000, max(columnsLen[1], self.f.measure(str(value))))
                elif isinstance(value, list):
                    if parent != '':
                        return 
                    root = self.treevw.insert(
                        root, tk.END, None, text=key, tags=("odd") if odd else ())
                    odd = not odd
                    columnsLen[0] = max(columnsLen[0], self.f.measure(key))
                    child_odd = False
                    for listValue in value:
                        self.treevw.insert(root, tk.END, None,
                                        text="", values=[str(listValue)], tags=("odd") if child_odd else ())
                        columnsLen[1] = min(1000, max(
                            columnsLen[1], self.f.measure(str(listValue))))
                        child_odd = not child_odd
                elif isinstance(value, tuple):
                    if len(value) == 0:
                        continue
                    value_arr = list(value[1:]) if len(value) > 1 else []
                    self.treevw.insert(root, tk.END, None, text=str(value[0]), values=value_arr, tags=("odd") if child_odd else ())
                    for i in range(len(value)):
                        try:
                            columnsLen[i] = min(1000, max(
                                columnsLen[i], self.f.measure(str(value[i]))))
                        except IndexError:
                            columnsLen.insert(i, min(1000, self.f.measure(str(value[i]))))
                    child_odd = not child_odd
                elif isinstance(value, dict):
                    parent = self.treevw.insert(
                        root, tk.END, None, text=key, tags=("odd") if odd else ())
                    odd = not odd
                    columnsLen[0] = max(columnsLen[0], self.f.measure(key))
                    columnsLen[1] = min(1000, max(
                        columnsLen[1], self.f.measure(str(value))))
                    columnsLen = self.recurse_insert(
                        value, parent=root, columnsLen=columnsLen, odd=odd)
        elif isinstance(values, list):
            # table like
            self.type = "list"
            for sub_list in values:
                if len(sub_list) == 0:
                        continue
                value_arr = list(sub_list[1:]) if len(sub_list) > 1 else []
                self.treevw.insert(parent, tk.END, None, text=str(sub_list[0]), values=value_arr, tags=("odd") if child_odd else ())
                for i in range(len(sub_list)):
                    try:
                        columnsLen[i] = min(1000, max(
                            columnsLen[i], self.f.measure(str(sub_list[i]))))
                    except IndexError:
                        columnsLen.insert(i, min(1000, self.f.measure(str(sub_list[i]))))
                child_odd = not child_odd
        return columnsLen

    def constructView(self, parent):
        """
        Create the text view inside the parent view given

        Args:
            parent: parent FormPanel.
        """
        from pollenisatorgui.core.components.settings import Settings
        w = self.getKw("width", 600)
        self.tvFrame = CTkFrame(
            parent.panel, width=w, height=0)
        h = self.getKw("height", len(self.default_values)+1)
        mh = self.getKw("max_height", 10)
        self.treevw = ttk.Treeview(self.tvFrame, height=min(h, mh))
        settings = Settings()
        font = tkfont.nametofont('TkTextFont')
        self.treevw.tag_configure("even", background=utils.getBackgroundColor(), font=tkfont.nametofont('TkTextFont'))
        self.treevw.tag_configure("odd", background=utils.getBackgroundSecondColor(), font=tkfont.nametofont('TkTextFont'))
        self.scbVSel = CTkScrollbar(self.tvFrame,
                                     orientation=tk.VERTICAL,
                                     command=self.treevw.yview, height=0)
        scbHSel = CTkScrollbar(
            self.tvFrame, orientation=tk.HORIZONTAL, command=self.treevw.xview)
        self.treevw.configure(yscrollcommand=self.scbVSel.set)
        self.treevw.configure(xscrollcommand=scbHSel.set)
        self.tvFrame.rowconfigure(0, weight=1)
        self.tvFrame.columnconfigure(0, weight=1)

        self.treevw.grid(row=0, column=0, sticky=tk.NSEW)
        self.scbVSel.grid(row=0, column=1, sticky=tk.NS)
        scbHSel.grid(row=1, column=0, sticky=tk.EW)
        if len(self.headings) > 1:
            self.treevw['columns'] = self.headings[1:]
        root = CTkLabel(self.tvFrame)
        self.f = tkfont.nametofont('TkTextFont')
        columnsLen = self.recurse_insert(self.default_values)
        listOfLambdas = [self.column_clicked("#"+str(i), False) for i in range(len(self.headings))]
        autoresize = self.getKw("auto_size_columns", True)
        for h_i, header in enumerate(self.headings):
            self.treevw.heading("#"+str(h_i), text=header, anchor="w", command=listOfLambdas[h_i])
            if autoresize:
                self.treevw.column("#"+str(h_i), anchor='w',
                               stretch=tk.YES, minwidth=columnsLen[h_i], width=columnsLen[h_i])
        
        emptyRowFound = False
        add_empty_row = self.getKw("add_empty_row", False)
        children = self.treevw.get_children()
        for child in children:
            item = self.treevw.item(child)
            if item["text"] == "":
                emptyRowFound = True
                break
        if self.getKw("status", "none") != "readonly":
            if not emptyRowFound and add_empty_row:
                tags = ("odd") if len(children) % 2 == 1 else ()
                self.treevw.insert('', tk.END, None, text="",
                                values=["" for x in range(len(self.headings)-1)], tags=tags)
            self.treevw.bind("<Double-Button-1>", self.OnDoubleClick)
            self.treevw.bind("<Delete>", self.deleteItem)
            self.treevw.bind("<Control-c>", self.copy)
            self.treevw.bind("<Alt-Down>",self.bDown)
            self.treevw.bind("<Alt-Up>",self.bUp)
            self.treevw.bind("<ButtonPress-1>",self.dragStart)
            self.treevw.bind("<ButtonRelease-1>",self.dragRelease, add='+')
            self.treevw.bind("<B1-Motion>",self.dragMove, add='+')
        self._initContextualMenu(self.treevw)
        binds = self.getKw("binds", {})
        for key, val in binds.items():
            self.treevw.bind(key, val)
        if parent.gridLayout:
            self.tvFrame.grid(row=self.getKw("row", 0), column=self.getKw(
                "column", 0), sticky=self.getKw("sticky", tk.NSEW), fill=self.getKw("fill", "both"), expand=self.getKw("expand", False))

        else:
            self.tvFrame.pack(side=self.getKw("side", "top"), anchor=self.getKw("anchor", None), padx=self.getKw(
                "padx", 10), pady=self.getKw("pady", 5), fill=self.getKw("fill", "both"), expand=self.getKw("expand", False))
        
    def column_clicked(self, col, reverse):
        """A lambda to call the statusbarController.statusbarClicked with the tag name clicked
        Args:
            name: the tag name clicked
        """
        return lambda : self.sort_column(self.treevw, col, reverse)
    
    def filter(self, *args, **kwargs):
        if kwargs.get("reset", True):
            children = list(self._detached) + list(self.treevw.get_children())
            self._detached = set()
        else:
            children = list(self.treevw.get_children())
        self._brut_searcher(children, *args, **kwargs)

    def _brut_searcher(self, children, *args, **kwargs):
        i_r = -1
        for item_id in children:
            allValid = True
            oneValid = False
            for iarg, arg in enumerate(args):
                if iarg == 0:
                    text = self.treevw.item(item_id)['text']
                else:
                    text = self.treevw.item(item_id)['values'][iarg-1]
                check_all = kwargs.get("check_all", True)
                if isinstance(arg, str):
                    is_valid = arg in text
                elif isinstance(arg, bool):
                    is_valid = arg
                elif isinstance(arg, list):
                    is_valid = text in arg
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
                self.treevw.reattach(item_id, '', i_r)
            elif oneValid and not check_all:
                i_r += 1
                self.treevw.reattach(item_id, '', i_r)
            else:
                self._detached.add(item_id)
                self.treevw.detach(item_id)
        self.resetOddTags()

    def sort_column(self, tv, col, reverse):
        if col != "#0":
            l = [(tv.set(k, col), k) for k in tv.get_children('')]
        else:
            l = [(tv.item(k)["text"],k) for k in tv.get_children('')]
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
        self._detached = set()
        if self.treevw is None:
            return
        for item in self.treevw.get_children():
            self.treevw.delete(item)

    def resetOddTags(self):
        for i, child in enumerate(self.treevw.get_children()):
            tags = ("odd") if i%2 != 0 else ()
            self.treevw.item(child, tags=tags)

    def deleteItem(self, _event=None):
        """Callback for <Del> event
        Remove the selected item in the treeview
        Args:
            _event: not used but mandatory"""
        for selected in self.treevw.selection():
            item = self.treevw.item(selected)
            if item["text"].strip() != "":
                self.treevw.delete(selected)
        self.resetOddTags()

    def addItem(self, parent="", insertPos="0", iid=None, **kwargs):
        self.treevw.insert(parent, insertPos, iid, **kwargs)
        self.resetOddTags()

    def setValue(self, values):
        self.reset()
        self.recurse_insert(values)

    def auto_resize_columns(self):
        columnsLen = [self.f.measure(str(x)) for x in self.headings]    
        for children in self.treevw.get_children():
            item = self.treevw.item(children)
            columnsLen[0] = max(columnsLen[0], self.f.measure(item["text"]))
            for i, value in enumerate(item["values"]):
                columnsLen[i+1] = max(columnsLen[i+1], self.f.measure(value))
        for h_i, header in enumerate(self.headings):
            self.treevw.column("#"+str(h_i), minwidth=columnsLen[h_i], width=columnsLen[h_i])

    def OnDoubleClick(self, event):
        """Callback for double click event
        Edit value of double clicked item
        Args:
            event: automatically filled when event is triggered.
        """
        item = self.treevw.identify("item", event.x, event.y)
        column = self.treevw.identify_column(event.x)
        columnNb = int(column[1:])
        values = self.treevw.item(item)["values"]
        if columnNb == 0:
            oldVal = self.treevw.item(item)["text"]
        else:
            try:
                oldVal = values[columnNb-1]
            except IndexError:
                oldVal = ""
        if self.doubleClickBinds is None:
            dialog = ChildDialogAskText(self.tvFrame, "New value for "+self.headings[columnNb].lower(), default=oldVal, multiline=True, width=100)
            self.tvFrame.wait_window(dialog.app)
            if dialog.rvalue is None:
                return
            newVal = dialog.rvalue
        else:
            binding = self.doubleClickBinds[columnNb]
            if binding is None:
                return
            elif callable(binding):
                newVal = binding(oldVal)
                if newVal is None:
                    return
            elif isinstance(binding, str):
                dialog = ChildDialogAskText(self.tvFrame, "New value for "+self.headings[columnNb].lower(), default=oldVal, multiline=True, width=100)
                self.tvFrame.wait_window(dialog.app)
                if dialog.rvalue is None:
                    return
                newVal = dialog.rvalue
            elif isinstance(binding, list):
                dialog = ChildDialogCombo(None, binding, "Choose one:")
                dialog.app.wait_window(dialog.app)
                newVal = dialog.rvalue
        if newVal is None:
            return
        if newVal.strip() == "" or newVal.strip() == oldVal.strip():
            return
        if columnNb == 0:
            self.treevw.item(item, text=newVal.strip())
        else:
            newVals = list(values)
            newVals[columnNb-1] = newVal.strip()
            self.treevw.item(item, values=newVals)
        emptyRowFound = False
        children = self.treevw.get_children()
        for child in children:
            item = self.treevw.item(child)
            if item["text"] == "":
                emptyRowFound = True
                break
        if not emptyRowFound:
            tags = ("odd") if len(children) % 2 == 1 else ()
            self.treevw.insert('', tk.END, None, text="",
                               values=["" for x in range(len(self.headings)-1)], tags=tags)
            currentHeight = len(self.treevw.get_children())
            if currentHeight < self.getKw("max_height", 5):
                self.treevw.configure(height=currentHeight)

    def selection(self):
        return self.treevw.selection()
    
    def item(self, iid, **kwargs):
        return self.treevw.item(iid, **kwargs)


    def getValue(self):
        """
        Return the form value. Required for a form.

        Returns:
            Return the entry value as string.
        """
        if self.type == "dict":
            ret = {}
            children = self.treevw.get_children()
            for child in children:
                item = self.treevw.item(child)
                if not item["values"]:
                    children_list = self.treevw.get_children(child)
                    if children_list:
                        for child_list in children_list:
                            ret[item["text"]] = ret.get(item["text"], [])
                            item_child_list = self.treevw.item(child_list)
                            if item_child_list["values"]:
                                ret[item["text"]].append(item_child_list["values"][0])
                    else:
                        ret[item["text"]] = ""
                else:
                    ret[item["text"]] = item["values"]
            return ret
        elif self.type == "list":
            ret = []
            children = self.treevw.get_children()
            for child in children:
                item = self.treevw.item(child)
                elem = []
                elem.append(item["text"])
                elem += list(item["values"])
                ret.append(elem)
            return ret

    def bDown(self, event=None):
        item_iid = self.treevw.selection()[0]
        children = self.treevw.get_children()
        iid_moving = children.index(item_iid)
        try:
            iid_moved_by = children[iid_moving+1]
            self.treevw.move(item_iid, '', iid_moving+1)
        except IndexError:
            pass
        return "break"


    def bUp(self, event=None):
        item_iid = self.treevw.selection()[0]
        children = self.treevw.get_children()
        iid_moving = children.index(item_iid)
        try:
            iid_moved_by = children[iid_moving-1]
            self.treevw.move(item_iid, '', iid_moving-1)
        except IndexError:
            pass
        return "break"

    def dragStart(self, event):
        tv = event.widget
        if tv.identify_row(event.y) not in tv.selection():
            tv.selection_set(tv.identify_row(event.y))    
            self.movingSelection = tv.identify_row(event.y)

    def dragRelease(self, event):
        if self.movingSelection is None or self.lastMovedTo is None:
            return
        tv = event.widget
        if tv.identify_row(event.y) in tv.selection():
            self.movingSelection = None
            self.lastMovedTo = None

    def dragMove(self, event):
        tv = event.widget
        rowToMove = tv.identify_row(event.y)
        moveto = tv.index(rowToMove)    
        self.lastMovedTo = rowToMove if rowToMove != self.movingSelection else self.lastMovedTo
        for s in tv.selection():
            tv.move(s, '', moveto)