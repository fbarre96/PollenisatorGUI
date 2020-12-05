"""A registry for all subclasses of Plugin"""
REGISTRY = {}

def register_class(target_class):
    """Register the given class
    Args:
        target_class: type <class>
    """
    REGISTRY[target_class.__name__] = target_class()


class MetaPlugin(type):
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        if name not in REGISTRY:
            register_class(cls)
        return cls


class Plugin(metaclass=MetaPlugin):
    """ Parent base plugin to be inherited
    Attributes:
        autoDetect: indicating to auto-detect that this plugin is able to auto detect.
    """

    def getActions(self, _toolmodel):
        """
        Summary: Add buttons to the tool view.
        Args:
            * toolmodel : the tool model opened in the pollenisator client.
        Return:
            A dictionary with buttons text as key and function callback as value.
        """
        return {}
