from neo4j import GraphDatabase, RoutingControl


URI = "neo4j://127.0.0.1:7687"

AUTH = ("neo4j", "Taran@2603")

def get_driver():
    return GraphDatabase.driver(URI, auth = AUTH)