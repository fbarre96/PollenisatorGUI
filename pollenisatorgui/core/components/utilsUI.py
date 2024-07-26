import tkinter  as tk
import tkinter.ttk as ttk
from customtkinter import *
from PIL import Image, ImageTk
from ttkwidgets import tooltips
import customtkinter
import screeninfo
import pollenisatorgui.core.components.utils as utils
import os
import json


def craftMenuWithStyle(menu_parent):
    """
    Craft a menu with the current style.
    Args:
        menu_parent: the parent menu to craft.

    Returns:
        the crafted menu.
    """
   
    menu = tk.Menu(menu_parent, tearoff=0, background= getStrongColor(), foreground="white", activebackground= getStrongActiveColor(), activeforeground="white")
    return menu

def setStyle(tkApp, dark_mode=False, _event=None):
    """
    Set the tk app style window widget style using ttk.Style
    Args:
        _event: not used but mandatory
    """
    if dark_mode:
        customtkinter.set_appearance_mode("dark")
    else:
        customtkinter.set_appearance_mode("light")

    style = ttk.Style(tkApp)
    style.theme_use("clam")
    
    colors = get_color_scheme(dark_mode)
    main_color = colors.get("main")
    hover_color = colors.get("hover") 
    background_color = colors.get("background")
    text_color = colors.get("text")
    background_bis_color = colors.get("background_bis")
    style.configure("Treeview.Heading", background=main_color,
                foreground="gray97", borderwidth=0)
    style.map('Treeview.Heading', background=[('active', hover_color)])
    style.configure("Treeview", background=background_color, fieldbackground=background_color, foreground=text_color)
    #style.configure("Treeview.Item")

    style.configure("TLabelframe", background=background_color,foreground=background_color,
                    labeloutside=False, bordercolor=main_color,relief=tk.SUNKEN)
    style.configure('TLabelframe.Label', background=main_color,
                    foreground=background_color, font=('Sans', '10', 'bold'))
    style.configure("TProgressbar",
                background=hover_color, foreground=hover_color, troughcolor=background_color, darkcolor=hover_color, lightcolor=hover_color)
    style.configure("Important.TFrame", background=main_color)
    style.configure("TFrame", background=background_color)
    style.configure("Debug.TFrame", background="red")
    style.configure("Important.TLabel", background=main_color, foreground=background_color)
    style.configure("Pagination.TLabel", background=background_color, foreground=main_color, font=('Sans', '10', 'underline') )
    style.configure("CurrentPagination.TLabel", background=background_color, foreground=main_color, font=('Sans', '10', 'bold') )
    style.map("Pagination.TLabel", foreground=[("active", hover_color)])
    style.map("CurrentPagination.TLabel", foreground=[("active", hover_color)] )
    style.configure("TLabel", background=background_color, foreground=text_color)
    style.configure("TCombobox", background=background_color)
    
    style.configure("TCheckbutton", background=background_color)

    style.configure("TButton", background=main_color,
                foreground=text_color, font=('Sans', '10', 'bold'), borderwidth=1)
    style.configure("icon.TButton", background=background_color, borderwidth=0)
    style.configure("iconbis.TButton", background=background_bis_color, borderwidth=0)
    style.configure("icon_white.TButton", background=main_color, borderwidth=0)

    style.configure("link.TButton", background=background_color, foreground=main_color, font=('Sans', '10', 'underline'), borderwidth=0)
    style.map('link.TButton', foreground=[('active', hover_color)], background=[('active', background_color)])
    style.configure("Notebook.TButton", background=main_color,
                foreground=text_color, font=('Sans', '10', 'bold'), borderwidth=0)
    style.configure("Notebook.TFrame", background=main_color)
    style.map('TButton', background=[('active', hover_color)])
    #  FIX tkinter tag_configure not showing colors   https://bugs.python.org/issue36468
    style.map('Treeview', foreground=fixedMap('foreground', style),
                background=fixedMap('background', style))
    tooltips.update_defaults({"background": getBackgroundColor()})

def getBackgroundColor():
    """
    Return the background color of the current style.
    Returns:
        the background color.
    """
    settings = utils.cacheSettings()
    dark_mode = settings.is_dark_mode()
    colors = get_color_scheme(dark_mode)
    return colors.get("background")

