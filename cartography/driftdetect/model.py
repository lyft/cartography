import json
import logging
from marshmallow import Schema, fields, post_load
from enum import IntEnum


logger = logging.getLogger(__name__)


class DriftDetectorType(IntEnum):
    EXPOSURE = 1


class DriftDetector(object):
    def __init__(self,
                 name,
                 validation_query,
                 expectations,
                 detector_type):

        self.name = name
        self.validation_query = validation_query
        self.expectations = expectations
        self.detector_type = detector_type

    def run(self, session, update):
        """
        Performs Detection
        :type session: neo4j session
        :param session: Graph session to pull infrastructure information from
        :type update: boolean
        :param update: Decides whether or not to update the graph
        :return: iterable of dictionaries of drift information
        """

        results = session.run(self.validation_query)
        logger.debug("Running validation for {0}".format(self.name))

        for record in results:
            values = []
            for field in record.values():
                if isinstance(field, list):
                    s = "|".join(field)
                    values.append(s)
                else:
                    values.append(field)
            if values not in self.expectations:
                if update:
                    self.expectations.append(values)
                yield _build_drift_insight(record)


class DriftDetectorSchema(Schema):
    name = fields.Str()
    validation_query = fields.Str()
    detector_type = fields.Int()
    expectations = fields.List(fields.List(fields.Str()))

    @post_load
    def make_driftdetector(self, data, **kwargs):
        return DriftDetector(data['name'],
                             data['validation_query'],
                             data['expectations'],
                             DriftDetectorType(data['detector_type']))


def load_detector_from_json_file(file_path):
    """
    Creates Detector from Json File
    :type file_path: string
    :param file_path: path to json file that detector is created from
    :return: DriftDetector
    """
    logger.debug("Creating from json file {0}".format(file_path))
    with open(file_path) as j_file:
        data = json.load(j_file)
    schema = DriftDetectorSchema()
    detector = schema.load(data)
    return detector


def write_detector_to_json_file(detector, file_path):
    """
    Saves detector to json file
    :type detector: DriftDetector
    :param detector: Detector to be saved
    :type file_path: string
    :param file_path: file_path to store detector
    :return: None
    """
    logger.debug("Saving to json file {0}".format(file_path))
    schema = DriftDetectorSchema()
    data = schema.dump(detector)
    with open(file_path, 'w') as j_file:
        json.dump(data, j_file, indent=4)


def _build_drift_insight(graph_result):
    """
    Build drift insight
    :type graph_result: BoltStatementResult
    :param graph_result: Graph data returned by the validation_query
    :return: Dictionary representing the addition data we have on the drift
    """

    data = {}
    for k in graph_result.keys():
        data[k] = graph_result[k]

    return data
