from neo4j import GraphDatabase, RoutingControl


URI = "neo4j+s://db3928ca.databases.neo4j.io"

AUTH = ("db3928ca", "DBORn5DJOlpkA8byKEWsh9McgsBJFcfLH8zGCVhoQTo")

def get_driver():
    return GraphDatabase.driver(URI, auth = AUTH)