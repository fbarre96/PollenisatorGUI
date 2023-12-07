"""Scope Model"""

from pollenisatorgui.core.components.datamanager import DataManager
from pollenisatorgui.core.models.element import Element
from pollenisatorgui.core.models.ip import Ip
from bson.objectid import ObjectId
from pollenisatorgui.core.components.apiclient import APIClient
from pollenisatorgui.core.models.tool import Tool
import pollenisatorgui.core.components.utils as utils
from pollenisatorgui.core.components.settings import Settings


class Scope(Element):
    """
    Represents a Scope object that defines a scope that will be targeted by network or domain tools.

    Attributes:
        coll_name: collection name in pollenisator database
    """

    coll_name = "scopes"

    def __init__(self, valuesFromDb=None):
        """Constructor
        Args:
            valueFromDb: a dict holding values to load into the object. A mongo fetched interval is optimal.
                        possible keys with default values are : _id (None), parent (None), tags([]), infos({}),
                        wave(""), scope(""), notes("")
        """
        if valuesFromDb is None:
            valuesFromDb = {}
        super().__init__(valuesFromDb.get("_id", None), valuesFromDb.get("parent", None), valuesFromDb.get("infos", {}))
        self.initialize(valuesFromDb.get("wave", ""), valuesFromDb.get("scope", ""),
                        valuesFromDb.get("notes", ""), valuesFromDb.get("infos", {}))

    def initialize(self, wave, scope="", notes="", infos=None):
        """Set values of scope
        Args:
            wave: the wave parent of this scope
            scope: a string describing the perimeter of this scope (domain, IP, NetworkIP as IP/Mask)
            notes: notes concerning this IP (opt). Default to ""
            infos: a dictionnary of additional info
        Returns:
            this object
        """
        self.wave = wave
        self.scope = scope
        self.notes = notes
        self.infos = infos if infos is not None else {}
        return self

    def update(self, pipeline_set=None):
        """Update this object in database.
        Args:
            pipeline_set: (Opt.) A dictionnary with custom values. If None (default) use model attributes.
        """
        apiclient = APIClient.getInstance()
        if pipeline_set is None:
            apiclient.update("scopes", ObjectId(self._id), {"notes": self.notes})
        else:
            apiclient.update("scopes", ObjectId(self._id), pipeline_set)

    def delete(self):
        """
        Delete the Scope represented by this model in database.
        Also delete the tools associated with this scope
        Also remove this scope from ips in_scopes attributes
        """
        # deleting tool with scope lvl
        apiclient = APIClient.getInstance()
        apiclient.delete("scopes", ObjectId(self._id))
        # Finally delete the selected element

    def addInDb(self):
        """
        Add this scope in database.

        Returns: a tuple with :
                * bool for success
                * mongo ObjectId : already existing object if duplicate, create object id otherwise 
        """
        base = self.getDbKey()
        # Checking unicity
        apiclient = APIClient.getInstance()
        res_insert, iid = apiclient.insert("scopes", base)
        self._id = iid
        # adding the appropriate tools for this scope.
        return res_insert, iid

    def addDomainInDb(self, checkDomain=True):
        """
        Add this scope domain in database.

        Args:
            checkDomain: boolean. If true (Default), checks that the domain IP is in scope

        Returns: a tuple with :
                * bool for success
                * mongo ObjectId : already existing object if duplicate, create object id otherwise 
        """
        # Checking unicity
        base = self.getDbKey()
        apiclient = APIClient.getInstance()
        # Check if domain's ip fit in one of the Scope of the wave
        if checkDomain:
            if not Scope.checkDomainFit(self.wave, self.scope):
                return -1, None
        # insert the domains in the scopes
        res_insert, iid = apiclient.insert("scopes", base)
        self._id = iid
        # Adding appropriate tools for this scopes
        return 1, iid

    @classmethod
    def checkDomainFit(cls, waveName, domain):
        """
        Check if a found domain belongs to one of the scope of the given wave.

        Args:
            waveName: The wave id (name) you want to search for a validating scope
            domain: The found domain.

        Returns:
            boolean
        """
        # Checking settings for domain check.
        settings = Settings()
        # get the domain ip so we can search for it in ipv4 range scopes.
        domainIp = utils.performLookUp(domain)
        datamanager = DataManager.getInstance()
        scopesOfWave = datamanager.find("scopes", {"wave": waveName})
        for scopeOfWave in scopesOfWave:
            scopeIsANetworkIp = utils.isNetworkIp(scopeOfWave["scope"])
            if scopeIsANetworkIp:
                if settings.db_settings.get("include_domains_with_ip_in_scope", False):
                    if Ip.checkIpScope(scopeOfWave["scope"], domainIp):
                        return True
            else:  # If scope is domain
                # check if we include subdomains
                if settings.db_settings.get("include_all_domains", False):
                    return True
                else:
                    splitted_domain = domain.split(".")
                    # Assuring to check only if there is a domain before the tld (.com, .fr ... )
                    topDomainExists = len(splitted_domain) > 2
                    if topDomainExists:
                        if settings.db_settings.get("include_domains_with_topdomain_in_scope", False):
                            if splitted_domain[1:] == scopeOfWave["scope"].split("."):
                                return True
                    if settings.db_settings.get("include_domains_with_ip_in_scope", False):
                        inRangeDomainIp = utils.performLookUp(
                            scopeOfWave["scope"])
                        if str(inRangeDomainIp) == str(domainIp):
                            return True
        return False

    

    def _getParentId(self):
        """
        Return the mongo ObjectId _id of the first parent of this object. For a scope it is the wave.

        Returns:
            Returns the parent wave's ObjectId _id".
        """
        datamanager = DataManager.getInstance()
        res = datamanager.find("waves", {"wave": self.wave}, False)
        if res is None:
            return None
        return res.getId()

    def __str__(self):
        """
        Get a string representation of a scope.

        Returns:
            Returns the scope string (network ipv4 range or domain).
        """
        return self.scope

    def getData(self):
        """Return scope attributes as a dictionnary matching Mongo stored scopes
        Returns:
            dict with keys wave, scope, notes, _id, tags and infos
        """
        return {"wave": self.wave, "scope": self.scope, "notes": self.notes, "_id": self.getId(), "infos": self.infos}

    def getDbKey(self):
        """Return a dict from model to use as unique composed key.
        Returns:
            A dict (2 keys :"wave", "scope")
        """
        return {"wave": self.wave, "scope": self.scope}

    

    def isDomain(self):
        """Returns True if this scope is not a valid NetworkIP
        Returns:
            bool
        """
        return not utils.isNetworkIp(self.scope)

    @classmethod
    def isSubDomain(cls, parentDomain, subDomainTest):
        """Returns True if this scope is a valid subdomain of the given domain
        Args:
            parentDomain: a domain that could be the parent domain of the second arg
            subDomainTest: a domain to be tested as a subdomain of first arg
        Returns:
            bool
        """
        splitted_domain = subDomainTest.split(".")
        # Assuring to check only if there is a domain before the tld (.com, .fr ... )
        topDomainExists = len(splitted_domain) > 2
        if topDomainExists:
            if ".".join(splitted_domain[1:]) == parentDomain:
                return True
        return False
