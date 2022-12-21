import logging
from typing import Any

import neo4j

logger = logging.getLogger(__name__)


class Neo4JSessionFactory:
    _setup = False
    _driver = None
    _database = None

    def __init__(self):
        logger.info("Neo4JFactory Init")

    def initialize(self, neo4j_driver: neo4j.Driver, neo4j_database: str) -> None:
        if self._setup:
            logger.warning("Reinitializing the Neo4JSessionFactory. It is not allowed.")
            return

        logger.info("Setting up the Neo4JSessionFactory")

        self._setup = True
        self._driver = neo4j_driver
        self._database = neo4j_database

    def get_new_session(self) -> Any:
        if not self._setup or not self._driver:
            logger.warning("Neo4J Factory is not initialized.")
            return

        new_session = self._driver.session(database=self._database)
        return new_session


factory = Neo4JSessionFactory()
