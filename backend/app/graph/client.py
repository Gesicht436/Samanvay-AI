from neo4j import GraphDatabase

from backend.app.config import get_settings


def create_driver():
    settings = get_settings()
    return GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
