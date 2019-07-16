import logging
import os
from marshmallow import ValidationError

from cartography.driftdetect.model import load_state_from_json_file
from cartography.driftdetect.report_info import load_report_info_from_json_file
from cartography.driftdetect.reporter import report_drift

logger = logging.getLogger(__name__)


def run_drift_detection(config):
    try:
        new_results, missing_results = stitch_drift_detection(
            config.query_directory,
            config.start_state,
            config.end_state)
        report_drift(new_results)
        report_drift(missing_results)
    except ValidationError as err:
        msg = "Unable to create DriftState from files {0},{1} for \n{2}".format(
            config.start_state,
            config.end_state,
            err.messages)
        logger.exception(msg)
    except Exception as msg:
        logger.exception(msg)


def stitch_drift_detection(query_directory, start_state_file, end_state_file):
    """
    Performs Drift Detection.

    :type query_directory: String
    :param query_directory: Path to the query directory.
    :type start_state_file: String
    :param start_state_file: The filename of the earlier state chronologically to be compared to.
    :type end_state_file: String
    :param end_state_file: The filename of the later state chronologically to be compared to.
    :return:
    """
    report_info = load_report_info_from_json_file(os.path.join(query_directory, "report_info.json"))
    start_state = load_state_from_json_file(os.path.join(query_directory, report_info.shortcuts.get(
        start_state_file,
        start_state_file)))
    end_state = load_state_from_json_file(os.path.join(query_directory, report_info.shortcuts.get(
        end_state_file,
        end_state_file)))
    if start_state.name != end_state.name or start_state.validation_query != end_state.validation_query:
        raise Exception("Query Information does not match.")
    new_results, missing_results = perform_drift_detection(start_state, end_state)
    return new_results, missing_results


def perform_drift_detection(start_state, end_state):
    """
    Returns differences (additions and missing results) between two DriftStates..

    :type start_state: DriftState
    :param start_state: The earlier state chronologically to be compared to.
    :type end_state: DriftState
    :param end_state: The later state chronologically to be compared to.
    :return: tuple of additions and subtractions between the end and start detector in the form of drift_info_detector
    pairs
    """
    new_results = compare_states(start_state, end_state)
    missing_results = compare_states(end_state, start_state)
    return new_results, missing_results


def compare_states(start_state, end_state):
    """
    Helper function for comparing differences between two DriftStates.

    :type start_state: DriftState
    :param start_state: The earlier state chronologically to be compared to.
    :type end_state: DriftState
    :param end_state: The later state chronologically to be compared to.
    :return: list of tuples of differences between detectors in the form (dictionary, DriftDetector object)
    """
    differences = []
    for result in end_state.results:
        if result in start_state.results:
            continue
        drift_info = {}
        for prop, field in zip(end_state.properties, result):
            value = field.split("|")
            if len(value) > 1:
                drift_info[prop] = value
            else:
                drift_info[prop] = field
        differences.append((drift_info, end_state))
    return differences
