from neo4j import GraphDatabase, RoutingControl


URI = "neo4j+s://983f0e6d.databases.neo4j.io"

AUTH = ("983f0e6d", "4GOEpYzEMxqQF33LMVlWWwwUClR0_tHI3YQ45RLZWAw")

def get_driver():
    return GraphDatabase.driver(URI, auth = AUTH)