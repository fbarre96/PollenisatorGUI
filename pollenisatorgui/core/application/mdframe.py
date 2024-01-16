import tkintermd.constants as constants
#import tkintermd.log as log
from customtkinter import *
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, simpledialog
from tkinter import messagebox as mbox
from tkinter.constants import *
import tkinter.ttk as ttk
from tkinterweb import HtmlFrame, Notebook
from tkinterweb.utilities import ScrolledTextBox
from markdown import Markdown
from pygments import lex
from pygments.lexers.markup import MarkdownLexer
from pygments.formatters.html import HtmlFormatter
from pygments.token import Generic
from pygments.lexer import bygroups
from pygments.styles import get_style_by_name, get_all_styles
from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
from pollenisatorgui.core.components import utils

class TkintermdFrame(CTkFrame):
    """A Markdown editor with HTML preview for use in tkinter projects. 
    
    The editor has syntax highlighting supplied by `Pygments` and the HTML 
    preview window is provided by `tkinterweb`.
    
    Import it into your own scripts like so:
    
    ```python
    from tkintermd.frame import TkintermdFrame

    import tkinter as tk
    from tkinter.constants import *

    root = tk.Tk()
    app = TkintermdFrame(root)
    app.pack(fill="both", expand=1)
    app.mainloop()
    ```
    
    """
    def __init__(self, master, **kwargs):
        super().__init__(master,  height=kwargs.get("height", 400))
        #self.logger = log.create_logger()
        self.just_editor = kwargs.get("just_editor", False)
        self.style_change = kwargs.get("style_change", False)
        self.enable_preview = kwargs.get("enable_preview", True)
        self.enable_maximize = kwargs.get("enable_maximize", True)
        self.default = kwargs.get("default_text", "")
        self.binds = kwargs.get("binds", {})
        self.font_size = kwargs.get("font_size", 12)
        # Toolbar.
        if not self.just_editor or self.style_change:
            self.root_toolbar = CTkFrame(self)
            self.open_btn = ttk.Button(self.root_toolbar, text="Open", command=self.open_md_file, tooltip="Open Markdown file")
            self.open_btn.pack(side="left", padx=0, pady=0)
            self.save_as_btn = ttk.Button(self.root_toolbar, text="Save As", command=self.save_as_md_file, tooltip="Save Markdown file as...")
            self.save_as_btn.pack(side="left", padx=0, pady=0)
            self.save_btn = ttk.Button(self.root_toolbar, text="Save", command=self.save_md_file, tooltip="Save Markdown file")
            self.save_btn.pack(side="left", padx=0, pady=0)
            self.export_as_btn = ttk.Button(self.root_toolbar, text="Export HTML", command=self.save_as_html_file, tooltip="Export HTML file as...")
            self.export_as_btn.pack(side="left", padx=0, pady=0)
            # Button to choose pygments style for editor, preview and HTML.
            if self.style_change:
                self.style_opt_btn = tk.Menubutton(self.root_toolbar, text="Editor Style", relief="raised")
                self.style_opt_btn.pack(side="left", padx=0, pady=0)
            self.root_toolbar.pack(side="top", fill="x")

        # Creating the widgets
        self.editor_pw = tk.PanedWindow(self, orient="horizontal", height=kwargs.get("height", 400))
        # Root editor frame
        self.editor_root_frame = tk.Frame(self.editor_pw)
        # Toolbar buttons
        self.editor_toolbar = tk.Frame(self.editor_root_frame)
        self.icons = utils.loadIcons(["maximize.png", "undo_small.png","redo_small.png", "cut_small.png", "copy_small.png", "paste_small.png", "find_small.png","bold_small.png", "italic_small.png", "strikethrough_small.png","image_small.png"])
        if self.enable_maximize:
            self.maximize_btn = ttk.Button(self.editor_toolbar, text="Maximize", image=self.icons["maximize.png"], command=self.maximize, style="icon.TButton", tooltip="Maximize editor")
            self.maximize_btn.pack(side="left", padx=0, pady=0)
        self.undo_btn = ttk.Button(self.editor_toolbar, text="", image=self.icons["undo_small.png"], command=lambda: self.text_area.event_generate("<<Undo>>"), style="icon.TButton", tooltip="Undo last action (Ctrl+z)")
        self.undo_btn.pack(side="left", padx=0, pady=0)
        self.redo_btn = ttk.Button(self.editor_toolbar, text="Redo", image=self.icons["redo_small.png"], command=lambda: self.text_area.event_generate("<<Redo>>"), style="icon.TButton", tooltip="Redo last undo (Ctrl+Shift+z)")
        self.redo_btn.pack(side="left", padx=0, pady=0)
        self.cut_btn = ttk.Button(self.editor_toolbar, text="Cut", image=self.icons["cut_small.png"], command=lambda: self.text_area.event_generate("<<Cut>>"), style="icon.TButton", tooltip="Cut selected text (ctrl+x)")
        self.cut_btn.pack(side="left", padx=0, pady=0)
        self.copy_btn = ttk.Button(self.editor_toolbar, text="Copy", image=self.icons["copy_small.png"], command=lambda: self.text_area.event_generate("<<Copy>>"), style="icon.TButton", tooltip="Copy selected text (ctrl+c)")
        self.copy_btn.pack(side="left", padx=0, pady=0)
        self.paste_btn = ttk.Button(self.editor_toolbar, text="Paste", image=self.icons["paste_small.png"], command=lambda: self.text_area.event_generate("<<Paste>>"), style="icon.TButton", tooltip="Paste selected text (ctrl+v)")
        self.paste_btn.pack(side="left", padx=0, pady=0)
        self.find_btn = ttk.Button(self.editor_toolbar, text="Find", image=self.icons["find_small.png"], command=self.find, style="icon.TButton", tooltip='Find text (ctrl+f)')
        self.find_btn.pack(side="left", padx=0, pady=0)
        self.bold_btn = ttk.Button(self.editor_toolbar, text="", image=self.icons["bold_small.png"], width=16,  command=lambda: self.check_markdown_both_sides(constants.bold_md_syntax, constants.bold_md_ignore, constants.bold_md_special), style="icon.TButton", tooltip='Bold selected text (ctrl+b)')
        self.bold_btn.pack(side="left", padx=0, pady=0)
        self.italic_btn = ttk.Button(self.editor_toolbar, text="", image=self.icons["italic_small.png"], command=lambda: self.check_markdown_both_sides(constants.italic_md_syntax, constants.italic_md_ignore, constants.italic_md_special), style="icon.TButton", tooltip='Italicize selected text (ctrl+i)')
        self.italic_btn.pack(side="left", padx=0, pady=0)
        self.strikethrough_btn = ttk.Button(self.editor_toolbar, text="", image=self.icons["strikethrough_small.png"], command=lambda: self.check_markdown_both_sides(constants.strikethrough_md_syntax, constants.strikethrough_md_ignore, md_special=None, strikethrough=True), style="icon.TButton", tooltip='Strikethrough selected text (ctrl+t)')
        self.strikethrough_btn.pack(side="left", padx=0, pady=0)
        # self.heading_btn = ttk.Button(self.editor_toolbar, text="Heading")
        # self.heading_btn.pack(side="left", padx=0, pady=0)
        # self.unordered_list_btn = ttk.Button(self.editor_toolbar, text="Unordered List")
        # self.unordered_list_btn.pack(side="left", padx=0, pady=0)
        # self.ordered_list_btn = ttk.Button(self.editor_toolbar, text="Ordered List")
        # self.ordered_list_btn.pack(side="left", padx=0, pady=0)
        # self.checklist_btn = ttk.Button(self.editor_toolbar, text="Checklist")
        # self.checklist_btn.pack(side="left", padx=0, pady=0)
        # self.blockquote_btn = ttk.Button(self.editor_toolbar, text="Blockquote")
        # self.blockquote_btn.pack(side="left", padx=0, pady=0)
        #self.codeblock_btn = ttk.Button(self.editor_toolbar, text="Codeblock", command=lambda: self.check_markdown_both_sides(("`","``","```"), constants.bold_md_ignore), style="icon.TButton")
        #self.codeblock_btn.pack(side="left", padx=0, pady=0)
        # self.table_btn = ttk.Button(self.editor_toolbar, text="Table")
        # self.table_btn.pack(side="left", padx=0, pady=0)
        # self.link_btn = ttk.Button(self.editor_toolbar, text="Link")
        # self.link_btn.pack(side="left", padx=0, pady=0)
        self.image_btn =  ttk.Button(self.editor_toolbar, text="", image=self.icons["image_small.png"], command=lambda: self.add_image(), style="icon.TButton", tooltip='Add image (you can also drag&drop inside the editor)')
        self.image_btn.pack(side="left", padx=0, pady=0)
        self.font_size_label = ttk.Label(self.editor_toolbar, text="Font size:")
        self.font_size_label.pack(side="left", padx=0, pady=0)
        self.font_size_combo = ttk.Combobox(self.editor_toolbar, values=list(range(6,64,2)), width=3)
        self.font_size_combo.set(self.font_size)
        self.font_size_combo.pack(side="left", padx=0, pady=0)
        self.font_size_combo.bind("<<ComboboxSelected>>", self.on_font_size_change)
        self.editor_toolbar.pack(side="top", fill="x")
        # Editor frame with scrollbar and text area.
        
        self.editor_frame = ScrolledTextBox(self.editor_root_frame, undo=True, wrap=tk.WORD, font=("Times New Roman", self.font_size))
        self.text_area = self.editor_frame.tbox
        self.text_area.register_drop_target("*")
        if self.binds.get("<<Drop:File>>", None) is not None:
            self.text_area.bind('<<Drop:File>>', self.binds.get("<<Drop:File>>"))
        else:
            self.text_area.bind('<<Drop:File>>', self.dropFile)

        self.editor_frame.pack(fill="both", expand=1)
        # Tabs for the preview and export options.
        if self.enable_preview:
            self.preview_tabs = Notebook(self.editor_pw)
            # HTML rendered preview.
            self.preview_document = HtmlFrame(self.preview_tabs, messages_enabled=False)
        # Root frame for export options.
        self.export_options_root_frame = tk.Frame(self.preview_tabs)
        # Export options frame.
        self.export_options_frame = tk.Frame(self.export_options_root_frame)
        # self.export_options_placeholder = tk.Label(self.export_options_frame, text="Placeholder", justify="center")
        # self.export_options_placeholder.pack(fill="both", expand=1)
        self.export_options_row_a = tk.Frame(self.export_options_frame)
        self.template_label = tk.Label(self.export_options_row_a, text="Choose template:\t")
        self.template_label.pack(side="left")
        self.template_Combobox_value = tk.StringVar()
        self.template_Combobox = ttk.Combobox(self.export_options_row_a, textvariable=self.template_Combobox_value, values=constants.template_list)
        self.template_Combobox.current(0)
        self.template_Combobox.pack(side="left")
        self.export_options_edit_btn = ttk.Button(self.export_options_row_a, text="Edit Before Export", command=self.enable_edit)
        self.export_options_edit_btn.pack(side="left", padx=0, pady=0)
        self.export_options_export_btn = ttk.Button(self.export_options_row_a, text="Export HTML", command=self.save_as_html_file)
        self.export_options_export_btn.pack(side="left", padx=0, pady=0)
        self.export_options_row_a.pack(fill="both")
        self.export_options_frame.pack(fill="both")
        # HTML code preview/edit before export with scrollbar and text area.
        self.export_options_text_area_frame = ScrolledTextBox(self.export_options_root_frame)
        self.export_options_text_area = self.export_options_text_area_frame.tbox
        self.export_options_text_area.configure(state="disabled")
        self.export_options_text_area_frame.pack(fill="both", expand=1)
        # Add the rendered preview and export options to the Notebook tabs.
        self.preview_tabs.add(self.preview_document, text="Preview Document")
        self.preview_tabs.add(self.export_options_root_frame, text="Export Options")
        # Add the editor and preview/export areas to the paned window.
        self.editor_pw.add(self.editor_root_frame)
        self.editor_pw.add(self.preview_tabs)
        self.editor_pw.pack(side="top", fill="both", expand=1)
        self.css = ""
        if self.style_change:
            # Load the self.style_opt_btn menu, this needs to be after the editor.
            self.style_menu = tk.Menu(self.style_opt_btn, tearoff=False)
            for style_name in get_all_styles():
                # dynamcially get names of styles exported by pygments
                try:
                    # test them for compatability
                    self.load_style(style_name)
                    
                except Exception as E:
                    #self.logger.exception(f"WARNING: style {style_name} failed ({E}), removing from style menu.")
                    continue # don't add them to the menu
                # add the rest to the menu
                self.style_menu.add_command(
                    label=style_name,
                    command=(lambda sn:lambda: self.load_style(sn))(style_name)
                    # unfortunately lambdas inside loops need to be stacked 2 deep to get closure variables instead of cell variables
                    )
            self.style_opt_btn["menu"] = self.style_menu

        # Set Pygments syntax highlighting style.
        self.lexer = Lexer()
        self.syntax_highlighting_tags = self.load_style("stata-dark")
        # self.syntax_highlighting_tags = self.load_style("material")
        # Default markdown string.
        default_text = self.default
        default_text = default_text.replace("\t", "    ")
        default_text = default_text.replace("\r", "")
        self.text_area.insert(0.0, default_text)
        self.template_top = constants.default_template_top
        self.template_middle = constants.default_template_middle
        self.template_bottom = constants.default_template_bottom
        # Applies markdown formatting to default file.
        self.check_markdown_highlighting(start="1.0", end=END)
        self.text_area.focus_set()

        # Create right click menu layout for the editor.
        self.right_click = tk.Menu(self.text_area, tearoff=False)
        self.right_click.add_command(label="Copy", command=lambda: self.focus_get().event_generate("<<Copy>>"), accelerator="Ctrl+C")
        self.right_click.add_command(label="Cut", command=lambda: self.focus_get().event_generate("<<Cut>>"), accelerator="Ctrl+X")
        self.right_click.add_command(label="Paste", command=lambda: self.focus_get().event_generate("<<Paste>>"), accelerator="Ctrl+V")
        self.right_click.add_separator()
        self.right_click.add_command(label="Undo", command=lambda: self.focus_get().event_generate("<<Undo>>"), accelerator="Ctrl+Z")
        self.right_click.add_command(label="Redo", command=lambda: self.focus_get().event_generate("<<Redo>>"), accelerator="Ctrl+Y")
        self.right_click.add_separator()
        self.right_click.add_command(label="Find", command=self.find, accelerator="Ctrl+F")
        self.right_click.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")

        # Bind mouse/key events to functions.
        self.template_Combobox.bind("<<ttk.ComboboxSelected>>", self.change_template)
        self.text_area.bind("<<Modified>>", self.on_input_change)
        self.text_area.edit_modified(0)#resets the text widget to generate another event when another change occours
        
        self.text_area.bind_all("<Control-f>", self.find)
        self.text_area.bind_all("<Control-a>", self.select_all)
        self.text_area.bind("<Button-3>", self.popup)

        # # This links the scrollbars but is currently causing issues. 
        # Changing the settings to make the scrolling work
        # self.preview_document.html['yscrollcommand'] = self.on_mousewheel

    def on_font_size_change(self, event=None):
        """Changes the font size of the text area.
        
        - Queries and changes the font size of the text area.
        """
        font_size = int(self.font_size_combo.get())
        self.font_size = font_size
        self.load_style(self.stylename)
        scale_factor = font_size/12.0
        self.preview_document.set_fontscale(scale_factor)

    def dropFile(self, event):
        # This function is called, when stuff is dropped into a widget
        local_paths = utils.drop_file_event_parser(event)
        for local_path in local_paths:
            self.text_area.insert(tk.INSERT, f"![{local_path}]({local_path})")

    def popup(self, event):
        """Right-click popup at mouse location within the text area only.
        
        Provides the following options:
        
        - Cut.
        - Copy.
        - Paste.
        - Undo.
        - Redo.
        - Find.
        - Select All.
        """
        self.right_click.tk_popup(event.x_root, event.y_root)

    # def on_scrollbar(self, *args):
    #     """Scrolls the text area scrollbar when clicked/dragged with a mouse.
        
    #     - Queries and changes the vertical position of the text area view.
    #     """
    #     self.text_area.yview(*args)
    #     # # This links the scrollbars but is currently causing issues.
    #     # self.preview_document.html.yview(*args)

    # def on_mousewheel(self, *args):
    #     """Moves the scrollbar and scrolls the text area on mousewheel event.
        
    #     - Sets the fractional values of the slider position (upper and lower 
    #         ends as value between 0 and 1).
    #     - Calls `on_scrollbar` function.
    #     """
    #     self.scrollbar.set(*args)
    #     # # This links the scrollbars but is currently causing issues.
    #     # self.preview_document.vsb.set(*args)
    #     self.on_scrollbar('moveto', args[0])

    def select_all(self, *args):
        """Select all text within the editor window.
        
        - Add tag TAGNAME to all characters between INDEX1 and INDEX2.
        - Set mark MARKNAME before the character at index.
        - Scroll so that the character at INDEX is visible.
        """
        self.text_area.tag_add(SEL, "1.0", END)
        self.text_area.mark_set(0.0, END)
        self.text_area.see(INSERT)

    def maximize(self, *args, **kwargs):
        """Maximize the editor window.
        
        - Maximizes the editor window.
        """
        dialog = ChildDialogAskText(self, "Markdown Editor", self.text_area.get("1.0", END), multiline=True, markdown=True, fullscreen=True, save_on_close=True)
        self.wait_window(dialog.app)
        text = dialog.rvalue
        if text is not None:
            self.text_area.delete("1.0", END)
            self.text_area.insert("1.0", text)

    def find(self, *args):
        """Simple search dialog for within the editor window.
        
        - Get the current text area content.
        - Displays a simple dialog with a field to enter a search string into 
            and two buttons.
        - If a string is provided then search for it within the text area.
        - Add tag TAGNAME to all characters between INDEX1 and INDEX2.
        - Highlight any found strings within the text editor.
        """
        self.text_area.tag_remove('found', '1.0', END)
        target = simpledialog.askstring('Find', 'Search String:')

        if target:
            idx = '1.0'
            while 1:
                idx = self.text_area.search(target, idx, nocase=1, stopindex=END)
                if not idx: break
                lastidx = '%s+%dc' % (idx, len(target))
                self.text_area.tag_add('found', idx, lastidx)
                idx = lastidx
            self.text_area.tag_config('found', foreground='white', background='blue')

    def open_md_file(self):
        """Open a file and clear/insert the text into the text_area.
        
        Opens a native OS dialog and expects markdown formatted files. Shows an 
        error message if it fails.

        - Display a native OS dialog and request a filename to open.
        - If a filename is provided then `try` to open it in "read" mode.
        - Replace the text area content.
        - Set the `constants.cur_file` value to the filename that was opened.
        - If any of the above fails then display an error message.
        """
        open_filename_md = filedialog.askopenfilename(filetypes=(("Markdown File", "*.md , *.mdown , *.markdown"), ("Text File", "*.txt"), ("All Files", "*.*")))
        if open_filename_md:
            try:
                with open(open_filename_md, "r") as stream:
                    open_filename_contents = stream.read()
                self.text_area.delete(1.0, END)
                self.text_area.insert(END, open_filename_contents)
                self.check_markdown_highlighting(start="1.0", end=END)
                constants.cur_file = Path(open_filename_md)
            except:
                mbox.showerror(title="Error", message=f"Error Opening Selected File\n\nThe file you selected: {open_filename_md} can not be opened!")
    
    def save_as_md_file(self):
        """Saves the file with the given filename.
        
        Opens a native OS dialog for saving the file with a name and markdown 
        extension. Shows an error message if it fails.

        - Display a native OS dialog and request a filename to save.
        - If a filename is provided then `try` to open it in "write" mode.
        - Set the `constants.cur_file` value to the filename that was opened.
        - If any of the above fails then display an error message.
        """
        self.file_data = self.text_area.get("1.0" , END)
        self.save_filename_md = filedialog.asksaveasfilename(filetypes = (("Markdown File", "*.md"), ("Text File", "*.txt")) , title="Save Markdown File")
        if self.save_filename_md:
            try:
                with open(self.save_filename_md, "w") as stream:
                    stream.write(self.file_data)
                    constants.cur_file = Path(self.save_filename_md)
            except:
                mbox.showerror(title="Error", message=f"Error Saving File\n\nThe file: {self.save_filename_md} can not be saved!")

    def save_md_file(self):
        """Quick saves the file with its current name.

        - Get the current text area content.
        - `try` to save the file with the `constants.cur_file` variable.
        - If it fails because no name exists it calls the "save_as_md_file" 
            function.
        """
        self.file_data = self.text_area.get("1.0" , END)
        try:
            with open(constants.cur_file, "w") as stream:
                stream.write(self.file_data)
        except:
            self.save_as_md_file()

    def save_as_html_file(self):
        """Exports the current contents of the HTML preview pane to the given filename.
        
        Opens a native OS dialog for saving the file with a html
        extension. Shows an error message if it fails.

        - Display a native OS dialog and request a filename to save.
        - If a filename is provided then `try` to open it in "write" mode.
        - If any of the above fails then display an error message.
        """
        html_file_data = self.export_options_text_area.get("1.0" , END)
        self.html_save_filename = filedialog.asksaveasfilename(filetypes = (("HTML file", ("*.html", "*.htm")),) , title="Save HTML File")
        if self.html_save_filename:
            try:
                with open(self.html_save_filename, "w") as stream:
                    stream.write(html_file_data)
                    #constants.cur_file = Path(self.html_save_filename)
            except:
                mbox.showerror(title="Error", message=f"Error Saving File\n\nThe file: {self.html_save_filename} can not be saved!")

    def on_input_change(self, event):
        return self.do_on_input_change(event)    
    def do_on_input_change(self, event):
        """Converts the text area input into html output for the HTML preview.
        
        When the user types:
        
        - Get the current text area contents.
        - Convert the markdown formatted string to HTML.
        - Merge the converted markdown with the currently selected template.
        - Load the merged HTML into the document preview.
        - Update the HTML content/states within the export options edit area.
        - Check the markdown and apply formatting to the text area.
        - Reset the modified flag.
        """
        md2html = Markdown(extensions=constants.extensions, extension_configs=constants.extension_configs)
        markdownText = self.text_area.get("1.0", END)
        html = md2html.convert(markdownText)
        final = f"{self.template_top}\n{self.css}\n{self.template_middle}\n{html}\n{self.template_bottom}"
        self.export_options_text_area.configure(state="normal")
        self.export_options_text_area.delete("1.0" , END)
        self.export_options_text_area.insert(END, final)
        self.export_options_text_area.configure(state="disabled")
        self.export_options_edit_btn.configure(state="normal")
        try:
            self.preview_document.load_html(final)
        except RuntimeError as e:
            pass #BUG, understand why main thread is not in main loop
        # self.preview_document.add_css(self.css)
        self.check_markdown_highlighting(start="1.0", end=END)
        self.text_area.edit_modified(0) # resets the text widget to generate another event when another change occours

    def load_style(self, stylename):
        self.stylename = stylename
        return self.do_load_style(stylename)

    def do_load_style(self, stylename):
        """Load Pygments style for syntax highlighting within the editor.
        
        - Load and configure the text area and `tags` with the Pygments styles 
            and custom `Lexer` tags.
        - Create the CSS styling to be merged with the HTML template
        - Generate a `<<Modified>>` event to update the styles when a new style 
            is chosen.
        """
        self.style = get_style_by_name(stylename)
        self.syntax_highlighting_tags = []
        for token, opts in self.style.list_styles():
            kwargs = {}
            fg = opts['color']
            bg = opts['bgcolor']
            if fg:
                kwargs['foreground'] = '#' + fg
            if bg:
                kwargs['background'] = '#' + bg
            font = ('Monospace', self.font_size) + tuple(key for key in ('bold', 'italic') if opts[key])
            kwargs['font'] = font
            kwargs['underline'] = opts['underline']
            self.text_area.tag_configure(str(token), **kwargs)
            self.export_options_text_area.tag_configure(str(token), **kwargs)
            self.syntax_highlighting_tags.append(str(token))
        # print(self.style.background_color or 'white', self.text_area.tag_cget("Token.Text", "foreground") or 'black', stylename)
        self.text_area.configure(bg=self.style.background_color or 'white',
                        fg=self.text_area.tag_cget("Token.Text", "foreground") or 'black',
                        selectbackground=self.style.highlight_color,
                        insertbackground=self.text_area.tag_cget("Token.Text", "foreground") or 'black',
                        )
        self.text_area.tag_configure(str(Generic.StrongEmph), font=('Monospace', self.font_size, 'bold', 'italic'))
        self.export_options_text_area.configure(bg=self.style.background_color or 'white',
                        fg=self.export_options_text_area.tag_cget("Token.Text", "foreground") or 'black',
                        selectbackground=self.style.highlight_color,
                        insertbackground=self.text_area.tag_cget("Token.Text", "foreground") or 'black',
                        )
        # self.export_options_text_area.tag_configure(str(Generic.StrongEmph), font=('Monospace', self.font_size, 'bold', 'italic'))
        self.syntax_highlighting_tags.append(str(Generic.StrongEmph))
        self.formatter = HtmlFormatter()
        self.pygments = self.formatter.get_style_defs(".highlight")
        # Previous version.
        self.css = 'body {background-color: %s; color: %s }\nbody .highlight{ background-color: %s; }\n%s' % (
            self.style.background_color,
            self.text_area.tag_cget("Token.Text", "foreground"),
            self.style.background_color,
            self.pygments
            )#used string%interpolation here because f'string' interpolation is too annoying with embeded { and }
        # self.preview_document.add_css(self.css)
        self.text_area.event_generate("<<Modified>>")
        from pollenisatorgui.core.components.settings import Settings
        settings = Settings()
        editor_key_style = "editor_dark_style" if settings.is_dark_mode() else "editor_light_style"
        settings.local_settings[editor_key_style] = stylename
        settings.saveLocalSettings()
        return self.syntax_highlighting_tags    

    def check_markdown_highlighting(self, start='insert linestart', end='insert lineend'):
        self.do_check_markdown_highlighting(start, end)

    def do_check_markdown_highlighting(self, start='insert linestart', end='insert lineend'):
        """Formats editor content using the Pygments style."""
        self.data = self.text_area.get(start, end)
        while self.data and self.data[0] == '\n':
            start = self.text_area.index('%s+1c' % start)
            self.data = self.data[1:]
        self.text_area.mark_set('range_start', start)
        # clear tags
        for t in self.syntax_highlighting_tags:
            self.text_area.tag_remove(t, start, "range_start +%ic" % len(self.data))
        # parse text
        for token, content in lex(self.data, self.lexer):
            self.text_area.mark_set("range_end", "range_start + %ic" % len(content))
            for t in token.split():
                self.text_area.tag_add(str(t), "range_start", "range_end")
            self.text_area.mark_set("range_start", "range_end")

    def apply_markdown_both_sides(self, selection, md_syntax):
        """Apply markdown to both sides of a selection.

        Args:
            selection (str): Text selection from the editor.
            md_syntax (tuple): Tuple of markdown strings to apply.
        """
        self.md_syntax = md_syntax
        self.cur_selection = selection
        self.insert_md = f"{self.md_syntax[0]}{self.cur_selection}{self.md_syntax[0]}"
        self.text_area.delete(index1=SEL_FIRST, index2=SEL_LAST)
        self.text_area.insert(INSERT, self.insert_md)
        return

    def remove_markdown_both_sides(self, selection, md_syntax):
        """Remove markdown from both sides of a selection.

        Args:
            selection (str): Text selection from the editor.
            md_syntax (tuple): Tuple of markdown strings to remove.
        """
        self.md_syntax = md_syntax
        self.cur_selection = selection
        self.remove_md = str(self.cur_selection).strip(self.md_syntax[0]).strip(self.md_syntax[1])
        self.text_area.delete(index1=SEL_FIRST, index2=SEL_LAST)
        self.text_area.insert(INSERT, self.remove_md)
        return

    def add_image(self):
        """add image to the editor."""
        image_path = filedialog.askopenfilename(title = "Select file",filetypes = (("jpeg files","*.jpg"),("png files","*.png"),("all files","*.*")))
        if image_path:
            self.text_area.insert(INSERT, f"![{os.path.basename(image_path)}]({image_path})")
        return

    def check_markdown_both_sides(self, md_syntax, md_ignore, md_special, strikethrough=None):
        """Check markdown formatting to be applied to both sides of a selection. 

        This will ignore items in the md_ignore variable and then deal with 
        special syntax individually before applying or removing the markdown 
        formatting.
        
        - If string starts with anything in md_ignore do nothing and return from
        the function.
        - If strikethrough is set to `True` then apply or remove the markdown.
        - If the formatting requires special items which can't go in md_ignore
        because they cause issues with markdown being applied incorrectly do 
        nothing and return from the function.
        - Apply or remove the markdown once we reach the end.

        Args:
            selection (str): Text selection from the editor.
            md_syntax (tuple): Tuple of markdown strings to remove.
            md_ignore (tuple): Tuple of markdown strings to ignore.
            md_special (tuple): Tuple of special markdown strings to ignore that 
                cause unexpected issues when included in md_ignore.
            strikethrough (bool): Set to True for strikethrough. Default is 
                `None`.
        """
        self.md_syntax = md_syntax
        self.md_ignore = md_ignore
        self.md_special = md_special
        self.cur_selection = self.text_area.selection_get()
        if str(self.cur_selection).startswith(self.md_ignore) or str(self.cur_selection).endswith(self.md_ignore):
            return
        elif strikethrough == True:
            if str(self.cur_selection).startswith(self.md_syntax) and str(self.cur_selection).endswith(self.md_syntax):
                self.remove_markdown_both_sides(self.cur_selection, self.md_syntax)
                return
            else:
                self.apply_markdown_both_sides(self.cur_selection, self.md_syntax)
                return
        elif str(self.cur_selection).startswith(self.md_special) and str(self.cur_selection).endswith(self.md_special) and not str(self.cur_selection).startswith(self.md_syntax) and not str(self.cur_selection).startswith(self.md_syntax):
            return 
        elif str(self.cur_selection).startswith(self.md_syntax) and str(self.cur_selection).endswith(self.md_syntax):
            self.remove_markdown_both_sides(self.cur_selection, self.md_syntax)
        else:
            self.apply_markdown_both_sides(self.cur_selection, self.md_syntax)

    def change_template(self, template_name):
        """Change the currently selected template.
        
        Get the selected template name from the `StringVar` for the `ttk.Combobox` 
        and compare it with the templates dictionary. If the name matches the 
        key then set the relevant template values and update all the previews.
        """
        template_name = self.template_Combobox_value.get()
        for key, val in constants.template_dict.items():
            if template_name == key:
                self.template_top = val[0]
                self.template_middle = val[1]
                self.template_bottom = val[2]
        self.text_area.event_generate("<<Modified>>")
    
    def enable_edit(self):
        """Enable editing of HTML before export.
        
        Displays a warning to the user and enables HTML editing prior to export.
        """
        mbox.showwarning(title="Warning", message=constants.edit_warning)
        self.export_options_text_area.configure(state="normal")
        self.export_options_edit_btn.configure(state="disabled")

class Lexer(MarkdownLexer):
    """Extend MarkdownLexer to add markup for bold-italic. 
    
    This needs extending further before being complete.
    """
    tokens = {key: val.copy() for key, val in MarkdownLexer.tokens.items()}
    # # bold-italic fenced by '***'
    tokens['inline'].insert(2, (r'(\*\*\*[^* \n][^*\n]*\*\*\*)',
                                bygroups(Generic.StrongEmph)))
    # # bold-italic fenced by '___'
    tokens['inline'].insert(2, (r'(\_\_\_[^_ \n][^_\n]*\_\_\_)',
                                bygroups(Generic.StrongEmph)))
