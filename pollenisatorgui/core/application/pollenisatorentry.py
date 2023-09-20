from customtkinter import CTkEntry

class PopoEntry(CTkEntry):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.bind("<Control-a>", self.onSelectAll)

    def onSelectAll(self, _event=None):
        # select text
        self.select_range(0, 'end')
        # move cursor to the end
        self.icursor('end')
        return "break"