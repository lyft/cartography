import logging
from typing import Any

import neo4j

logger = logging.getLogger(__name__)


class Neo4jSessionFactory:
    _setup = False
    _driver = None
    _database = None

    def __init__(self):
        logger.info("Neo4j neo4j_session_factory init")

    def initialize(self, neo4j_driver: neo4j.Driver, neo4j_database: str) -> None:
        if self._setup:
            logger.warning("Reinitializing the Neo4j session neo4j_session_factory. It is not allowed.")
            return

        logger.info("Setting up the Neo4j Session Factory")

        self._setup = True
        self._driver = neo4j_driver
        self._database = neo4j_database

    def get_new_session(self) -> Any:
        if not self._setup or not self._driver:
            logger.warning("Neo4j Factory is not initialized.")
            return

        new_session = self._driver.session(database=self._database)
        return new_session


neo4j_session_factory = Neo4jSessionFactory()
