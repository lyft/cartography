import neobolt.exceptions
from neo4j import GraphDatabase


class GraphLibrary:
    def __init__(self, context):
        self.context = context
        self.driver = None

        self.connect()

    def close(self):
        self.driver.close()

    def connect(self):
        neo4j_auth = None
        if self.context.neo4j_user or self.context.neo4j_pwd:
            neo4j_auth = (
                self.context.neo4j_user,
                self.context.neo4j_pwd,
            )

        try:
            self.driver = GraphDatabase.driver(
                self.context.neo4j_uri,
                auth=neo4j_auth,
            )

        except neobolt.exceptions.ServiceUnavailable as e:
            self.context.logger.debug(
                "Error occurred during Neo4j connect.", exc_info=True,
            )
            self.context.logger.error(
                (
                    "Unable to connect to Neo4j using the provided URI '%s', an error occurred: '%s'.\
                        Make sure the Neo4j server is running and accessible from your network."
                ),
                self.context.neo4j_uri,
                e,
            )
            return

        except neobolt.exceptions.AuthError as e:
            self.context.logger.debug(
                "Error occurred during Neo4j auth.", exc_info=True,
            )
            if not neo4j_auth:
                self.context.logger.error(
                    (
                        "Unable to auth to Neo4j, an error occurred: '%s'. lambda attempted to connect to Neo4j "
                        "without any auth. Check your Neo4j server settings to see if auth is required and, if it is, "
                        "provide lambda with a valid username and password."
                    ),
                    e,
                )
            else:
                self.context.logger.error(
                    (
                        "Unable to auth to Neo4j, an error occurred: '%s'. lambda attempted to connect to Neo4j with "
                        "a username and password. Check your Neo4j server settings to see if the username and password "
                        "provided to lambda are valid credentials."
                    ),
                    e,
                )
            return

    def execute(self, statement, entity, **kwargs):
        # https://neo4j.com/docs/api/python-driver/1.7/results.html
        # https://community.neo4j.com/t/extracting-subgraph-into-json-format/3416/2
        # https://community.neo4j.com/t/query-neo4j-to-return-json-data-using-the-c-driver/1961/3

        result = None
        records = None
        with self.driver.session() as neo4j_session:
            result = neo4j_session.run(
                statement,
                kwargs,
            )

        if result:
            for records in result.records():
                record = records.data()
                return record[entity]

        return None
