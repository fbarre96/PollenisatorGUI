# -*- coding: utf-8 -*-
from pollenisatorgui.core.components.apiclient import APIClient
from bson import ObjectId
from pollenisatorgui.core.application.dialogs.ChildDialogAskText import ChildDialogAskText
from neo4j import GraphDatabase

def mark_as_owned(uri, users, username, password):
    driver = GraphDatabase.driver(uri, auth=(username, password))
    with driver.session() as session:
        for user in users:
            account = user.get("username", "")
            if account == "":
                continue
            domain = user.get("domain", "")
            if domain == "":
                continue
            the_query = "MATCH (n) WHERE (n.name = \"{}@{}\") SET n.owned = true".format(account.strip().upper(), domain.upper())
            graph = session.run(the_query)
    driver.close()

def main(apiclient, appli, **kwargs):
    APIClient.setInstance(apiclient)
    users = apiclient.find("users", {"type":"user", "password":{"$ne":""}}, True)
    if users is None or not users:
        return False, "No owned users found"
    dialog = ChildDialogAskText(appli, "Bloodhound uri:", "bolt://localhost:7687", False)
    appli.wait_window(dialog.app)
    if dialog.rvalue is None:
        return False, "No URI given"
    bloodhound_uri = dialog.rvalue
    dialog = ChildDialogAskText(appli, "neo4j username:", "neo4j", False)
    appli.wait_window(dialog.app)
    if dialog.rvalue is None:
        return False, "No username given"
    bloodhound_username = dialog.rvalue
    dialog = ChildDialogAskText(appli, "neo4j password:", "neo4j", False, secret=True)
    appli.wait_window(dialog.app)
    if dialog.rvalue is None:
        return False, "No password given"
    bloodhound_password = dialog.rvalue
    mark_as_owned(bloodhound_uri, users, bloodhound_username, bloodhound_password)
    return True, f"Marked {len(users)} users as owned in bloodhound"
