from pollenisatorgui.core.Components.apiclient import APIClient

class Module:
    def loadModuleInfo(self):
        apiclient = APIClient.getInstance()
        self.module_info = apiclient.getModuleInfo(self.__class__.collName)