"""A special form that contains all other forms"""

import tkinter.ttk as ttk
from customtkinter import *
import tkinter as tk
from pollenisatorgui.core.forms.formcombo import FormCombo
from pollenisatorgui.core.forms.formchecklist import FormChecklist
from pollenisatorgui.core.forms.formmarkdown import FormMarkdown
from pollenisatorgui.core.forms.formstr import FormStr
from pollenisatorgui.core.forms.formtext import FormText
#from pollenisatorgui.core.forms.formmarkdown import FormMarkdown
from pollenisatorgui.core.forms.formbutton import FormButton
from pollenisatorgui.core.forms.formdate import FormDate
from pollenisatorgui.core.forms.formlabel import FormLabel
from pollenisatorgui.core.forms.formimage import FormImage
from pollenisatorgui.core.forms.formfile import FormFile
from pollenisatorgui.core.forms.formhidden import FormHidden
from pollenisatorgui.core.forms.formtreevw import FormTreevw
from pollenisatorgui.core.forms.formcheckbox import FormCheckbox
from pollenisatorgui.core.forms.formswitch import FormSwitch
from pollenisatorgui.core.forms.formhelper import FormHelper
from pollenisatorgui.core.forms.formsearchbar import FormSearchBar
from pollenisatorgui.core.forms.formseparator import FormSeparator

from pollenisatorgui.core.forms.form import Form


