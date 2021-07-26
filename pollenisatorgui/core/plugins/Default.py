from pollenisatorgui.core.plugins.plugin import Plugin

class Default(Plugin):
    """Attributes:
        autoDefect: a boolean indication that this plugin should be used to autodetect file.
    """
    autoDetect = False  # Override default True value

def getActions():
    return ""