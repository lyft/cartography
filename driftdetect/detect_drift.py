import os
import os.path
import logging
from driftdetect.driftdetector import DriftDetector
from marshmallow import ValidationError


logger = logging.getLogger(__name__)


def perform_baseline_drift_detection(session, expect_folder):
    """
    Perform baseline drift detection based on the detectors defined in the expect_folder
    :type neo4j Session
    :param driver: graph db driver
    :param expect_folder: Folder where the detectors are defined
    :return: None
    """
    detector_list = _get_detectors(expect_folder)
    return get_drift_from_detectors(session, detector_list)


def get_drift_from_detectors(session, detector_list):
    """
    Perform baseline drift detection based on the detectors defined in the expect_folder
    :type neo4j Session
    :param driver: graph db driver
    :param detector_list: list of detectors
    :return: None
    """

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
    :return: List of DriftDetector
    """

    detectors = []
    for root, _, filenames in os.walk(expect_folder):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            try:
                detectors.append(DriftDetector.from_json_file(file_path))
            except ValidationError as err:
                msg = "Unable to create DriftDetector from file {0} for {1}".format(file_path, err.messages)
                logger.error(msg, exc_info=True)

    return detectors
