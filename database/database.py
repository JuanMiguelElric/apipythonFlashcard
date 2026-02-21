from neo4j import GraphDatabase, RoutingControl


URI = "neo4j+s://23aa91ea.databases.neo4j.io"

AUTH = ("neo4j", "z1qS3K-xOtX0NWcB62U8Qhr6W5J-9eE8i4bqICjeUoo")

def get_driver():
    return GraphDatabase.driver(URI, auth = AUTH)