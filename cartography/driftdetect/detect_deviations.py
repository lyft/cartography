import logging
import os
from marshmallow import ValidationError

from cartography.driftdetect.serializers import StateSchema, ShortcutSchema
from cartography.driftdetect.storage import FileSystem
from cartography.driftdetect.reporter import report_drift

logger = logging.getLogger(__name__)


def run_drift_detection(config):
    try:
        shortcut_data = FileSystem.load(os.path.join(config.query_directory, "shortcut.json"))
        shortcut = ShortcutSchema.load(shortcut_data)
        start_state_data = FileSystem.load(os.path.join(config.query_directory, shortcut.shortcuts.get(
            config.start_state,
            config.start_state)))
        start_state = StateSchema.load(start_state_data)
        end_state_data = FileSystem.load(os.path.join(config.query_directory, shortcut.shortcuts.get(
            config.end_state,
            config.end_state)))
        end_state = StateSchema.load(end_state_data)
        new_results, missing_results = perform_drift_detection(start_state, end_state)
        report_drift(new_results)
        report_drift(missing_results)
    except ValidationError as err:
        msg = "Unable to create DriftStates from files {0},{1} for \n{2}".format(
            config.start_state,
            config.end_state,
            err.messages)
        logger.exception(msg)
    except ValueError as msg:
        logger.exception(msg)


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
    if start_state.name != end_state.name:
        raise ValueError("State names do not match.")
    if start_state.validation_query != end_state.validation_query:
        raise ValueError("State queries do not match.")
    if start_state.properties != end_state.properties:
        raise ValueError("State properties do not match.")
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
