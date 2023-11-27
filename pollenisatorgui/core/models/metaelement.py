REGISTRY = {}

def register_class(target_class):
    """Register the given class
    Args:
        target_class: type <class>
    """
    REGISTRY[target_class.__name__.lower()] = target_class


class MetaElement(type):
    def __new__(meta, name, bases, class_dict):
        name = name.lower()
        cls = type.__new__(meta, name, bases, class_dict)
        if name not in REGISTRY and name != "element":
            register_class(cls)
        return cls