from neo4j import GraphDatabase, RoutingControl


URI = "neo4j+s://35a8dc7c.databases.neo4j.io"

AUTH = ("neo4j", "D9EQ-E-W_7J-vzXr6oVgWUh3CKWLtVP4Q8YgywAR5WI")

def get_driver():
    return GraphDatabase.driver(URI, auth = AUTH)