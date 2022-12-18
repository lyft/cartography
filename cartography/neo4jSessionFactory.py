import logging

logger = logging.getLogger(__name__)


class Neo4JSessionFactory:
    _setup = False
    _driver = None
    _database = None

    def __init__(self):
        logger.info("Neo4JFactory Init")

    def initialize(self, neo4j_driver, neo4j_database):
        if self._setup:
            logger.warning("Reinitializing the Neo4JSessionFactory. It is not allowed.")
            return

        logger.info("Setting up the Neo4JSessionFactory")

        self._setup = True
        self._driver = neo4j_driver
        self._database = neo4j_database

    def get_new_session(self):
        if not self._setup:
            logger.warning("Neo4JSessionFactory is not setup")
            return ClientError

        session = self._driver.session(database=self._database)
        return session


factory = Neo4JSessionFactory()