class FormPanel(Form):
    """
    Form field representing a panel. It is composed of other forms.
    Additional kwargs values:
        grid: set the layout to grid, default to False
    Default setted values:
        width=500
        if pack : padx = 10, pady = 5, side = top, fill = x
        if grid: row = column = 0 sticky = "East"
    """

    def __init__(self, **kwargs):
        """
        Constructor for a panel.
        """
        super().__init__("main panel")
        self.subforms = []
        self.kwargs = kwargs
        self.gridLayout = self.getKw("grid", False)
        self.make_uniform_column = self.getKw("make_uniform_column", None)
        self.save_row_configure = []
        self.save_column_configure = []
        self.panel = None

    def constructView(self, parent):
        """
        Create the panel view by constructing all subforms views inside a tkinter panel the parent view given.
        Args:
            parent: parent view or parent FormPanel.
        """
        if isinstance(parent, FormPanel):  # Panel is a subpanel
            self.panel = CTkFrame(parent.panel,fg_color=self.getKw("fg_color", None), height=self.getKw("height", 0))
        else:
            self.panel = CTkFrame(parent, fg_color=self.getKw("fg_color", None), height=self.getKw("height", 0))
        self.populateView(parent)

    def populateView(self, parent):
        try:
            if self.make_uniform_column is not None:
                self.makeUniformColumn(self.make_uniform_column)
            
            for form in self.subforms:
                form.constructView(self)
            if isinstance(parent, FormPanel):  # Panel is a subpanel
                if parent.gridLayout:
                    # self.panel.grid_rowconfigure(0, weight=1)
                    # self.panel.grid_columnconfigure(0, weight=1)
                    self.panel.grid(column=self.getKw(
                        "column", 0), row=self.getKw("row", 0), sticky=self.getKw("sticky", tk.NSEW), **self.kwargs)
                else:
                    self.panel.pack(fill=self.getKw("fill", "both"), side=self.getKw(
                        "side", "top"), pady=self.getKw("pady", 5), padx=self.getKw("padx", 10), expand=True, **self.kwargs)
            else:  # Master panel, packing
                is_grid = "row" in self.kwargs or "column" in self.kwargs
                if not is_grid:
                    self.panel.pack(fill=self.getKw("fill", "both"), side="top", pady=self.getKw("pady", 5), padx=self.getKw("padx", 30), expand=True)
                else:
                    self.panel.grid(sticky=self.getKw("sticky", tk.NSEW), row=self.getKw("row", 0), column=self.getKw("column", 0), pady=self.getKw("pady", 5), padx=self.getKw("padx", 30))
            for rowconfigured in self.save_row_configure:
                self.panel.grid_rowconfigure(rowconfigured[0], weight=rowconfigured[1])
            for columnconfigured in self.save_column_configure:
                self.panel.grid_columnconfigure(columnconfigured[0], weight=columnconfigured[1])
        except Exception as e:
            raise Exception("Error while populating view of panel named '" + self.name + "' : " + str(e))

    def checkForm(self):
        """
        Check if this form is correctly filled. A panel is correctly filled if all subforms composing it are correctly filled.

        Returns:
            {
                "correct": True if the form is correctly filled, False otherwise.
                "msg": A message indicating what is not correctly filled.
            }
        """
        for form in self.subforms:
            res, msg = form.checkForm()
            if res == False:
                return False, msg
        return True, ""

    def setFocusOn(self, name):
        """Set focus on the given form name
        Args:
            name: the form name to set the focus on
        """
        for form in self.subforms:
            if name == form.name:
                form.setFocus()

    def makeUniformColumn(self, n):
        for i in range(n):
            self.panel.grid_columnconfigure(i, weight=1, uniform="uniform")

    def rowconfigure(self, row, weight):
        self.save_row_configure.append([row, weight]) 

    def columnconfigure(self, column, weight):
        self.save_column_configure.append([column, weight]) 

    def getValue(self):
        """
        Return the form value. Required for a form.
        Returns:
            returns a list of tuple with subform's name and values.
        """
        res = []
        for form in self.subforms:
            if isinstance(form, FormLabel) or isinstance(form, FormButton) or isinstance(form, FormSeparator):
                continue
            val = form.getValue()
            if val is not None:
                if isinstance(form, FormPanel):
                    res += val
                else:
                    res.append((form.name, val))
        return res

    def setValues(self, dict_of_infos):
        """
        Set the form value recursively. 
        Args:
            dict_of_infos: a dictionnary with key = subform's name and value = subform's value.
        """
        for form in self.subforms:
            if isinstance(form, FormLabel) or isinstance(form, FormButton) or isinstance(form, FormSeparator):
                continue
            if form.name in dict_of_infos:
                form.setValue(dict_of_infos[form.name])
            if isinstance(form, FormPanel):
                form.setValues(dict_of_infos)

    def addFormTreevw(self, name, headers,
                      default_values=None, **kwargs):
        """
        Add a form table to this panel.
        Args:
            name: the table desired name
            headers: a list of 2 strings for the table headers
            default_values: a dictionnary with key = column 0 and value = column 1
            kwargs: Keywords for FormTreevw
        """
        ret = FormTreevw(name, headers, default_values, **kwargs)
        self.subforms.append(ret)
        return ret

    def addFormCombo(self, name, choicesList, default=None, **kwargs):
        """
        Add a form combo to this panel.
        Args:
            name: the combobox desired name
            choicesList: a list of options as strings
            default: a string within the choicesList that will be selected by default. optional.
            kwargs: keywords for FormCombo
        """
        formCombo = FormCombo(name, choicesList, default, **kwargs)
        self.subforms.append(formCombo)
        return formCombo

    def addFormChecklist(self, name, choicesList, default=None, values=None, **kwargs):
        """
        Add a form checklist to this panel.
        Args:
            name: the checklist desired name
            choicesList: a list of options as strings
            default: a list of string within the choicesList that will be selected by default
            kwargs: keywords for FormCheckList
        """
        if default is None:
            default = []
        f = FormChecklist(
            name, choicesList, default, values, **kwargs)
        self.subforms.append(f)
        return f

    def addFormCheckbox(self, name, text, default, **kwargs):
        """
        Add a form checkbox to this panel.

        Args:
            name: the checkbox desired name
            text: a label that will be in front of the checkbox
            default: a boolean indicating if the checkbox should be check by default
            kwargs: keywords for FormCheckbox
        """
        f = FormCheckbox(name, text, default, **kwargs)
        self.subforms.append(f)
        return f
    
    def addFormSwitch(self, name, text, default, **kwargs):
        """
        Add a form switch to this panel.

        Args:
            name: the switch desired name
            text: a label that will be in front of the switch
            default: a boolean indicating if the switch should be check by default
            kwargs: keywords for FormSwitch
        """
        f = FormSwitch(name, text, default, **kwargs)
        self.subforms.append(f)
        return f

    def addFormStr(self, name, regexvalidation="", default="", contextualMenu=None, **kwargs):
        """
        Add a form String to this panel.

        Args:
            name: the string var desired name
            regexvalidation: a regex to validate this input
            default: a default value for this input
            width: the width size of the input
            kwargs: keywords for FormStr
        """
        f = FormStr(name, regexvalidation, default, contextualMenu, **kwargs)
        self.subforms.append(f)
        return f

    def addFormSearchBar(self, name, searchCallback, panel_to_fill, default="", **kwargs):
        """
        Add a form String to this panel.

        Args:
            name: the string var desired name
            searchCallback: a callback
            panel_to_fill: panel to search for subforms with namse matching callback ret
            default: a default value for this input
            kwargs: keywords for FormSearchbar
        """
        f = FormSearchBar(
            name, searchCallback, panel_to_fill, None, default, **kwargs)
        self.subforms.append(f)
        return f

    def addFormFile(self, name, regexvalidation="", default="", **kwargs):
        """
        Add a form String to this panel.

        Args:
            name: the string var desired name
            regexvalidation: a regex validating the form
            default: a default value for this input
            kwargs: keywords for FormFile
        """
        f = FormFile(name, regexvalidation, default, **kwargs)
        self.subforms.append(f)
        return f

    def addFormText(self, name, validation="", default="", contextualMenu=None, **kwargs):
        """
        Add a form Text to this panel.

        Args:
            name: the text var desired name
            validation: a regex to validate this input or a callback function
            default: a default value for this input
            kwargs: keywords for FormText
        """
        f = FormText(name, validation, default, contextualMenu, **kwargs)
        self.subforms.append(f)
        return f
    
    def addFormMarkdown(self, name, validation="", default="", contextualMenu=None, **kwargs):
        """
        Add a form Text to this panel.

        Args:
            name: the text var desired name
            validation: a regex to validate this input or a callback function
            default: a default value for this input
            kwargs: keywords for FormText
        """
        f = FormMarkdown(name, validation, default, contextualMenu, **kwargs)
        self.subforms.append(f)
        return f

    def addFormDate(self, name, root, default="", dateformat='%d/%m/%Y %H:%M:%S', **kwargs):
        """
        Add a form Date to this panel.

        Args:
            name: the text var desired name
            default: a default value for this input
            dateformat: a date format to validate this input. Default to dd/mm/YYYY hh:mm:ss.
            kwargs: keywords for FormDate
        """
        f = FormDate(name, root, default, dateformat, **kwargs)
        self.subforms.append(f)
        return f

    def addFormLabel(self, name, text="", **kwargs):
        """
        Add a form Label to this panel.

        Args:
            name: the label desired name
            text: the text printed by the label
            kwargs: keywords for FormLabel
        """
        f = FormLabel(name, text, **kwargs)
        self.subforms.append(f)
        return f

    def addFormImage(self, path, **kwargs):
        """
        Add a form Label to this panel.

        Args:
            path: the image path
            kwargs: keywords for FormImage (same as tk label)
        """
        f = FormImage(path, **kwargs)
        self.subforms.append(f)
        return f

    def addFormHelper(self, helper, **kwargs):
        """
        Add a form Label to this panel.

        Args:
            helper: the text printed by the helper
            kwargs: keywords for FormHelper
        """
        f = FormHelper("", helper, **kwargs)
        self.subforms.append(f)
        return f

    def addFormButton(self, name, callback, **kwargs):
        """
        Add a form Button to this panel.

        Args:
            name: the button desired name and text
            callback: a function that will be called when the button is pressed.
            kwargs: keywords for FormButton
        """
        f = FormButton(name, callback, **kwargs)
        self.subforms.append(f)
        return f
    

    def addFormSeparator(self,  **kwargs):
        """
        Add a form Button to this panel.

        Args:
            callback: a function that will be called when the button is pressed.
            kwargs: keywords for FormButton
        """
        f = FormSeparator(**kwargs)
        self.subforms.append(f)
        return f

    def addFormHidden(self, name, default=""):
        """
        Add a form Hidden to this panel.

        Args:
            name: the hidden value desired name and text
            default: the value to be hidden
        """
        f = FormHidden(name, default)
        self.subforms.append(f)
        return f

    def addFormPanel(self, **kwargs):
        """
        Add a form Pannel to this panel.

        Args:
            kwargs: can indicate grid=True if a grid layout must be set for subelements.
        Returns:
            Return the new panel to add other forms in.
        """
        pan = FormPanel(**kwargs)
        self.subforms.append(pan)
        return pan
    
    def addFormCollapsiblePanel(self, text, **kwargs):
        """
        Add a form Pannel to this panel.

        Args:
            kwargs: can indicate grid=True if a grid layout must be set for subelements.
        Returns:
            Return the new panel to add other forms in.
        """
        from .formcollapsiblepanel import FormCollapsbilePanel
        pan = FormCollapsbilePanel(text, **kwargs)
        self.subforms.append(pan)
        return pan

    def clear(self):
        """
        Empties the panel's subforms.
        """
        del self.subforms
        self.subforms = []

    def redraw(self):
        """
        Empties the panel's subforms.
        """
        if self.panel is None:
            return
        for w in self.panel.winfo_children():
            w.destroy()
        self.populateView(self.panel)
