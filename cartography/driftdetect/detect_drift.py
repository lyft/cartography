import os
import os.path
import logging
from cartography.driftdetect.driftstate import load_state_from_json_file, write_state_to_json_file


logger = logging.getLogger(__name__)


def update_detectors(session, expect_folder, filename):
    """
    Walks through all detector directories, runs the query, and saves the detector using the detector template.
    :param session:
    :param expect_folder:
    :param time: filename
    :return:
    """
    for root, directories, _ in os.walk(expect_folder):
        for directory in directories:
            file_path = os.path.join(root, directory, "template.json")
            detector = load_state_from_json_file(file_path)
            detector.update(session)
            write_state_to_json_file(detector, os.path.join(root, directory, filename))


def compare_states(start_state, end_state):
    """
    Compares drift between two detectors
    :param start_state: DriftDetector
    :param end_state: DriftDetector
    :return: tuple of additions and subtractions between the end and start detector in the form of drift_info_detector
    pairs
    """
    new_results = state_differences(start_state, end_state)
    missing_results = state_differences(end_state, start_state)
    return new_results, missing_results


def state_differences(start_state, end_state):
    """
    Compares drift between two detectors
    :param start_state: DriftDetector
    :param end_state: DriftDetector
    :return: list of tuples of differences between detectors in the form (dictionary, DriftDetector object)
    """
    new_results = []
    for result in end_state.expectations:
        if result not in start_state.expectations:
            drift_info = {}
            for i in range(len(end_state.properties)):
                field = result[i].split("|")
                if len(field) > 1:
                    drift_info[end_state.properties[i]] = field
                else:
                    drift_info[end_state.properties[i]] = result[i]
            new_results.append((drift_info, end_state))
    return new_results
