import logging

logger = logging.getLogger(__name__)


class State:
    """
    The default object which stores query information.

    :type name: String
    :param name: Name of the query.
    :type validation_query: String
    :param validation_query: Actual Cypher query being run.
    :type properties: List of Strings
    :param properties: List of keys in order that the cypher query will return.
    :type results: List of List of Strings
    :param results: List of all results of running the validation query
    """

    def __init__(
            self,
            name,
            validation_query,
            properties,
            results,
    ):

        self.name = name
        self.validation_query = validation_query
        self.properties = properties
        self.results = results
