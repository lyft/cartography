import argparse
import getpass
import logging
import os
import sys
from marshmallow import ValidationError

from cartography.driftdetect.detect_drift import perform_drift_detection
from cartography.driftdetect.update_drift import run_update
from cartography.driftdetect.reporter import report_drift


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
        subparsers = parser.add_subparsers(
            dest='command',
            help='To update current drift files, use the command `cartography-detectdrift update --neo4j_uri <your '
                 'neo4j_uri> --drift-detection-directory <your drift detection directory>` \n'
                 'To get drift between two drift files, use the command `cartography-detectdrift get-drift'
                 '--start-state <path to beginning drift state> --end-state <path to final drift state>'
        )
        parser_update = subparsers.add_parser(
            name='update',
            help='updates each drift detector with the current status of the neo4j database'
        )
        parser_update.add_argument(
            '--neo4j-uri',
            type=str,
            default='bolt://localhost:7687',
            help=(
                'A valid Neo4j URI to sync against. See '
                'https://neo4j.com/docs/api/python-driver/current/driver.html#uri for complete documentation on the '
                'structure of a Neo4j URI.'
            ),
        )
        parser_update.add_argument(
            '--neo4j-user',
            type=str,
            default=None,
            help='A username with which to authenticate to Neo4j.'
        )
        parser_update.add_argument(
            '--neo4j-password-env-var',
            type=str,
            default=None,
            help='The name of an environment variable containing a password with which to authenticate to Neo4j.',
        )
        parser_update.add_argument(
            '--neo4j-password-prompt',
            action='store_true',
            help=(
                'Present an interactive prompt for a password with which to authenticate to Neo4j. This parameter '
                'supersedes other methods of supplying a Neo4j password.'
            ),
        )
        parser_update.add_argument(
            '--drift-detection-directory',
            type=str,
            default=None,
            help=(
                'A path to a directory containing drift-states to build. Drift-detection will discover all JSON'
                'files in the given directory (and its subdirectories) and construct detectors from'
                'them. Drift-detection does not guarantee the order in which the detector jobs are executed.'
            ),
        )
        parser_get_drift = subparsers.add_parser(
            name='get-drift',
            help=(
                'gets drift between two drift states. Must be between the same detection directory'
            )
        )
        parser_get_drift.add_argument(
            '--start-state',
            type=str,
            default=None,
            help=(
                'A path to a directory containing drift-detectors to build. Drift-detection will discover all JSON'
                'files in the given directory (and its subdirectories) and construct detectors from'
                'them. Drift-detection does not guarantee the order in which the detector jobs are executed.'
            ),
        )
        parser_get_drift.add_argument(
            '--end-state',
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
        if config.command == 'update':
            return configure_update(config)
        else:
            return config

    def main(self, argv):
        config = self.configure(argv)
        if config.command == 'update':
            try:
                run_update(config)
            except KeyboardInterrupt:
                return 130
        elif config.command == 'get-drift':
            try:
                new_results, missing_results = perform_drift_detection(config.start_state, config.end_state)
                report_drift(new_results)
                report_drift(missing_results)
            except ValidationError as err:
                msg = "Unable to create DriftDetector from files {0},{1} for \n{2}".format(
                    config.start_state,
                    config.end_state,
                    err.messages)
                logger.exception(msg)
            except AssertionError:
                msg = "Drift States do not belong to the same Query Directory"
                logger.exception(msg)
            except KeyboardInterrupt:
                return 130
        else:
            msg = "No command detected"
            logger.exception(msg)


def configure_update(config):
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


def main(argv=None):
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('neo4j.bolt').setLevel(logging.WARNING)
    argv = argv if argv is not None else sys.argv[1:]
    return CLI(prog="cartography-detectdrift").main(argv)
