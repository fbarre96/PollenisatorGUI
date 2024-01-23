"""View parent object. Handle node in treeview and present forms to user when interacted with."""

from pollenisatorgui.core.application.dialogs.ChildDialogGenericView import ChildDialogGenericView
from pollenisatorgui.core.application.dialogs.ChildDialogQuestion import ChildDialogQuestion
from pollenisatorgui.core.forms.formpanel import FormPanel
import pollenisatorgui.core.components.settings as settings
from pollenisatorgui.core.application.dialogs.ChildDialogToast import ChildDialogToast
import tkinter.messagebox
from tkinter import ttk
from tkinter import TclError
from customtkinter import *
from PIL import Image
import tkinter as tk
import pollenisatorgui.core.components.utils as utils


class ViewElement(object):
    """
    Defines a basic view to be inherited. Those functions are generic entry points to models.
    Most of them should not be redefined in other Views.
    Attributes:
        icon: icon name to show in treeview. Icon filename must be in icon directory
        cachedClassIcon: a cached loaded PIL image icon of ViewElement.icon. Starts as None.
    """
    icon = 'undefined.png'
    cachedClassIcon = None
    loadingicon = 'loading.png'
    cachedloadingicon = None
    multiview_class = None

    def __init__(self, appTw, appViewFrame, mainApp, controller):
        """Constructor
        Args:
            appTw: a PollenisatorTreeview instance to put this view in
            appViewFrame: an view frame to build the forms in.
            mainApp: the Application instance
            controller: a CommandController for this view.
        """
        self.appliTw = appTw
        self.appliViewFrame = appViewFrame
        self.mainApp = mainApp
        self.controller = controller
        self._form = None
        self._opened = False

    @property
    def form(self):
        """
        Returns the form of this view. If it is not yet created, it will create it.
        """
        if self._form is None:
            self._form = FormPanel()
        return self._form

    @classmethod
    def getClassIcon(cls):
        """
        Load the class icon in cache if it is not yet done, and returns it

        Return:
            Returns the ImageTk.PhotoImage icon representing this class .
        """
        from PIL import Image, ImageTk
        if cls.cachedClassIcon is None:
            path = utils.getIcon(cls.icon)
            cls.cachedClassIcon = ImageTk.PhotoImage(Image.open(path))
        return cls.cachedClassIcon
    
    @classmethod
    def getLoadingIcon(cls):
        """
        Load the class icon in cache if it is not yet done, and returns it

        Return:
            Returns the ImageTk.PhotoImage icon representing this class .
        """
        from PIL import Image, ImageTk
        if cls.cachedloadingicon is None:
            path = utils.getIcon(cls.loadingicon)
            cls.cachedloadingicon = ImageTk.PhotoImage(Image.open(path))
        return cls.cachedloadingicon

    def getIcon(self):
        """
        Load the object icon in cache if it is not yet done, and returns it

        Return:
            Returns the icon representing this object.
        """
        return self.__class__.getClassIcon()

    def addChildrenBaseNodes(self, newNode):
        """
        Add to the given node from a treeview the mandatory childrens.
        Will be redefined in children.

        Args:
            newNode: the newly created node we want to add children to.
        """
        # pass

    def opened(self):
        """Callback called when the view is opened"""
        if self._opened:
            return
        self._opened = True
        try:
            icon = self.appliTw.item(str(self.controller.getDbId()))["image"]
            self.appliTw.item(str(self.controller.getDbId()), image=ViewElement.getLoadingIcon())
            self.appliTw.update()
            self.appliTw.delete(str(self.controller.getDbId())+"|<Empty>")
        except tk.TclError as e:
            pass
        self._insertChildren()
        for module in self.mainApp.modules:
            if hasattr(module["object"], "_insertChildren"):
                module["object"]._insertChildren(self.controller.model.coll_name, self.controller.getData())
        try:
            self.appliTw.item(str(self.controller.getDbId()), image=icon)
        except tk.TclError:
            pass
        self.appliTw.update()
        
    def delete(self, _event=None, showWarning=True):
        """
        Entry point to the model doDelete function.

        Args:
            _event: automatically filled if called by an event. Not used
            showWarning: a boolean. If true, the user will be asked a confirmation before supression. Default to True.
        """
        ret = True
        if showWarning:
            dialog = ChildDialogQuestion(self.mainApp,
                                     "DELETE WARNING", "Becareful for you are about to delete this entry and there is no turning back.", ["Delete", "Cancel"])
            self.mainApp.wait_window(dialog.app)
            if dialog.rvalue != "Delete":
                return
        self.controller.doDelete()

    def getAdditionalContextualCommands(self):
        return {}

    def update(self, event=None):
        """
        Entry point to the model doUpdate function.

        Args:
            event: automatically filled if called by an event. Holds info on update clicked widget.
        Returns:
            * a boolean to shwo success or failure
            * an empty message on success, an error message on failure
        """
        res, msg = self.form.checkForm()
        if(res):
            form_values = self.form.getValue()
            form_values_as_dicts = ViewElement.list_tuple_to_dict(form_values)
            self.controller.doUpdate(form_values_as_dicts)
            try:
                caller = self.update_btn.btn
                toast = ChildDialogToast(self.appliViewFrame, "Done" , x=caller.winfo_rootx(), y=caller.winfo_rooty()+caller.winfo_reqheight(), width=caller.winfo_reqwidth())
                toast.show()
            except Exception:
                pass
            return True, ""
        else:
            tkinter.messagebox.showwarning(
                "Form not validated", msg, parent=self.appliViewFrame)
            return False, msg
        
    def _insertChildren(self):
        return

    def insert(self, _event=None):
        """
        Entry point to the model doInsert function.

        Args:
            _event: automatically filled if called by an event. Not used
        Returns:
            * a boolean to shwo success or failure
            * an empty message on success, an error message on failure
        """
        res, msg = self.form.checkForm()
        if(res):
            form_values = self.form.getValue()
            form_values_as_dicts = ViewElement.list_tuple_to_dict(form_values)
            res, msg = self.controller.doInsert(form_values_as_dicts)
            if not res:
                msg = "This element cannot be inserted, check for conflicts with existings elements."
                tkinter.messagebox.showerror(
                    "Insertion failed", msg, parent=self.appliViewFrame)
                return False, msg
            else:
                if isinstance(msg, tuple):
                    nbErrors = msg[0]
                    iid = msg[1]
                else:
                    iid = None
                    nbErrors = msg
                if nbErrors > 0:
                    msg = str(len(
                        res))+" were inserted, "+str(nbErrors)+" were not to avoid conflicts or out of wave elements."
                    tkinter.messagebox.showwarning(
                        "Insertion succeeded with warnings", msg, parent=self.appliViewFrame)
                    return True, msg
                else:
                    return True, str(iid)
        else:
            tkinter.messagebox.showwarning(
                "Form not validated", msg, parent=self.appliViewFrame)
            return False, msg

    def tagClicked(self, name):
        """Callback intermediate for tag clicked
        Ensure that the tag name clicked is added to View item
        Args:
            name: a tag name
        """
        return lambda _event: self.tagButtonClicked(name)
    
    def tagButtonClicked(self, name):
        """Callback for tag button clicked
        Ensure that the tag name clicked is set to View item
        Args:
            name: a tag name
        """
        self.controller.setTags([name])

    def completeModifyWindow(self, editable=True, addTags=True):
        """
        Add the buttons for an update window.
            -Submit button that validates the form with the update function.
            -Delete button that asks the user to delete the object with the delete function.
        """
        pan = self.form.addFormPanel()
        self.delete_image = CTkImage(Image.open(utils.getIcon("delete.png")))
        self.save_image = CTkImage(Image.open(utils.getIcon("save.png")))
        if editable:
            self.update_btn = pan.addFormButton("Submit", self.update, image=self.save_image)
            pan.addFormButton("Delete", self.delete, image=self.delete_image,
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
            # if addTags:
            #     registeredTags = settings.Settings.getTags()
            #     keys = list(registeredTags.keys())
            #     column = 0
            #     item_no = 0
            #     listOfLambdas = [self.tagClicked(keys[i]) for i in range(len(keys))]
            #     for registeredTag, color in registeredTags.items():
            #         if column == 0:
            #             panTags = self.form.addFormPanel(pady=0)
            #         s = ttk.Style(self.mainApp)
            #         try: # CHECK IF COLOR IS VALID
            #             if color == "transparent":
            #                 color = "white"
            #             CTkLabel(self.mainApp, fg_color=color)
            #         except tkinter.TclError as e:
            #             #color incorrect
            #             color = "gray97"
            #         btn_tag = panTags.addFormButton(registeredTag, listOfLambdas[item_no],  side="left", padx=1, pady=0)
            #         btn_tag.configure(fg_color=color, border_width=1, text_color="black")
            #         column += 1
            #         item_no += 1
            #         if column == 4:
            #             column = 0
        self.showForm()

    def clearWindow(self):
        self.form.clear()
        for widget in self.appliViewFrame.winfo_children():
            widget.destroy()

    def reopenView(self):
        self.clearWindow()
        self.form.clear()
        self.openModifyWindow()
        

    def showForm(self):
        """Resets the application view frame and start displaying the form in it
        """
        for widget in self.appliViewFrame.winfo_children():
            try:
                widget.destroy()
            except tk.TclError:
                pass
        self.form.constructView(self.appliViewFrame)

    def completeInsertWindow(self):
        """
        Add the button for an insert window.
            -Insert button that validate the form with the insert function.
        """
        pan = self.form.addFormPanel()
        pan.addFormButton("Insert", self.insert)
        for widget in self.appliViewFrame.winfo_children():
            widget.destroy()
        self.form.constructView(self.appliViewFrame)

    def hide(self, reason="manual_hide"):
        """Tells the application treeview to hide this node
        """
        self.appliTw.hide(str(self.controller.getDbId()), reason)

    def unhide(self):
        """Tells the application treeview to unhide this node
        """
        self.appliTw.unhide(self)

    def __str__(self):
        """
        Return the __str__ method of the model
        """
        return str(self.controller.getModelRepr())

    @classmethod
    def DbToTreeviewListId(cls, parent_db_id):
        """Converts a mongo Id to a unique string identifying a list of view elemnt given its parent
        Args:
            parent_db_id: the parent node mongo ID
        Returns:
            A string that should be unique to describe the parent list of viewelement node
        """
        if parent_db_id is None:
            return None
        return str(parent_db_id)

    def getParentId(self):
        """
        Return the id of the parent node in treeview.

        Returns:
            return the model parent id DbToTreeviewListId
        """
        return self.controller.getParentId()

    def getParentNode(self):
        """
        Return the parent node in treeview.
        """
        return self.__class__.DbToTreeviewListId(self.controller.getParentId())
    
    def openInDialog(self,is_insert=False):
        """
        Open a dialog to show the tool information.
        """
        default_title = "Modify" if not is_insert else "Insert"
        dialog = ChildDialogGenericView(self.mainApp, default_title, self, is_insert=is_insert)
        return dialog.rvalue
    
    def updateReceived(self, obj=None, old_obj=None):
        """Called when any view element update is received by notification.
        Resets the node tags according to database and hide it if "hidden" is in tags
        """
        if self.controller.getDbId() is None:
            return
        tags = self.controller.getTags()
        try:
            self.appliTw.item(str(self.controller.getDbId()), tags=tags)
        except TclError:
            pass
        if "hidden" in tags:
            self.hide("tags")

    def insertReceived(self):
        """Called when any view element insert is received by notificaiton
        To be overriden
        """
        pass

    def key(self):
        """Returns a key for sorting this node
        Returns:
            tuple, key to sort
        """
        return tuple([ord(c) for c in str(self.controller.getModelRepr()).lower()])

    @classmethod
    def list_tuple_to_dict(cls, list_of_tuple):
        """Transforms a list of 2-tuple to a dictionnary
        Args:
            list_of_tuple: a 2-tuple with (key, value)
        Returns:
            A dictionnary with all key-values pair inserted
        """
        ret = dict()
        for key, value in list_of_tuple:
            ret[key] = value
        return ret
