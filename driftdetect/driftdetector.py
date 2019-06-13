#
# Assumption drift detection based on baseline and intel service graph data
#
# Author: Sacha Faust (sfaust@lyft.com)
#
import json
from driftdetect.driftdetectortype import DriftDetectorType
from marshmallow import Schema, fields, post_load


def _build_drift_insight(graph_result):
    """
    Build drift insight
    :type BoltStatementResult
    :param graph_result: Graph data returned by the validation_query
    :return: Dictionary representing the addition data we have on the drift
    """

    data = {}
    for k in graph_result.keys():
        data[k] = graph_result[k]

    return data


class DriftDetector(object):
    """
    Class that represent a job to run against the intel graph. This is a series of
    GraphStatement that will run sequentially
    """

    def __init__(self,
                 name,
                 validation_query,
                 expectations,
                 detector_type):

        self.name = name
        self.validation_query = validation_query
        self.expectations = expectations
        self.detector_type = detector_type

    def run(self, session):
        """
        Performs Detection
        :type neo4j Session
        :param session: Intel graph session
        :return: Drift detected as Iterator
        """
        results = session.run(self.validation_query)

        for r in results:
            baseline_tag = r["baseline_tag"]

            if baseline_tag not in self.expectations:
                yield _build_drift_insight(r)

    @classmethod
    def from_json_file(cls, file_path):
        """
        Creates Detector from Json File
        :type string
        :param file_path:
        :return: DriftDetector
        """
        try:
            with open(file_path) as j_file:
                data = json.load(j_file)
                schema = DriftDetectorSchema()
                detector = schema.load(data)
                return detector
        except Exception:
            raise


class DriftDetectorSchema(Schema):
    name = fields.Str()
    validation_query = fields.Str()
    detector_type = fields.Int()
    expectations = fields.List(fields.Str())

    @post_load
    def make_driftdetector(self, data):
        return DriftDetector(data['name'],
                             data['validation_query'],
                             data['expectations'],
                             DriftDetectorType(data['detector_type']))
