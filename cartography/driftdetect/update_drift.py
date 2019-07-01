import os
import os.path
import pathlib
import time
import logging
from neo4j.v1 import GraphDatabase
import neobolt.exceptions

from cartography.driftdetect.model import load_state_from_json_file, write_state_to_json_file

logger = logging.getLogger(__name__)


def update_queries(session, expect_folder, filename):
    """
    Walks through all detector directories, runs the query, and saves the detector using the detector template.
    :param session:
    :param expect_folder:
    :param filename:
    :return:
    """
    for root, directories, _ in os.walk(expect_folder):
        for directory in directories:
            file_path = os.path.join(root, directory, "template.json")
            state = load_state_from_json_file(file_path)
            state.update(session)
            write_state_to_json_file(state, os.path.join(root, directory, filename))


def run_update(config):
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
        filename = '.'.join([str(i) for i in time.gmtime()] + [".json"])
        update_queries(session, config.drift_detection_directory, filename)


def valid_directory(config):
    drift_detector_directory_path = config.drift_detector_directory
    if not drift_detector_directory_path:
        logger.info("Cannot perform drift-detection because no job path was provided.")
        return False
    drift_detector_directory = pathlib.Path(drift_detector_directory_path)
    if not drift_detector_directory.exists():
        logger.warning(
            "Cannot perform drift-detection because the provided job path '%s' does not exist.",
            drift_detector_directory
        )
        return False
    if not drift_detector_directory.is_dir():
        logger.warning(
            "Cannot perform drift-detection because the provided job path '%s' is not a directory.",
            drift_detector_directory
        )
        return False
    return True
