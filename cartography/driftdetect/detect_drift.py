import logging
import os

from cartography.driftdetect.model import load_state_from_json_file
from cartography.driftdetect.report_info import load_report_info_from_json_file

logger = logging.getLogger(__name__)


def perform_drift_detection(drift_detection_directory, start_state_path, end_state_path):
    report_info = load_report_info_from_json_file(os.path.join(drift_detection_directory, "report_info.json"))
    start_state = load_state_from_json_file(report_info.shortcuts.get(start_state_path, start_state_path))
    end_state = load_state_from_json_file(report_info.shortcuts.get(end_state_path, end_state_path))
    assert start_state.name == end_state.name
    assert start_state.validation_query == end_state.validation_query
    new_results, missing_results = compare_states(start_state, end_state)
    return new_results, missing_results


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
