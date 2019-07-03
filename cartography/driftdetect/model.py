import json
import logging
from marshmallow import Schema, fields, post_load

logger = logging.getLogger(__name__)


class DriftState(object):
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
    def __init__(self,
                 name,
                 validation_query,
                 properties,
                 results):

        self.name = name
        self.validation_query = validation_query
        self.properties = properties
        self.results = results

    def run(self, session, update):
        """
        Connects to a neo4j session, runs the validation query, saves the results to the detector, and finally returns
        the new information found.

        :type session: neo4j session
        :param session: Graph session to pull infrastructure information from.
        :type update: boolean
        :param update: Decides whether or not to update the graph.
        :rtype: List of Dictionaries
        :return: iterable of dictionaries of drift information.
        """

        results = session.run(self.validation_query)
        logger.debug("Running validation for {0}".format(self.name))

        for record in results:
            values = []
            for field in record.values():
                if not field:
                    values.append("")
                elif isinstance(field, list):
                    s = "|".join(field)
                    values.append(s)
                else:
                    values.append(field)
            if values not in self.results:
                if update:
                    self.results.append(values)
                yield _build_drift_insight(record)

    def update(self, session):
        """
        Connects to a neo4j session, runs the validation query, then saves the results to the detector.

        :type session: neo4j session
        :param session: Graph session to pull infrastructure information from.
        :return: None
        """

        new_results = session.run(self.validation_query)
        logger.debug("Updating results for {0}".format(self.name))

        results = []

        for record in new_results:
            values = []
            for field in record.values():
                if isinstance(field, list):
                    s = "|".join(field)
                    values.append(s)
                else:
                    values.append(field)
            results.append(values)

        self.results = results


class DriftStateSchema(Schema):
    """
    Schema for saving DriftStates
    """
    name = fields.Str()
    validation_query = fields.Str()
    properties = fields.List(fields.Str())
    results = fields.List(fields.List(fields.Str()))

    @post_load
    def make_driftstate(self, data, **kwargs):
        return DriftState(data['name'],
                          data['validation_query'],
                          data['properties'],
                          data['results'])


def load_state_from_json_file(file_path):
    """
    Creates Detector from Json File
    :type file_path: string
    :param file_path: path to json file that detector is created from
    :return: DriftDetector
    """
    logger.debug("Creating from json file {0}".format(file_path))
    with open(file_path) as j_file:
        data = json.load(j_file)
    schema = DriftStateSchema()
    detector = schema.load(data)
    return detector


def write_state_to_json_file(detector, file_path):
    """
    Saves detector to json file
    :type detector: DriftDetector
    :param detector: Detector to be saved
    :type file_path: string
    :param file_path: file_path to store detector
    :return: None
    """
    logger.debug("Saving to json file {0}".format(file_path))
    schema = DriftStateSchema()
    data = schema.dump(detector)
    with open(file_path, 'w') as j_file:
        json.dump(data, j_file, indent=4)


def _build_drift_insight(graph_result):
    """
    Build drift insight

    :type graph_result: BoltStatementResult
    :param graph_result: Graph data returned by the validation_query

    :rtype: Dictionary
    :return: Dictionary representing the addition data we have on the drift
    """

    data = {}
    for k in graph_result.keys():
        data[k] = graph_result[k]

    return data
