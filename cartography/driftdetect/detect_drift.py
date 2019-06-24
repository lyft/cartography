import os
import os.path
import logging
import pathlib
from neo4j.v1 import GraphDatabase
import neobolt.exceptions

from cartography.driftdetect.model import load_detector_from_json_file, write_detector_to_json_file
from marshmallow import ValidationError


logger = logging.getLogger(__name__)


def perform_drift_detection(session, expect_folder, update):
    """
    Perform Drift Detection
    :type session: neo4j_session
    :param session: session with infrastructure information
    :type expect_folder: string
    :param expect_folder: detector directory
    :type update: Decides whether or not to update the graph
    :param update: boolean
    :return: list of tuples of drift dictionaries and detectors
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
                        write_detector_to_json_file(detector, file_path)
                    except ValidationError as err:
                        msg = "Unable to save DriftDetector from file {0}.\n{1}".format(file_path, err.messages)
                        logger.exception(msg)
            except ValidationError as err:
                msg = "Unable to create DriftDetector from file {0}.\n{1}".format(file_path, err.messages)
                logger.exception(msg)
    return drift_info_detector_pairs


def run(config):
    """
    :type config: config object passed from argparse
    :param config: refer to config.py
    :return: list of tuples of drift dictionaries and detectors
    """
    if not valid_directory(config):
        return
    neo4j_auth = None
    if config.neo4j_user or config.neo4j_password:
        neo4j_auth = (config.neo4j_user, config.neo4j_password)
    try:
        neo4j_driver = GraphDatabase.driver(
            config.neo4j_uri,
            auth=neo4j_auth,
        )
    except neobolt.exceptions.ServiceUnavailable as e:
        logger.debug("Error occurred during Neo4j connect.", exc_info=True)
        logger.error(
            (
                "Unable to connect to Neo4j using the provided URI '%s', an error occurred: '%s'. Make sure the "
                "Neo4j server is running and accessible from your network."
            ),
            config.neo4j_uri,
            e
        )
        return
    except neobolt.exceptions.AuthError as e:
        logger.debug("Error occurred during Neo4j auth.", exc_info=True)
        if not neo4j_auth:
            logger.error(
                (
                    "Unable to auth to Neo4j, an error occurred: '%s'. driftdetect attempted to connect to Neo4j "
                    "without any auth. Check your Neo4j server settings to see if auth is required and, if it is, "
                    "provide driftdetect with a valid username and password."
                ),
                e
            )
        else:
            logger.error(
                (
                    "Unable to auth to Neo4j, an error occurred: '%s'. driftdetect attempted to connect to Neo4j "
                    "with a username and password. Check your Neo4j server settings to see if the username and "
                    "password provided to driftdetect are valid credentials."
                ),
                e
            )
        return

    with neo4j_driver.session() as session:
        drift_info_detector_pairs = perform_drift_detection(
            session,
            config.drift_detector_directory,
            config.update
        )
        return drift_info_detector_pairs


def valid_directory(config):
    """
    :type config: config object returned by argparse
    :param config: refer to config.py
    :return: boolean
    """
    drift_detector_directory_path = config.drift_detector_directory
    if not drift_detector_directory_path:
        logger.info("Skipping drift-detection because no job path was provided.")
        return False
    drift_detector_directory = pathlib.Path(drift_detector_directory_path)
    if not drift_detector_directory.exists():
        logger.warning(
            "Skipping drift-detection because the provided job path '%s' does not exist.",
            drift_detector_directory
        )
        return False
    if not drift_detector_directory.is_dir():
        logger.warning(
            "Skipping drift-detection because the provided job path '%s' is not a directory.",
            drift_detector_directory
        )
        return False
    return True
