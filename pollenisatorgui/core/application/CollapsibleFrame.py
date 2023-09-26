
from customtkinter import *
from tkinter import ttk
import tkinter as tk
from PIL import Image
import base64
from io import BytesIO


class CollapsibleFrame(CTkFrame):
    def __init__(self, master, text=None, border_width=2, width=0, height=16, interior_padx=0, interior_pady=8, background=None, caption_separation=4, caption_font=None, caption_builder=None, icon_x=5, **kwargs):
        CTkFrame.__init__(self, master, **kwargs)
        
        self._is_opened = False

        self._interior_padx = interior_padx
        self._interior_pady = interior_pady

        self._iconOpen = "R0lGODlhEAAQAKIAAP///9TQyICAgEBAQAAAAAAAAAAAAAAAACwAAAAAEAAQAAADNhi63BMgyinFAy0HC3Xj2EJoIEOM32WeaSeeqFK+say+2azUi+5ttx/QJeQIjshkcsBsOp/MBAA7"
        self._iconClose = "R0lGODlhEAAQAKIAAP///9TQyICAgEBAQAAAAAAAAAAAAAAAACwAAAAAEAAQAAADMxi63BMgyinFAy0HC3XjmLeA4ngpRKoSZoeuDLmo38mwtVvKu93rIo5gSCwWB8ikcolMAAA7"
        self._iconOpen = Image.open(BytesIO(base64.b64decode(self._iconOpen)))
        self._iconClose = Image.open(BytesIO(base64.b64decode(self._iconClose)))
        height_of_icon = max(self._iconOpen.height, self._iconClose.height)
        width_of_icon = max(self._iconOpen.width, self._iconClose.width)
        
        containerFrame_pady = (height_of_icon//2) +1

        self._height = height
        self._width = width

        self._containerFrame = CTkFrame(self, border_width=border_width, width=width, height=height)
        self._containerFrame.pack(expand=True, fill=tk.X, pady=(containerFrame_pady,0))
        
        self.interior = CTkFrame(self._containerFrame)

        self._collapseButton = CTkLabel(self,  text= "", image=CTkImage(self._iconOpen))
        self._collapseButton.place(in_= self._containerFrame, x=icon_x, y=-(height_of_icon//2)-5, anchor=tk.NW, bordermode="ignore")
        self._collapseButton.bind("<Button-1>", lambda _event=None: self.toggle())

        if caption_builder is None:
            self._captionLabel = CTkLabel(self, anchor=tk.W, text=text)
            if caption_font is not None:
                self._captionLabel.configure(font=caption_font)
        else:
            self._captionLabel = caption_builder(self)
            
            if not isinstance(self._captionLabel, ttk.Widget):
                raise Exception("'caption_builder' doesn't return a tkinter widget")

        self.after(0, lambda _event=None: self._place_caption(caption_separation, icon_x, width_of_icon))

    def update_width(self, width=None):
        # Update could be devil
        # http://wiki.tcl.tk/1255
        self.after(0, lambda width=width:self._update_width(width))

    def _place_caption(self, caption_separation, icon_x, width_of_icon):
        try:
            self.update()
            x = caption_separation + icon_x + width_of_icon
            y = -(self._captionLabel.winfo_reqheight()//2)-1
            self._captionLabel.place(in_= self._containerFrame, x=x, y=y, anchor=tk.NW, bordermode="ignore")
        except tk.TclError:
            pass
        
    def _update_width(self, width):
        self.update()
        if width is None:
            width=self.interior.winfo_reqwidth()

        if isinstance(self._interior_pady, (list, tuple)):
            width += self._interior_pady[0] + self._interior_pady[1]
        else:
            width += 2*self._interior_pady
            
        width = max(self._width, width)

        self._containerFrame.configure(width=width)
        
    def open(self):
        self._collapseButton.configure(image=CTkImage(self._iconClose))
        
        self._containerFrame.configure(height=self.interior.winfo_reqheight())
        self.interior.pack(expand=True, fill=tk.X, padx=self._interior_padx, pady =self._interior_pady)

        self._is_opened = True

    def close(self):
        self.interior.pack_forget()
        self._containerFrame.configure(height=self._height)
        self._collapseButton.configure(image=CTkImage(self._iconOpen))
        self._is_opened = False
    
    def toggle(self):
        if self._is_opened:
            self.close()
        else:
            self.open()
