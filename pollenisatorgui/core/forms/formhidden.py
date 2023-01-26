"""Widget with no display that holds a value"""
from pollenisatorgui.core.forms.form import Form


class FormHidden(Form):
    """
    Form field hidden, to store a value.
    """

    def __init__(self, name, default=""):
        """
        Constructor for a hidden form.

        Args:
            name: the form name.
            default: a default value to store in it.
        """
        super().__init__(name)
        self.default = default
        self.val = default

    def getValue(self):
        """
        Return the form value. Required for a form.

        Returns:
            Return the form value.
        """
        return self.val

    def setValue(self, newval):
        """
        Set the form value. Required for a form.
        Args:
           newval: new value to be setted
        """
        self.val = newval
