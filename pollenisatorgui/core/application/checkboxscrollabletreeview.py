
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.application.scrollabletreeview import ScrollableTreeview
import tkinter as tk

class CheckboxScrollableTreeview(ScrollableTreeview):
    checked_image = None
    unchecked_image = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bindtags = list(self.treevw.bindtags())
        bindtags.insert(1, self.treevw)
        self.bindtags(tuple(bindtags))
        self.bind("<1>", self.on_sub_click)


    def get_checked_image(self):
        if self.__class__.checked_image is None:
            self.__class__.checked_image = utils.loadIcon("checked.png", resize=(16,16))
        return self.__class__.checked_image

    def get_unchecked_image(self):
        if self.__class__.unchecked_image is None:
            self.__class__.unchecked_image = utils.loadIcon("unchecked.png", resize=(16,16))
        return self.__class__.unchecked_image
    
    def on_sub_click(self, event):
        # Get the clicked coordinates
        x, y = event.x, event.y
        # Identify the item at the clicked coordinates
        item = self.treevw.identify('item', x, y)
        if item is None or item == "":
            return
        column = self.treevw.identify_column(x)
        if column != "#0":
            return
        tags = super().item(item)["tags"]
        tags = [tags] if isinstance(tags, str) else list(tags)
        if 'unchecked' in tags:
            tags.remove('unchecked')
            tags.append('checked')
            image = self.get_checked_image()
        else:
            tags.remove('checked')
            tags.append('unchecked')
            image = self.get_unchecked_image()
        super().item(item, image=image, tags=tags)

    def _check(self, item):
        tags = super().item(item)["tags"]
        tags = [tags] if isinstance(tags, str) else list(tags)
        if 'unchecked' in tags:
            tags.remove('unchecked')
            tags.append('checked')
            image = self.get_checked_image()
            try:
                super().item(item, image=image, tags=tags)
            except tk.TclError:
                pass

    def _uncheck(self, item):
        tags = super().item(item)["tags"]
        tags = [tags] if isinstance(tags, str) else list(tags)
        if 'checked' in tags:
            tags.remove('checked')
            tags.append('unchecked')
            image = self.get_unchecked_image()
            try:
                super().item(item, image=image, tags=tags)
            except tk.TclError:
                pass
    
    def checkAll(self):
        for item in self.get_children(all=True):
            self._check(item)

    def uncheckAll(self):
        for item in self.get_children(all=True):
            self._uncheck(item)        

    def get_checked_children(self):
        return [item for item in self.get_children(all=True) if 'checked' in self.item(item)["tags"]]

    def insert(self, *args, **kwargs):
        kwargs["image"] = self.get_unchecked_image()
        kwargs["tags"] = kwargs.get("tags", []) + ["unchecked"]
        super().insert(*args, **kwargs)