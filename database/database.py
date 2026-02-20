from neo4j import GraphDatabase, RoutingControl


URI = "neo4j+s://3e875d51.databases.neo4j.io"

AUTH = ("neo4j", "VG9N4Wr9Et0laG1yUkZe4JzWshilhB9-1sn3gaYL-Tc")

def get_driver():
    return GraphDatabase.driver(URI, auth = AUTH)