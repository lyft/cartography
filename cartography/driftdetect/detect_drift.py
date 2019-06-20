import os
import os.path
import logging
from cartography.driftdetect.driftstate import load_detector_from_json_file, write_state_to_json_file
from marshmallow import ValidationError

logger = logging.getLogger(__name__)


def perform_drift_detection(session, expect_folder, update):
    """
    Perform Drift Detection
    :param session: neo4j_session
    :param expect_folder: detector directory (string)
    :param update: boolean
    :return: list of drift_info (dictionary), DriftDetector tuples
    """
    drift_info_detector_pairs = []
    for root, _, filenames in os.walk(expect_folder):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            try:
                detector = load_detector_from_json_file(file_path)
                for drift_info in detector.run(session, update):
                    drift_info_detector_pairs.append((drift_info, detector))
                if update:
                    try:
                        write_state_to_json_file(detector, file_path)
                    except ValidationError as err:
                        msg = "Unable to save DriftDetector from file {0} for \n{1}".format(file_path, err.messages)
                        logger.error(msg, exc_info=True)
            except ValidationError as err:
                msg = "Unable to create DriftDetector from file {0} for \n{1}".format(file_path, err.messages)
                logger.error(msg, exc_info=True)
    return drift_info_detector_pairs


def update_detectors(session, expect_folder, filename):
    """
    Walks through all detector directories, runs the query, and saves the detector using the detector template.
    :param session:
    :param expect_folder:
    :param time: filename
    :return:
    """
    for root, directories, _ in os.walk(expect_folder):
        for dir in directories:
            file_path = os.path.join(root, dir, "template.json")
            detector = load_detector_from_json_file(file_path)
            detector.update(session)
            write_state_to_json_file(detector, os.path.join(root, dir, ".".join(filename)))


def compare_detectors(start_detector, end_detector):
    """
    Compares drift between two detectors
    :param start_detector: DriftDetector
    :param end_detector: DriftDetector
    :return: tuple of additions and subtractions between the end and start detector in the form of drift_info_detector
    pairs
    """
    new_results = detector_differences(start_detector, end_detector)
    missing_results = detector_differences(end_detector, start_detector)
    return new_results, missing_results


def detector_differences(start_detector, end_detector):
    """
    Compares drift between two detectors
    :param start_detector: DriftDetector
    :param end_detector: DriftDetector
    :return: list of tuples of differences between detectors in the form (dictionary, DriftDetector object)
    """
    new_results = []
    for result in end_detector.expectations:
        if result not in start_detector.expectations:
            drift_info = {}
            for i in range(len(end_detector.properties)):
                field = result[i].split("|")
                if len(field) > 1:
                    drift_info[end_detector.properties[i]] = field
                else:
                    drift_info[end_detector.properties[i]] = result[i]
            new_results.append((drift_info, end_detector))
    return new_results
