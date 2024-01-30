"""This class pop a fix view form in a subdialog"""

import tkinter as tk
import tkinter.ttk as ttk
from customtkinter import *
from PIL import ImageTk, Image
from pollenisatorgui.core.application.dialogs.ChildDialogFixView import ChildDialogFixView
import pollenisatorgui.core.components.utils as utils


class ChildDialogFixes:
    """
    Open a child dialog of a tkinter application to answer a question.
    """
    def __init__(self, parent, defectView=None):
        """
        Open a child dialog of a tkinter application to edit fixes settings.

        Args:
            parent: the tkinter parent view to use for this window construction.
        """
        self.app = CTkToplevel(parent)
        self.app.attributes("-type", "dialog")
        self.app.title("Edit defect fixes")
        self.app.resizable(True, True)
        self.app.bind("<Escape>", self.cancel)
        self.rvalue = None
        self.lastMovedTo = None
        self.pane_base_height = 31
        self.defectView = defectView
        self.fixes = defectView.controller.getData().get("fixes", [])
        appFrame = CTkFrame(self.app)
        
        self.parent = None
        self.initUI(appFrame)
        ok_button = CTkButton(appFrame, text="OK")
        ok_button.pack(side="right", padx=5, pady=10)
        ok_button.bind('<Button-1>', self.okCallback)
        cancel_button = CTkButton(appFrame, text="Cancel", 
                               fg_color=utils.getBackgroundColor(), text_color=utils.getTextColor(),
                               border_width=1, border_color="firebrick1", hover_color="tomato")
        cancel_button.pack(side="right", padx=5, pady=10)
        cancel_button.bind('<Button-1>', self.cancel)
        appFrame.pack(fill=tk.BOTH, ipady=10, ipadx=10, expand=True)

        self.app.transient(parent)
        try:
            self.app.wait_visibility()
            self.app.transient(parent)
            self.app.grab_set()
            self.app.focus_force()
            self.app.lift()
        except tk.TclError:
            pass

    def cancel(self, _event=None):
        """called when canceling the window.
        Close the window and set rvalue to False
        Args:
            _event: Not used but mandatory"""
        self.rvalue = None
        self.app.destroy()

    def okCallback(self, _event=None):
        """called when pressing the validating button
        Close the window if the form is valid.
        Set rvalue to True and perform the defect update/insert if validated.
        Args:
            _event: Not used but mandatory"""
        
        self.rvalue = self.fixes
        self.app.destroy()

    def initUI(self, parent):
        """
        Initialize window and widgets.
        """
        if self.parent is not None:  # Already initialized
            self.reset()
            self.fillWithFixes()
            return
        self.parent = parent
        ###Fixes TABLE ###
        self.rowHeight = 20
        self.style = ttk.Style()
        self.style.configure('Report.Treeview', rowheight=self.rowHeight)
       
        # FIXES TREEVW	
        fixesLabelFrame = ttk.LabelFrame(parent, text="Fixes table")	
        self.paned = tk.PanedWindow(fixesLabelFrame, orient=tk.VERTICAL, height=400)
        self.frameTw = CTkFrame(self.paned)
        self.treevw = ttk.Treeview(self.frameTw, style='Report.Treeview', height=0)
        self.treevw['columns'] = ('execution', 'gain')
        self.treevw.heading("#0", text='Title', anchor=tk.W)
        self.treevw.column("#0", anchor=tk.W, width=150)
        self.treevw.heading('execution', text='Execution')
        self.treevw.column('execution', anchor='center', width=40)
        self.treevw.heading('gain', text='Gain')
        self.treevw.column('gain', anchor='center', width=40)
        
        self.treevw.bind("<Double-Button-1>", self.OnDoubleClick)
        self.treevw.bind("<Delete>", self.deleteSelectedItem)
        self.treevw.bind("<Alt-Down>",self.bDown)
        self.treevw.bind("<Alt-Up>",self.bUp)
        self.treevw.bind("<ButtonPress-1>",self.dragStart)
        self.treevw.bind("<ButtonRelease-1>",self.dragRelease, add='+')
        self.treevw.bind("<B1-Motion>",self.dragMove, add='+')
        self.treevw.grid(row=0, column=0, sticky=tk.NSEW)
        scbVSel = CTkScrollbar(self.frameTw,
                                orientation=tk.VERTICAL,
                                command=self.treevw.yview)
        self.treevw.configure(yscrollcommand=scbVSel.set)
        scbVSel.grid(row=0, column=1, sticky=tk.NS)
        self.frameTw.pack(side=tk.TOP, fill=tk.BOTH, padx=5, pady=10)
        self.frameTw.columnconfigure(0, weight=1)
        self.frameTw.rowconfigure(0, weight=1)
        ### OFFICE EXPORT FRAME ###
        belowFrame = CTkFrame(self.paned)
        frameBtn = CTkFrame(belowFrame)
        self.buttonUpImage = CTkImage(Image.open(utils.getIcon('up-arrow.png')))
        self.buttonDownImage = CTkImage(Image.open(utils.getIcon('down-arrow.png')))
        # use self.buttonPhoto
        btn_down = CTkButton(frameBtn, image=self.buttonDownImage, text="",command=self.bDown)
        btn_down.pack(side="left", anchor="center")
        btn_up = CTkButton(frameBtn, image=self.buttonUpImage, text="", command=self.bUp)
        btn_up.pack(side="left", anchor="center")
        btn_delFix = CTkButton(
            frameBtn, text="Remove selection", command=self.deleteSelectedItem)
        btn_delFix.pack(side=tk.RIGHT, padx=5)
        btn_addFix = CTkButton(
            frameBtn, text="Add a fix", command=self.addFixCallback)
        btn_addFix.pack(side=tk.RIGHT, padx=5)
        frameBtn.pack(side=tk.TOP, pady=5)
        belowFrame.pack(side=tk.TOP, fill=tk.BOTH)
        self.paned.add(self.frameTw)
        self.paned.add(belowFrame)
        self.paned.pack(fill=tk.BOTH, expand=1)
        fixesLabelFrame.pack(side=tk.TOP, fill=tk.BOTH, pady=10)	
        self.fillWithFixes()

    def bDown(self, event=None):
        item_iid = self.treevw.selection()[0]
        children = self.treevw.get_children()
        iid_moving = children.index(item_iid)
        try:
            iid_moved_by = children[iid_moving+1]
            self.treevw.move(item_iid, '', iid_moving+1)
            self.fixes[iid_moving+1], self.fixes[iid_moving] = self.fixes[iid_moving], self.fixes[iid_moving+1]
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
            self.fixes[iid_moving-1], self.fixes[iid_moving] = self.fixes[iid_moving], self.fixes[iid_moving-1]
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
            moved = tv.index(s) 
            if moved != moveto:
                tv.move(s, '', moveto)
                self.fixes[moved], self.fixes[moveto] = self.fixes[moveto], self.fixes[moved]
                
    def deleteSelectedItem(self, _event=None):
        """
        Remove selected defect from treeview
        Args:
            _event: not used but mandatory
        """
        try:
            selected = self.treevw.selection()[0]
        except IndexError:
            return
        self.treevw.delete(selected)
        ind = [fix["title"] for fix in self.fixes].index(str(selected))
        del self.fixes[ind]
        self.resizeTreeview()

    def reset(self):
        """
        reset defect treeview by deleting every item inside.
        """
        for item in self.treevw.get_children():
            self.treevw.delete(item)
        self.fixes = []
        self.resizeTreeview()

    def addFixCallback(self):
        """Open an insert defect view form in a child window"""
        dialog = ChildDialogFixView(self.parent, None)
        self.parent.wait_window(dialog.app)
        if dialog.rvalue is None:
            return
        self.addFixInTreevw(dialog.rvalue)

    def OnDoubleClick(self, event):
        """
        Callback for double click on treeview.
        Opens a window to update the double clicked defect view.
        Args:
            event: automatically created with the event catch. stores data about line in treeview that was double clicked.
        """
        item = self.treevw.identify("item", event.x, event.y)
        if item is None or item == '':
            return
        ind = [fix["title"] for fix in self.fixes].index(str(item))
        fix = self.fixes[ind]
        dialog = ChildDialogFixView(self.parent, fix)
        self.parent.wait_window(dialog.app)
        if dialog.rvalue is None:
            return
        self.fixes[ind] = dialog.rvalue 
        self.treevw.item(item, text=dialog.rvalue["title"], values=(dialog.rvalue["execution"], dialog.rvalue["gain"]))

    def resizeTreeview(self):
        currentHeight = len(self.treevw.get_children())
        self.treevw.configure(height=currentHeight)
        sx, sy = self.paned.sash_coord(0)
        if sy <= (currentHeight)*self.rowHeight + self.pane_base_height:
            self.paned.paneconfigure(self.frameTw, height=(currentHeight)*self.rowHeight + self.pane_base_height)

    def fillWithFixes(self):	
        """	
        Fetch remarks and fill the remarks table with them.	
        """	
        for fix in self.fixes:
            try:
                self.treevw.insert('', "end", fix["title"], text=fix["title"], values=(fix["execution"], fix["gain"],))
            except:
                pass
        self.resizeTreeview()

    def addFixInTreevw(self, fix):
        try:
            self.treevw.insert('', "end", fix["title"], text=fix["title"], values=(fix["execution"], fix["gain"],))
            self.fixes.append(fix)
        except:
            pass
        self.resizeTreeview()