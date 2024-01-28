"""
PollenisatorTreeview abstract class
Ttk treeview abstract class to be inherited added functions.
"""
import json
import os
import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *

from bson.objectid import ObjectId
from bson.errors import InvalidId
from pollenisatorgui.core.application.dialogs.ChildDialogProgress import ChildDialogProgress
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.filter import Filter, ParseError
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
import pollenisatorgui.core.components.utils as utils



class PollenisatorTreeview(ttk.Treeview):
    """PollenisatorTreeview class
    Defines common treeview features not implemented by ttk.
    Deletion, expand, collapse, contextualMenu, selection.
    Object stored in a tree view must have a unique iid.
    To make it easier, treeview iid used are their mongo database ID.
    For lists it is given by the view DbToTreeview method.
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, appli, parentFrame):
        """
        Args:
            appli: a reference to the main Application object.
            parentFrame: the parent tkinter window object.
        """
        ttk.Treeview.__init__(self, parentFrame)
        self.appli = appli
        self.parentFrame = parentFrame
        self._detached = []  # Temporary detached objects (filtered objects)
        self._moved = []  # Objects that were moved to be repositioned later
        self._hidden = []  #  Hidden objects reference
        self._hidden_lkp = {}  # Hidden objects lookup table
        self.views = {}  # Dict of views stored in this treeview.
        self.contextualMenu = None
        self.configureTags()
        datamanager = DataManager.getInstance().attach(self)

    def configureTags(self):
        self.icon_oos = utils.loadIcon("ip_oos.png")
        s = Settings()
        oos_color = "gray30" if s.is_dark_mode() else "grey"
        self.tag_configure('OOS', background=oos_color, image=self.icon_oos)
        self.tag_configure('known_command', background="spring green")
        tags = Settings.getTags()
        for tag, color in tags.items():
            if color == "transparent":
                continue
            try:
                self.tag_configure(tag, background=color)
            except tk.TclError:
                #color does not exist
                pass
            
    def resetTags(self, dbId):
        """
        Remove all tags of the node with given id.
        Args:
            dbId: The databaseID of the object to remove tags of
        """
        try:
            # removes all tags, including todo
            self.item(str(dbId), tags=())
        except tk.TclError:
            pass

    def _initContextualsMenus(self):
        """
        Create the contextual menu of variables
        """
        self.contextualMenu = utils.craftMenuWithStyle(self.parentFrame)
        self.contextualMenu.selection = None
        self.contextualMenu.add_command(
            label="Sort children", command=self.sort)
        self.contextualMenu.add_command(
            label="Expand", command=self.expand)
        self.contextualMenu.add_command(
            label="Collapse", command=self.collapse)
        self.contextualMenu.add_command(
            label="Close", command=self.closeMenu)

    def closeMenu(self, _event=None):
        """Does nothing. Used to close the contextual menu."""
        return  # Do nothing.
    
    

    def sort(self, node=None):
        """
        Sort the children node of a treeview node. The sorting key is the node's text.
        Args:
            node: the parent node to sort children of. 
                If none is given, will sort last right clicked node.
                Default is None.
        """
        if node is None:
            try:
                nodeToSort = str(self.contextualMenu.selection)
            except:
                return
        else:
            nodeToSort = node
            
        l = []
        try:
            for k in self.get_children(nodeToSort):
                view_o = self.getViewFromId(str(k))
                if view_o is not None:
                    l.append((k, view_o))
            if l:
                l.sort(key=lambda t: t[1].key() if t[1] is not None else None)
                
                for index, (iid, _) in enumerate(l):
                    # way faster than move is to detach reattach at the end
                    #self.move(iid, nodeToSort, index)
                    self.detach(iid)
                    self.reattach(iid,nodeToSort, "end")
        except tk.TclError: # node given not found
            pass

    def getViewFromId(self, dbId):
        """
        Craft a specific Molde from the Models classes with just a valid Mongo Object Id.

        Args:
            dbId: the database Mongo Id to return a view of.
        """
        try:
            return self.views[dbId]["view"]
        except KeyError:
            return None

    def updateView(self, dbId, model):
        try:
            self.views[dbId]["view"].controller.model = model
        except KeyError:
            pass

    def switchExpandCollapse(self, openAction=True, nodeToExpand=None):
        """
        Expand or collapse all children recursivly of a treeview node.
        Args:
            openAction: Expand if True, Collapse if False.
        """
        if nodeToExpand is None:
            nodeToExpand = str(self.contextualMenu.selection)
        self.item(nodeToExpand, open=openAction)
        children = list(self.get_children(nodeToExpand))
        while len(children) > 0:
            child = children[0]
            children = children + list(self.get_children(child))
            self.item(child, open=openAction)
            del children[0]

    def _getTreeItemState(self, node, toFill):
        """
        Recursive function to get a list of children opened node.
        Args:
            node: the node will want to recursively list opened node of.
            toFill: a list to fill with opened nodes.
        """
        if self.item(node)["open"]:
            toFill.append(str(node))
        children = self.get_children(node)
        for child in children:
            self._getTreeItemState(child, toFill)
        return toFill

    def saveState(self, name):
        """
        Save opened nodes list state to a file.
        file name is given in arguments and stored as an hidden file in Pollenisator/local/states/ folder.
        Args:
            name: the name of this treeview to save.
                  A Dot (".") will be prepended to the name to make the resulting file hidden on linux.
        """
        toFill = []
        ret = self._getTreeItemState('', toFill)
        directory = os.path.join(
            PollenisatorTreeview.dir_path, "../../../local/states/")
        if not os.path.exists(directory):
            os.makedirs(directory)
        path = os.path.join(directory, "."+name)
        with open(path, mode="w") as f:
            f.write(json.dumps(ret))

    def loadState(self, name):
        """
        Load opened nodes list state from a file.
        Restore the state if its exists.
        file name is given in arguments and it must be stored as an hidden file in Pollenisator/local/states/ folder.
        Args:
            name: the name of this treeview to save.
                  The full path to local/states folder and a Dot (".") will be prepended to the name.
        """
        directory = os.path.join(
            PollenisatorTreeview.dir_path, "../../../local/states/")
        if not os.path.exists(directory):
            os.makedirs(directory)
        path = os.path.join(directory, "."+name)
        state = None
        try:
            with open(path, mode="r") as f:
                state = json.loads(f.read())
        except FileNotFoundError:
            state = None
        if state is not None:
            self.restoreTreeItemState(state)

   

    def restoreTreeItemState(self, state):
        """
        Restore the given state.
        Args:
            state: a list of iid to open in the treeview.
        """
        for k in state:
            try:
                self.item(k, open=True)
            except tk.TclError:
                pass

    def open(self, nodeId):
        try:
            self.item(nodeId, open=True)
        except tk.TclError:
            pass

    def expand(self):
        """
        Expand all children recursivly of a treeview node.
        """
        self.switchExpandCollapse(True)

    def collapse(self):
        """
        Collapse all children recursivly of a treeview node.
        """
        self.switchExpandCollapse(False)

    def doPopup(self, event):
        """
        Open the popup contextual menu of the treeview.

        Args:
            event: a ttk Treeview event autofilled. Contains information on what treeview node was clicked.
        """
        # display the popup menu
        self.contextualMenu.selection = self.identify(
            "item", event.x, event.y)
        try:
            self.contextualMenu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            print(e)
        finally:
            # make sure to release the grab (Tk 8.0a1 only)
            self.contextualMenu.grab_release()
        self.contextualMenu.focus_set()
        self.contextualMenu.bind('<FocusOut>', self.popupFocusOut)

    def popupFocusOut(self, _event=None):
        """Called when the contextual menu loses focus. Closes it.
        Args:
            _event: default to None
        """
        self.contextualMenu.unpost()

    def deleteSelected(self, _event=None):
        """
        Interface to delete a database object from an event.
        Prompt the user a confirmation window.
        Args:
            _event: not used, a ttk Treeview event autofilled. Contains information on what treeview node was clicked.
        """
        n = len(self.selection())
        dialog = ChildDialogQuestion(self.parentFrame,
                                     "DELETE WARNING", "Becareful for you are about to delete "+str(n) + " entries and there is no turning back.", ["Delete", "Cancel"])
        self.wait_window(dialog.app)
        if dialog.rvalue != "Delete":
            return
        if n == 1:
            view = self.getViewFromId(self.selection()[0])
            if view is None:
                return
            view.delete(None, False)
        else:
            toDelete = {}
            for selected in self.selection():
                view = self.getViewFromId(selected)
                if view is not None:
                    viewtype = view.controller.model.coll_name
                    if viewtype not in toDelete:
                        toDelete[viewtype] = []
                    toDelete[viewtype].append(view.controller.getDbId())
            apiclient = APIClient.getInstance()
            apiclient.bulkDelete(toDelete)
                

    def load(self, _event=None):
        """To be overriden
        Args:
            _event: not used, a ttk Treeview event autofilled. Contains information on what treeview node was clicked.
        """
        return

    def onTreeviewSelect(self, _event=None):
        """
        Return ObjectId of selection if it is a valid bson objectid.
        Else return the string of teeview iid.
        Make the viewframe empty.
        Args:
            _event: the treeview node clicked. Not used
        Returns:
            If selection is empty, returns None
            Return ObjectId of selection if it is a valid bson objectid.
            Else return the string of teeview iid.
        """
        selec = self.selection()
        if len(selec) == 0:
            return None
        item = selec[0]
            # the treeview node can either be an object view or a parent node used to store its children and to insert new nodes.
        ret = str(item)
        try:
            # This will raise an exception if the treeview item selected was not a database id.
            # This should only be the case for list of objects ids.
            # An object double click open the list item's type modifying form.
            ret = ObjectId(item)
        except InvalidId:
            pass # str
        if len(self.selection()) == 1:
            for widget in self.appli.viewframe.winfo_children():
                widget.destroy()
        return ret

    def filterTreeview(self, query, settings=None, text_search_allowed=True):
        """
        Deattach objects in the treeview that does not match the query and search settings.
        Args:
            query: filter query string
            settings: a dict of options:
                * "search_exact_match": for exact matching, default to False
                *  "search_show_hidden" : to enable showing hidden objects, default to False
             Default is None.
        Returns:
            True if the filter is done, else if an error occured. Most probably if the query is bad.
        """
        # Reload local settings and prepare search object.
        self.unhideAll()
        searcher = None
        apiclient = APIClient.getInstance()
        if query.strip() != "":
            dialog = ChildDialogProgress(self.parentFrame, "Searching ...",  msg="Querying ...", progress_mode="indeterminate")
            dialog.show()
            try:
                if self.lazyload:
                    if len(query.strip().split(" ")) == 1 and text_search_allowed:
                        textsearch = True
                    else:
                        textsearch = bool(settings.local_settings.get("textsearch", False))
                    searcher = apiclient.searchPentest(query.strip(), textonly=textsearch)
                    dialog.update(msg="Loading in treeview ...")
                    if searcher.get("success", True):
                        self.doFilterTreeview(searcher, True, keep_parents=settings.local_settings.get("keep_parents", True), dialog_progress=dialog)
                    else:
                        tk.messagebox.showerror("Search error", searcher.get("msg", "Unknown error"))
                        return False
                elif len(query.strip().split(" ")) == 1 and text_search_allowed: # 1 word search = text search
                    self.doFilterTreeview(query, False, keep_parents=settings.local_settings.get("keep_parents", True))
                elif settings.local_settings.get("textsearch", False) and text_search_allowed:
                    self.doFilterTreeview(query, False, keep_parents=settings.local_settings.get("keep_parents", True))
                else:
                    searcher = Filter(query, )
                    self.doFilterTreeview(searcher, True, keep_parents=settings.local_settings.get("keep_parents", True))
            except ParseError as e:
                tk.messagebox.showerror("Search error", str(e))
                return False
            finally:
                dialog.destroy()
        return True

    def unfilterAll(self):
        """Reattach all detached objects and reposition them.
        """
        detached = sorted(self._detached, key=lambda x: len(x[0]))
        for detached in self._detached:
            itemId = detached[0]
            parentId = '' if detached[1] is None else detached[1]
            try:
                self.reattach(itemId, parentId, 0)
            except tk.TclError:
                pass
        for moved in self._moved:
            itemId = moved[0]
            parentId = '' if moved[1] is None else moved[1]
            try:
                self.move(itemId, parentId, 0)
            except tk.TclError:
                pass
            view_o = self.getViewFromId(itemId)
            try:
                self.item(itemId, text=str(view_o.controller.getModelRepr()))
            except tk.TclError:
                pass
        for hidden in self._hidden:
            try:
                self.detach(str(hidden[0]))
            except tk.TclError:
                pass
        self._detached = []
        self._moved = []

    def unhide(self, reason):
        hiddens = self._hidden[::-1]
        toDel = []
        for i, hidden in enumerate(hiddens):
            itemId = hidden[0]
            parentId = '' if hidden[1] is None else hidden[1]
            
            if reason in hidden[2]:
                hidden[2].remove(reason)
            
            elif reason == "*":
                hidden[2] = []
            if len(hidden[2]) == 0:
                try:
                    self.reattach(itemId, parentId, 0)
                    toDel.append(i)
                except tk.TclError:
                    pass
        for i in toDel[::-1]:
            if hiddens[i][0] in self._hidden_lkp:
                del self._hidden_lkp[hiddens[i][0]]
            del hiddens[i]
        self._hidden = hiddens[::-1]

    
    def unhideNodeChildren(self, reason, node=None):
        if node is None:
            node = self.selection()[0]
        hiddens = self._hidden[::-1]
        for i, hidden in enumerate(hiddens):
            itemId = hidden[0]
            parentId = '' if hidden[1] is None else hidden[1]
            if str(parentId) != str(node):
                continue
            if reason in hidden[2]:
                hidden[2].remove(reason)
            elif reason == "*":
                hidden[2] = []
            if len(hidden[2]) == 0:
                try:
                    self.reattach(itemId, parentId, 0)
                except tk.TclError:
                    pass

    def unhideAll(self):
        """Reattach all hidden objects but keep in memory that they are hidden.
        """
        hiddens = self._hidden[::-1]
        for hidden in hiddens:
            itemId = hidden[0]
            parentId = '' if hidden[1] is None else hidden[1]
            try:
                self.reattach(itemId, parentId, 0)
            except tk.TclError:
                pass

    

    def doFilterTreeview(self, query, show_hidden=True, keep_parents=True, dialog_progress=None):
        """Apply the query on the treeview.
        Args:
            query: the core.Components.Search object that hold the informations
            show_hidden: will filter the hidden object as well and show them if they match the filter. Default to True.
        """
        # reattach every one
        self.unfilterAll()
        if query is not None:
            if isinstance(query, Filter):
                results_iid = query.getIds(self)
                if len(results_iid) != 0:
                    if show_hidden:
                        self.unhideAll()
                else:
                    tk.messagebox.showerror("No results", "No results found")
                    return
                self._brutSearcher(results_iid, "filter", keep_parents=keep_parents)
            elif isinstance(query, dict):
                total = 0
                results_iid = set()
                datamanager = DataManager.getInstance()
                for value in query.values():
                    total += len(value)
                if total > self.lazylimit:
                    tk.messagebox.showerror("Too many results", f"Too many results found ({total}), please refine your search")
                    return
                try:
                    self.delete("search")
                except tk.TclError:
                    pass
                node = self.insert("", 0, "search", text="Search results")
                for classtype, classitems in query.items():
                    clazz = datamanager.getClass(classtype)
                    if classitems:
                        obj = clazz(classitems[0])
                        view = self.appli.modelToView(clazz.coll_name, obj)
                        if hasattr(view.__class__, "multiAddInTreeview"):
                            # if dialog_progress is not None:
                            #     dialog_progress.update(msg="Adding %s" % clazz.coll_name)
                            view.__class__.multiAddInTreeview(self, self.appli.viewframe, self.appli, [clazz(c) for c in classitems], "search", addChildren=False, detailed=True)
                            results_iid.update(set([str(o.get("_id")) for o in classitems]))
                            continue
                    count = 0
                    size = len(classitems)
                    for classitem in classitems:
                        obj = clazz(classitem)
                        view = None
                        if obj is None:
                            return
                        model = obj
                        # if dialog_progress is not None:
                        #     dialog_progress.update(msg="Adding  %s results in treeview (%s/%s)" % clazz.coll_name, count, size)
                        view = self.appli.modelToView(clazz.coll_name, model)
                        count += 1
                        results_iid.add(str(model.getId()))
                        try:
                            if view is not None:
                                view.addInTreeview(node, addChildren=False)
                                #view.insertReceived()
                        except tk.TclError:
                            pass
                    
                if results_iid:
                    if show_hidden:
                        self.unhideAll()
                if dialog_progress is not None:
                    dialog_progress.update(msg="Filtering treeview ...")
                self._brutSearcher(results_iid, "filter", keep_parents=keep_parents)
            else:
                self._brutSearcher(query, "text", keep_parents=keep_parents)

    # def _brutSearcher(self, query_item, search_type, parentItem='', **kwargs):
    #     stack = [parentItem] if parentItem else list(self.get_children(''))
    #     keep_parents = kwargs.get("keep_parents", True)
    #     while stack:
    #         current_item = stack.pop()
    #         children = list(self.get_children(current_item))

    #         if search_type == "filter":
    #             is_match = current_item in query_item
    #         else:
    #             nodetext = self.item(current_item)["text"]
    #             is_match = str(query_item).lower() in nodetext.lower()

    #         has_child_match = any(child in stack for child in children)  # Check if any children are in the stack

    #         if is_match:
    #             self.item(current_item, open=True)
    #             if not keep_parents:
    #                 self._moved.append([current_item, self.parent(current_item)])
    #                 self.move(current_item, '', 'end')
    #             # Add children to the stack
    #             stack.extend(children)
    #             continue

    #         if keep_parents and has_child_match:
    #             self.item(current_item, open=True)
    #             # Add children to the stack
    #             stack.extend(children)
    #             continue

    #         # If no match and the item has children, add them to the stack
    #         if children:
    #             stack.extend(children)
    #         else:
    #             try:
    #                 self._detached.append([current_item, self.parent(current_item)])
    #                 # Detach the child
    #                 self.detach(current_item)
    #             except tk.TclError:
    #                 pass

    def _brutSearcher(self, query_item, search_type, parentItem='', **kwargs):
        if search_type == "filter":
            is_match = parentItem in query_item
        else:
            nodetext = self.item(parentItem)["text"]
            is_match =  str(query_item).lower() in nodetext.lower()
        keep_parents = kwargs.get("keep_parents", True)
        has_child_match = False
        # Nominal case = empty least
        children = list(self.get_children(parentItem))
        for item_id in children:
            matched = self._brutSearcher(query_item, search_type, item_id, **kwargs)
            if keep_parents and matched:
                has_child_match = True
        if is_match:
            #self.item(parentItem, open=True)
            if not keep_parents:
                self._moved.append([parentItem, self.parent(parentItem)])
                self.move(parentItem, '', 'end')
            return True
        if keep_parents and has_child_match:
            #self.item(parentItem, open=True)
            return True
        try:
            self._detached.append([parentItem, self.parent(parentItem)])
            # Detach the child
            self.detach(parentItem)
        except tk.TclError:
            pass
        return False
    
   