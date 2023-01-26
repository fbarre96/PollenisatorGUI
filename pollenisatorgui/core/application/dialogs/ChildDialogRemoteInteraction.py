"""Ask the user to select a file or directory and then parse it with the selected parser"""
import tkinter as tk
import tkinter.ttk as ttk
from pollenisatorgui.core.components.apiclient import APIClient
import threading

class ChildDialogRemoteInteraction:
    """
    Open a child dialog of a tkinter application to show a text area.
    """

    def __init__(self, toolController):
        """
        Open a child dialog of a tkinter application to ask details about
        existing files parsing.

        Args:
            default_path: a default path to be added
        """
        self.app = tk.Toplevel(None, bg="white")
        self.app.protocol("WM_DELETE_WINDOW", self.onError)
        self.app.title("Remote interaction with "+str(toolController.getDetailedString()))
        self.toolController = toolController
        self.rvalue = None
        appFrame = ttk.Frame(self.app)
        self.text_area = tk.Text(self.app, font=("Consolas", 14), bg="#000000", fg="#00ff00")
        self.text_area.insert(tk.END, toolController.getDetailedString()+"\n"+str(toolController.getData().get("infos",{}).get("cmdline", ""))+"\n")
        self.text_area.pack(fill="both", expand=True)     
        self.text_area.focus_force()
        btn = ttk.Button(self.app, text="Quit", command=self.onError)
        btn.pack(side="bottom", anchor=tk.E)
        self.app.bind("<Escape>", self.onError)
        appFrame.pack(ipadx=10, ipady=10)
        self.timer = threading.Timer(0.5, self.getProgress)
        self.timer.start()
        try:
            self.app.wait_visibility()
            self.app.focus_force()
            self.app.grab_set()
            self.app.lift()
        except tk.TclError:
            pass
            
    
    def getProgress(self):
        # Print the key that was pressed
        apiclient = APIClient.getInstance()
        result = apiclient.getToolProgress(str(self.toolController.getDbId()))
        try:
            if isinstance(result, str):
                self.text_area.insert(tk.END, result)
            elif isinstance(result, bool) and result:
                self.text_area.insert(tk.END, "Scan ended. You can quit and download result file.")
                return True
            else:
                tk.messagebox.showerror("Could not get progress", result[1])
                return False
        except:
            return False
        self.timer = threading.Timer(2, self.getProgress)
        self.timer.start()
        #self.sio.emit("remoteInteractionGet", {"name":apiclient.getUser(), "db": apiclient.getCurrentPentest(),"id":str(self.toolController.getDbId())})
        return True

    def quit(self):
        #self.sio.disconnect()
        #self.sio.eio.disconnect()
        #self.sio = None
        self.timer.cancel()

    def onError(self, _event=None):
        self.rvalue = None
        self.quit()

        self.app.destroy()

    def onOk(self, _event=None):
        """
        Called when the user clicked the validation button.
        launch parsing with selected parser on selected file/directory.
        Close the window.

        Args:
            _event: not used but mandatory
        """
        self.quit()
        self.app.destroy()
        
