#
# Assumption drift detection based on baseline and intel service graph data
#
# Author: Sacha Faust (sfaust@lyft.com)
#
import os
import os.path
from driftdetect.driftdetector import DriftDetector
from neo4j.v1 import GraphDatabase


def perform_baseline_drift_detection(session, expect_folder):
    """
    Perform baseline drift detection based on the detectors defined in the expect_folder
    :type neo4j Session
    :param driver: Intel graph db driver
    :param expect_folder: Folder where the detectors are defined
    :return: None
    """

    detector_list = _get_detectors(expect_folder)
    drift_info_detector_pairs = []
    for detector in detector_list:
        for drift_info in detector.run(session):
            drift_info_detector_pairs.append((drift_info, detector))

    return drift_info_detector_pairs


def _get_detectors(expect_folder):
    """
    Get detectors from the folder
    :type string
    :param expect_folder: folder where the detectors re defined
    :return: List od DriftDetector
    """

    detectors = []
    for root, _, filenames in os.walk(expect_folder):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            detectors.append(DriftDetector.from_json_file(file_path).data)

    return detectors


if __name__ == '__main__':
    graph_driver = GraphDatabase.driver("bolt://localhost:7687")
    with graph_driver.session() as session:
        perform_baseline_drift_detection(
            session=session,
            expect_folder="driftdetect/detectors"
        )
