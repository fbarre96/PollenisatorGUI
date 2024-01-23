# coding: utf-8


class ComputerInfos():
    def __init__(self, valuesFromDb=None):
        """
        :param os: The os of this ComputerInfos.
        :type os: str
        :param signing: The signing of this ComputerInfos.
        :type signing: boolean
        :param smbv1: The smbv1 of this ComputerInfos.
        :type smbv1: boolean
        :param is_dc: The is_dc of this ComputerInfos.
        :type is_dc: boolean
        :param secrets: The secrets of this ComputerInfos.
        :type secrets: List[str]
        """
        if valuesFromDb is None:
            valuesFromDb = {}
        self.initialize(valuesFromDb.get("os"), valuesFromDb.get("signing"),valuesFromDb.get("smbv1"), \
             valuesFromDb.get("is_dc"), valuesFromDb.get("secrets"))
        

    def initialize(self, os=None, signing=None, smbv1=None, is_dc=None, secrets=None): 
        self.os = os
        self.signing = signing
        self.smbv1 = smbv1
        self.is_dc = is_dc
        self.secrets = secrets
        return self

    def getData(self):
        return {"os":self.os, "signing": self.signing, "smbv1":self.smbv1, "is_dc":self.is_dc, "secrets":self.secrets}
    
    @property
    def os(self):
        """Gets the os of this ComputerInfos.


        :return: The os of this ComputerInfos.
        :rtype: str
        """
        return self._os

    @os.setter
    def os(self, os):
        """Sets the os of this ComputerInfos.


        :param os: The os of this ComputerInfos.
        :type os: str
        """

        self._os = os

    @property
    def signing(self):
        """Gets the signing of this ComputerInfos.


        :return: The signing of this ComputerInfos.
        :rtype: bool
        """
        return self._signing

    @signing.setter
    def signing(self, signing):
        """Sets the signing of this ComputerInfos.


        :param signing: The signing of this ComputerInfos.
        :type signing: bool
        """

        self._signing = signing

    @property
    def smbv1(self):
        """Gets the smbv1 of this ComputerInfos.


        :return: The smbv1 of this ComputerInfos.
        :rtype: bool
        """
        return self._smbv1

    @smbv1.setter
    def smbv1(self, smbv1):
        """Sets the smbv1 of this ComputerInfos.


        :param smbv1: The smbv1 of this ComputerInfos.
        :type smbv1: bool
        """

        self._smbv1 = smbv1

    @property
    def is_dc(self):
        """Gets the is_dc of this ComputerInfos.


        :return: The is_dc of this ComputerInfos.
        :rtype: bool
        """
        return self._is_dc

    @is_dc.setter
    def is_dc(self, is_dc):
        """Sets the is_dc of this ComputerInfos.


        :param is_dc: The is_dc of this ComputerInfos.
        :type is_dc: bool
        """

        self._is_dc = is_dc

    @property
    def secrets(self):
        """Gets the secrets of this ComputerInfos.


        :return: The secrets of this ComputerInfos.
        :rtype: List[str]
        """
        return self._secrets

    @secrets.setter
    def secrets(self, secrets):
        """Sets the secrets of this ComputerInfos.


        :param secrets: The secrets of this ComputerInfos.
        :type secrets: List[str]
        """

        self._secrets = secrets