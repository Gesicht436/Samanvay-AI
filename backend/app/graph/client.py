"""
Neo4j Graph Database Client & Connection Pool Management.
Provides Bolt driver lifecycle, context-managed sessions, and connection diagnostics.
"""

import logging
from typing import Generator, Optional
from neo4j import GraphDatabase, Driver, Session
from backend.app.config import settings

logger = logging.getLogger(__name__)

_driver: Optional[Driver] = None


def get_neo4j_driver() -> Optional[Driver]:
    """Returns the singleton Neo4j Bolt driver instance."""
    global _driver
    if _driver is None:
        try:
            _driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=5.0
            )
            logger.info(f"[+] Initialized Neo4j Bolt driver for {settings.NEO4J_URI}")
        except Exception as e:
            logger.warning(f"[-] Could not initialize Neo4j driver ({e}). Graph queries will fall back to mock.")
            return None
    return _driver


def close_neo4j_driver() -> None:
    """Closes the Neo4j driver on application shutdown."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
        logger.info("[+] Closed Neo4j driver connection pool.")


def verify_connectivity() -> bool:
    """Tests if the Neo4j instance is reachable."""
    driver = get_neo4j_driver()
    if driver is None:
        return False
    try:
        driver.verify_connectivity()
        return True
    except Exception as e:
        logger.warning(f"[-] Neo4j verify_connectivity failed: {e}")
        return False


def get_neo4j_session() -> Generator[Optional[Session], None, None]:
    """FastAPI dependency yielding an active Neo4j session."""
    driver = get_neo4j_driver()
    if driver is None:
        yield None
        return
    try:
        with driver.session() as session:
            yield session
    except Exception as e:
        logger.warning(f"[-] Error during Neo4j session: {e}")
        yield None
