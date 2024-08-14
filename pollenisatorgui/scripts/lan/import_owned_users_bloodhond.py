# -*- coding: utf-8 -*-
from pollenisatorgui.core.components.apiclient import APIClient
from bson import ObjectId
from neo4j import GraphDatabase
from pollenisatorgui.scripts.lan.utils import ask_text

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
    bloodhound_uri = ask_text(appli is not None, "Bloodhound uri:", "bolt://localhost:7687")
    if bloodhound_uri == "" or bloodhound_uri is None:
        return False, "No URI given"
    bloodhound_username = ask_text(appli is not None, "neo4j username:", "neo4j")
    if bloodhound_username is None or bloodhound_username == "":
        return False, "No username given"
    bloodhound_password = ask_text(appli is not None, "neo4j password:", "exegol4thewin", secret=True)
    if bloodhound_password is None or bloodhound_password == "":
        return False, "No password given"
    mark_as_owned(bloodhound_uri, users, bloodhound_username, bloodhound_password)
    return True, f"Marked {len(users)} users as owned in bloodhound"
