import tkinter as tk
from pollenisatorgui.core.application.dialogs.ChildDialogToast import ChildDialogToast
from pollenisatorgui.core.forms.form import Form

import tkinter.ttk as ttk
from customtkinter import *
import tkinter.messagebox
from pollenisatorgui.core.application.pollenisatorentry import PopoEntry

class FormSearchBar(Form):
    """
    Form field representing a string input.
    """

    def __init__(self, name, searchCallback, panel_to_fill, list_of_forms_to_fill, default="", **kwargs):
        """
        Constructor for a form entry

        Args:
            name: the entry name (id).
            regexValidation: a regex used to check the input in the checkForm function., default is ""
            default: a default value for the Entry, defauult is ""
        """
        super().__init__(name)
        self.searchCallback = searchCallback
        self.panel_to_fill = panel_to_fill
        self.list_of_forms_to_fill = list_of_forms_to_fill
        self.default = default
        self._results = None
        self.kwargs = kwargs
        self.entry = None
        self.result_form = None
        self.options_forms = []
        self.results_forms = {}

    def constructView(self, parent):
        """
        Create the string view inside the parent view given

        Args:
            parent: parent FormPanel.
        """
        self.val = tk.StringVar()
        self.parent = parent
        frame = CTkFrame(parent.panel)
        lbl = CTkLabel(frame, text=self.name+" : ")
        lbl.grid(column=0, row=0)
        self.entry = PopoEntry(frame, textvariable=self.val, width=200)
        self.entry.grid(column=1, row=0)
        self.val.set(self.default)
        
        values = []
        if self.default != "":
            values.append(self.default)
        if self.result_form is None:
            lbl = CTkLabel(frame, text="Search results : ")
            lbl.grid(column=0, row=1)
            self.result_form = CTkComboBox(frame, values=values, width=200, state="readonly")
            self.result_form.grid(column=1, row=1)
        self.result_form.configure( command= self.postSelect)
        self.result_form.bind('<<ComboboxSelected>>', self.postSelect)
        if self.default != "":
            self.result_form.set(self.default)
        
        self.entry.bind('<Key-Return>', self.updateValues)
        if self.getKw("autofocus", False):
            self.entry.focus_set()
        if parent.gridLayout:
            frame.grid(row=self.getKw("row", 0), column=self.getKw("column", 0), **self.kwargs)
        else:
            frame.pack(side=self.getKw("side", "top"), padx=self.getKw("padx", 10), pady=self.getKw("pady", 5), **self.kwargs)
        

   
    def updateValues(self, _event=None):
        options = {}
        for form, option_name in self.options_forms:
            options[option_name] = form.getValue()
        self._results, err_msg = self.searchCallback(self.val.get(), **options)
        if self._results is None:
            tkinter.messagebox.showinfo("SearchBar is not responding", err_msg)
            self.result_form['values'] = [self.val.get()]
            self.result_form.set(self.val.get())
            return
        list_choice = []
        for result in self._results:
            if isinstance(result["TITLE"], str):
                list_choice.append(result["TITLE"])
        self.result_form.configure(values=list_choice)
        if len(list_choice) == 0:
            self.result_form.set("")
            toast = ChildDialogToast(self.parent, "No results found" , 
                                     x=self.result_form.winfo_rootx()+self.result_form.winfo_reqwidth(), y=self.result_form.winfo_rooty(), width=self.result_form.winfo_reqwidth())
            toast.show()
        if len(list_choice) > 0:
            self.result_form.set(list_choice[0])
        if len(list_choice) == 1:
            self.postSelect()

    def fillResults(self, selected):
        for key, value in selected.items():
            if key.lower() in self.results_forms:
                resultform = self.results_forms[key.lower()]
                form = resultform.get("form")
                callback = resultform.get("fill_callback")
                if callback is not None:
                    callback(form, value)
                else:
                    if getattr(form, "addItem", None) is None:
                        form.setValue(value)
                    else:
                        if isinstance(value, dict):
                            form.addItem(**value)
                    
    def postSelect(self, _event=None):
        selected = self.getValue()
        if selected is None:
            return
        if self.results_forms:
            self.fillResults(selected)
            return
        for subform in self.panel_to_fill.subforms:
            if getattr(subform, "subforms", None) is not None: # 1 depth max
                for subform_depth in subform.subforms:
                    if getattr(subform_depth, "subforms", None) is None:
                        if subform_depth.name.lower() in selected.keys():
                            if subform_depth.name.lower() not in [tup[1] for tup in self.options_forms]:
                                if getattr(subform_depth, "addItem", None) is None:
                                    subform_depth.setValue(selected[subform_depth.name.lower()])
                                else:
                                    itemToAdd = selected[subform_depth.name.lower()]
                                    if isinstance(itemToAdd, dict):
                                        subform_depth.addItem(**itemToAdd)
            else:
                if subform.name.lower() not in [tup[1] for tup in self.options_forms]:
                    if subform.name.lower() in selected.keys():
                        if getattr(subform, "addItem", None) is None:
                            subform.setValue(selected[subform.name.lower()])
                        else:
                            itemToAdd = selected[subform.name.lower()]
                            if isinstance(itemToAdd, dict):
                                subform.addItem(**itemToAdd)

    def getValue(self):
        """
        Return the form value. Required for a form.

        Returns:
            Return the entry value as string.
        """
        title = self.result_form.get()
        if self._results is not None:
            for elem in self._results:
                if elem["TITLE"] == title:
                    return elem
        return None

    def setFocus(self):
        self.entry.focus_set()

    def addOptionForm(self, optionForm, optionName):
        self.options_forms.append((optionForm, optionName))
        optionForm.bind('<Key-Return>', self.updateValues)

    def addResultForm(self, resultForm, resultName, **kwargs):
        self.results_forms[resultName.lower()] = {"form":resultForm, "fill_callback":kwargs.get("fill_callback", None)}
        
    def setResultForm(self, resultForm):
        self.result_form = resultForm