def getBackgroundSecondColor():
    settings = utils.cacheSettings()
    dark_mode = settings.is_dark_mode()
    colors = get_color_scheme(dark_mode)
    return colors.get("background_bis")

def getTextColor():
    """
    Return the background color of the current style.
    Returns:
        the background color.
    """
    settings = utils.cacheSettings()
    dark_mode = settings.is_dark_mode()
    colors = get_color_scheme(dark_mode)
    return colors.get("text")

def getStrongColor():
    """
    Return the background color of the current style.
    Returns:
        the background color.
    """
    settings = utils.cacheSettings()
    dark_mode = settings.is_dark_mode()
    colors = get_color_scheme(dark_mode)
    return colors.get("strong")

def getStrongActiveColor():
    """
    Return the background color of the current style.
    Returns:
        the background color.
    """
    settings = utils.cacheSettings()
    dark_mode = settings.is_dark_mode()
    colors = get_color_scheme(dark_mode)
    return colors.get("strong_active")

def get_color_scheme(dark_mode=False):
    main_color = ("#5ac433", "#2FA572")[dark_mode]
    hover_color = ("#48a825", "#2FC572")[dark_mode]
    background_color = ("gray97", "gray17")[dark_mode]
    text_color = ("gray20", "#DCE4EE")[dark_mode]
    second_color = ("gray89", "dim gray")[dark_mode]
    strong_color = ('#3b75a8','#113759')[dark_mode]
    strong_active_color = ('#061b4e','#2768a1')[dark_mode]
    return {"main":main_color, "hover":hover_color, "background":background_color, "text":text_color, "background_bis":second_color,
            "strong":strong_color, "strong_active":strong_active_color}


def fixedMap(option, style):
    """
    Fix color tag in treeview not appearing under some linux distros
    Args:
        option: the string option you want to affect on treeview ("background" for example)
        strle: the style object of ttk
    """
    # Fix for setting text colour for Tkinter 8.6.9
    # From: https://core.tcl.tk/tk/info/509cafafae
    #  FIX tkinter tag_configure not showing colors   https://bugs.python.org/issue36468
    # Returns the style map for 'option' with any styles starting with
    # ('!disabled', '!selected', ...) filtered out.

    # style.map() returns an empty list for missing options, so this
    # should be future-safe.
    return [elm for elm in style.map('Treeview', query_opt=option) if
            elm[:2] != ('!disabled', '!selected')]
                  



def get_screen_where_widget(widget):
    """
    Get the screen size of the current terminal

    Returns:
        Return the screen size as a tuple (width, height)
    """
    monitors = screeninfo.get_monitors()
    monitor = None
    if widget is not None:
        x = widget.winfo_rootx()
        y = widget.winfo_rooty()
        for m in reversed(monitors):
            if m.x <= x <= m.width + m.x and m.y <= y <= m.height + m.y:
                monitor = m
    if monitor is None:
        monitor = monitors[0]
    return monitor



def getValidMarkIconPath():
    """Returns:
         a validation mark icon path
    """
    return getIcon("done_tool.png")


def getBadMarkIconPath():
    """Returns:
         a bad mark icon path
    """
    return getIcon("cross.png")


def getWaitingMarkIconPath():
    """Returns:
         a waiting icon path
    """
    return getIcon("waiting.png")

def getIcon(name):
    """Returns : the path to an specified icon name
    """
    settings = utils.cacheSettings()
    if settings.is_dark_mode():
        return os.path.join(getIconDir(), "dark", os.path.basename(name))
    else:
        return os.path.join(getIconDir(), "light", os.path.basename(name))
        
def getHelpIconPath():
    """Returns:
         a help icon path
    """
    return getIcon("help.png")

def loadIcon(name, **kwargs):
    """Returns:
         a help icon path
    """
    path = getIcon(name)
    image = Image.open(path)
    #img = image.resize((16, 16))
    return ImageTk.PhotoImage(image)

def loadIcons(names):
    load_icons = {}
    for name in names:
        load_icons[name] = loadIcon(name)
    return load_icons

def getIconDir():
    """Returns:
        the icon directory path
    """
    p = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../../theme/")
    return p

def getColorTheme():
    return utils.getMainDir()+"theme/pollenisator_theme.json"

def loadTheme():
    with open(getColorTheme(), "r") as f:
        return json.load(f)