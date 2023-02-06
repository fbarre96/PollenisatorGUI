"""
PollenisatorTreeview abstract class
Ttk treeview abstract class to be inherited added functions.
"""
import json
import os
import tkinter as tk
import tkinter.ttk as ttk

from bson.objectid import ObjectId
from bson.errors import InvalidId
from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.components.settings import Settings
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.components.filter import Filter, ParseError
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion


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
        self.views = {}  # Dict of views stored in this treeview.
        self.contextualMenu = None
        self.configureTags()
        datamanager = DataManager.getInstance().attach(self)

    def configureTags(self):
        self.tag_configure('OOS', background="grey")
        self.tag_configure('known_command', background="spring green")
        tags = Settings.getTags()
        for tag, color in tags.items():
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
        self.contextualMenu = tk.Menu(self.parentFrame, tearoff=0, background='#A8CF4D',
                                      foreground='white', activebackground='#A8CF4D', activeforeground='white')
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
                text_k = self.item(k)["text"]
                view_o = self.getViewFromId(str(k))
                if view_o is not None:
                    l.append((k, text_k, view_o))
            if l:
                l.sort(key=lambda t: t[2].key() if t[2] is not None else None)
                for index, (iid, _, _) in enumerate(l):
                    self.move(iid, nodeToSort, index)
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

    def deleteState(self, name):
        """
        Delete the given name state file
        file name is given in arguments and it must be stored as an hidden file in Pollenisator/local/states/ folder.
        Args:
            name: the name of this treeview to delete.
                  The full path to local/states folder and a Dot (".") will be prepended to the name.
        """
        try:
            path = os.path.join(PollenisatorTreeview.dir_path,
                                "../../../local/states/."+name)
            os.remove(path)
        except FileNotFoundError:
            pass

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
        try:
            self.contextualMenu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            print(e)
        finally:
            # make sure to release the grab (Tk 8.0a1 only)
            self.contextualMenu.grab_release()
        self.contextualMenu.focus_set()
        #self.contextualMenu.bind('<FocusOut>', self.popupFocusOut)

    def popupFocusOut(self, _event=None):
        """Called when the contextual menu loses focus. Closes it.
        Args:
            _event: default to None
        """
        print("popup closing :)")
        self.contextualMenu.unpost()

    def deleteSelected(self, _event):
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

    def filterTreeview(self, query, settings=None):
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
        if query.strip() != "":
            try:
                if settings.local_settings.get("quicksearch", False):
                    self.doFilterTreeview(query, False)
                else:
                    searcher = Filter(query, )
                    self.doFilterTreeview(searcher, True)
            except ParseError as e:
                tk.messagebox.showerror("Search error", str(e))
                return False
        
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

    def doFilterTreeview(self, query, show_hidden=True):
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
                self._brutSearcher(results_iid)
            else:
                self._brutTextSearcher(query)

    # def insert(self, *args, **kwargs):
    #     """Insert a new node in the treeview. Surcharge the ttk.Treeview insert method to check hidden nodes"""
    #     iid = args[2]
    #     return super().insert(*args, **kwargs)
        
    def _brutSearcher(self, results_iid, parentItem=''):
        """
        Check all children of the item given to see if their iid is in the resukts_iid.
        Args:
            results_iid: a list to complete with matching results iid
            parentItem: an parent treeview node to start from recurisve search
        """
        # Get all the children of the parentItem
        if parentItem in results_iid:
            self.item(parentItem, open=True)
            return True
        children = list(self.get_children(parentItem))
        # For each child, recursively call _brutSearcher
        atLeastOneChildAdded = False
        for item_id in children:
            child_added = self._brutSearcher(results_iid, item_id)
            # If the child is not in the results
            if not child_added:
                # Add the child to the list of detached items
                self._detached.append([item_id, parentItem])
                # Detach the child
                self.detach(item_id)
            else:
                # Get the view of the child
                self.item(parentItem, open=True)
                atLeastOneChildAdded = True
        return atLeastOneChildAdded

    def _brutTextSearcher(self, textSearch, parentItem=''):
        """
        Check all children of the item given to see if their text matches the textSearch
        Args:
            textSearch: text to search
            parentItem: an parent treeview node to start from recurisve search
        """
        # Get all the children of the parentItem
        nodetext = self.item(parentItem)["text"]
        if textSearch.lower() in nodetext.lower():
            self.item(parentItem, open=True)
            return True
        children = list(self.get_children(parentItem))
        # For each child, recursively call _brutSearcher
        atLeastOneChildAdded = False
        for item_id in children:
            child_added = self._brutTextSearcher(textSearch, item_id)
            # If the child is not in the results
            if not child_added:
                # Add the child to the list of detached items
                self._detached.append([item_id, parentItem])
                # Detach the child
                self.detach(item_id)
            else:
                # Get the view of the child
                self.item(parentItem, open=True)
                atLeastOneChildAdded = True
        return atLeastOneChildAdded

        