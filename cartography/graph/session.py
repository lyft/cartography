import logging
import neo4j
from neo4j.exceptions import ServiceUnavailable, AuthError, SessionExpired, TransactionError, TransactionNestingError, RoutingServiceUnavailable, WriteServiceUnavailable


logger = logging.getLogger(__name__)


class Session(neo4j.Session):
    def __init__(self, neo4j_driver):
        self.neo4j_session = neo4j_driver.session()

    def run(self, query, parameters=None, **kwparameters):
        try:
            return self.neo4j_session.run(query, parameters, **kwparameters)
        except (ServiceUnavailable, AuthError, SessionExpired, TransactionError, TransactionNestingError, RoutingServiceUnavailable, WriteServiceUnavailable) as e:
            logger.warning(f"Failed run neo4j cypher query. Error - {e}")
        except Exception as e:
            logger.warning(f"Failed run neo4j cypher query. Error - {e}")
        return None

    def write_transaction(self, transaction_function, *args, **kwargs):
        try:
            return self.neo4j_session.write_transaction(transaction_function, *args, **kwargs)
        except (ServiceUnavailable, AuthError, SessionExpired, TransactionError, TransactionNestingError, RoutingServiceUnavailable, WriteServiceUnavailable) as e:
            logger.warning(f"Failed write transaction for neo4j. Error - {e}")
        except Exception as e:
            logger.warning(f"Failed write transaction for neo4j. Error - {e}")
        return None
