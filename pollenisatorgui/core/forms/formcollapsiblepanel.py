"""A collapsible panel form field."""

import tkinter.ttk as ttk
from customtkinter import *
import tkinter as tk
from pollenisatorgui.core.application.CollapsibleFrame import CollapsibleFrame

from pollenisatorgui.core.forms.formpanel import FormPanel


class FormCollapsbilePanel(FormPanel):
    """
    Form field representing a collapsible panel. It is composed of other forms.
    Additional kwargs values:
        grid: set the layout to grid, default to False
    Default setted values:
        width=500
        if pack : padx = 10, pady = 5, side = top, fill = x
        if grid: row = column = 0 sticky = "East"
    """

    def __init__(self, text, **kwargs):
        """
        Constructor for a panel.
        """
        super().__init__(**kwargs)
        self.text = text
        self.kwargs = kwargs
        self.gridLayout = self.getKw("grid", False)

    def constructView(self, parent):
        """
        Create the panel view by constructing all subforms views inside a tkinter panel the parent view given.
        Args:
            parent: parent view or parent FormPanel.
        """
        self.panel_frame = CollapsibleFrame(parent.panel, self.text, fg_color=self.getKw("fg_color", None), height=self.getKw("height", 20), 
                                      interior_padx=self.getKw("interior_padx", 0), interior_pady=self.getKw("interior_pady", 0))
        self.panel = self.panel_frame.interior
        self.populateView(parent)

    def populateView(self, parent):
        try:
            if self.make_uniform_column is not None:
                self.makeUniformColumn(self.make_uniform_column)
            
            for form in self.subforms:
                form.constructView(self)
            self.panel_frame.update_width()
            if isinstance(parent, FormPanel):  # Panel is a subpanel
                if parent.gridLayout:

                    self.panel_frame.grid(column=self.getKw(
                        "column", 0), row=self.getKw("row", 0), sticky=self.getKw("sticky", tk.NSEW), **self.kwargs)
                else:
                    self.panel_frame.pack(fill=self.getKw("fill", "both"), side=self.getKw(
                        "side", "top"), pady=self.getKw("pady", 5), padx=self.getKw("padx", 10),  **self.kwargs)
            else:  # Master panel, packing
                is_grid = "row" in self.kwargs or "column" in self.kwargs
                if not is_grid:
                    self.panel_frame.pack(fill=self.getKw("fill", "both"), side="top", pady=self.getKw("pady", 5), padx=self.getKw("padx", 30))
                else:
                    self.panel_frame.grid(sticky=self.getKw("sticky", tk.NSEW), row=self.getKw("row", 0), column=self.getKw("column", 0), pady=self.getKw("pady", 5), padx=self.getKw("padx", 30))
        except Exception as e:
            raise Exception("Error while populating view of panel named '" + self.name + "' : " + str(e))
            
