import argparse
import getpass
import logging
import os
import sys
import pathlib
from neo4j.v1 import GraphDatabase
import neobolt.exceptions

from driftdetect.detect_drift import perform_baseline_drift_detection
from driftdetect.reporter import Reporter


logger = logging.getLogger(__name__)


class CLI(object):
    def __init__(self, prog=None):
        self.prog = prog
        self.parser = self._build_parser()

    def _build_parser(self):
        """
        :rtype: argparse.ArgumentParser
        :return: A drift-detection argument parser. Calling parse_args on the argument parser will return an object
                 which implements the driftdetect.config.Config interface.
        """
        parser = argparse.ArgumentParser(
            prog=self.prog,
            description=(
                "drift-detection takes database queries along with their expected states in the cartography-generated "
                "graph database and reports the deviations."
            ),
            epilog='For more documentation please visit: https://github.com/lyft/cartography',
        )
        parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            help='Enable verbose logging for drift-detection.',
        )
        parser.add_argument(
            '-q',
            '--quiet',
            action='store_true',
            help='Restrict drift-detection logging to warnings and errors only.',
        )
        parser.add_argument(
            '--neo4j-uri',
            type=str,
            default='bolt://localhost:7687',
            help=(
                'A valid Neo4j URI to sync against. See '
                'https://neo4j.com/docs/api/python-driver/current/driver.html#uri for complete documentation on the '
                'structure of a Neo4j URI.'
            ),
        )
        parser.add_argument(
            '--neo4j-user',
            type=str,
            default=None,
            help='A username with which to authenticate to Neo4j.'
        )
        parser.add_argument(
            '--neo4j-password-env-var',
            type=str,
            default=None,
            help='The name of an environment variable containing a password with which to authenticate to Neo4j.',
        )
        parser.add_argument(
            '--neo4j-password-prompt',
            action='store_true',
            help=(
                'Present an interactive prompt for a password with which to authenticate to Neo4j. This parameter '
                'supersedes other methods of supplying a Neo4j password.'
            ),
        )
        parser.add_argument(
            '--drift-detector-directory',
            type=str,
            default=None,
            help=(
                'A path to a directory containing drift-detectors to build. Drift-detection will discover all JSON'
                'files in the given directory (and its subdirectories) and construct detectors from'
                'them. Drift-detection does not guarantee the order in which the detector jobs are executed.'
            ),
        )
        return parser

    def configure(self, argv):
        """
        Entrypoint for the command line interface.

        :type argv: string
        :param argv: The parameters supplied to the command line program.
        """
        # TODO support parameter lookup in environment variables if not present on command line
        config = self.parser.parse_args(argv)
        if config.verbose:
            logging.getLogger('driftdetect').setLevel(logging.DEBUG)
        elif config.quiet:
            logging.getLogger('driftdetect').setLevel(logging.WARNING)
        else:
            logging.getLogger('driftdetect').setLevel(logging.INFO)
        logger.debug("Launching driftdetect with CLI configuration: %r", vars(config))
        if config.neo4j_user:
            config.neo4j_password = None
            if config.neo4j_password_prompt:
                logger.info("Reading password for Neo4j user '%s' interactively.", config.neo4j_user)
                config.neo4j_password = getpass.getpass()
            elif config.neo4j_password_env_var:
                logger.debug(
                    "Reading password for Neo4j user '%s' from environment variable '%s'.",
                    config.neo4j_user,
                    config.neo4j_password_env_var
                )
                config.neo4j_password = os.environ.get(config.neo4j_password_env_var)
            if not config.neo4j_password:
                logger.warning("Neo4j username was provided but a password could not be found.")
        else:
            config.neo4j_password = None
        return config

    def main(self, argv):
        config = self.configure(argv)
        try:
            drift_info_detector_pairs = run(config)
            Reporter.report_drift(drift_info_detector_pairs)
        except KeyboardInterrupt:
            return 130


def run(config):
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
        drift_info_detector_pairs = perform_baseline_drift_detection(session, config.drift_detector_directory)
        return drift_info_detector_pairs


def valid_directory(config):
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


def main(argv=None):
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('neo4j.bolt').setLevel(logging.WARNING)
    argv = argv if argv is not None else sys.argv[1:]
    return CLI(prog="driftdetect").main(argv)
