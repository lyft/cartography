import argparse
import getpass
import logging
import os
import sys

import cartography.sync
import cartography.util


logger = logging.getLogger(__name__)


class CLI:
    """
    :type sync: cartography.sync.Sync
    :param sync: A sync task for the command line program to execute.
    :type prog: string
    :param prog: The name of the command line program. This will be displayed in usage and help output.
    """

    def __init__(self, sync, prog=None):
        self.prog = prog
        self.sync = sync
        self.parser = self._build_parser()

    def _build_parser(self):
        """
        :rtype: argparse.ArgumentParser
        :return: A cartography argument parser. Calling parse_args on the argument parser will return an object which
            implements the cartography.config.Config interface.
        """
        parser = argparse.ArgumentParser(
            prog=self.prog,
            description=(
                "cartography consolidates infrastructure assets and the relationships between them in an intuitive "
                "graph view. This application can be used to pull configuration data from multiple sources, load it "
                "in to Neo4j, and run arbitrary enrichment and analysis on that data. Please make sure you have Neo4j "
                "running and have configured AWS credentials with the SecurityAudit IAM policy before getting started. "
                "Running cartography with no parameters will execute a simple sync against a Neo4j instance running "
                "locally. It will use your default AWS credentials and will not execute and post-sync analysis jobs. "
                "Please see the per-parameter documentation below for information on how to connect to different Neo4j "
                "instances, use auth when communicating with Neo4j, sync data from multiple AWS accounts, and execute "
                "arbitrary analysis jobs after the conclusion of the sync."
            ),
            epilog='For more documentation please visit: https://github.com/lyft/cartography',
        )
        parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            help='Enable verbose logging for cartography.',
        )
        parser.add_argument(
            '-q',
            '--quiet',
            action='store_true',
            help='Restrict cartography logging to warnings and errors only.',
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
            help='A username with which to authenticate to Neo4j.',
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
        # TODO add the below parameters to a 'sync' subparser
        parser.add_argument(
            '--update-tag',
            type=int,
            default=None,
            help=(
                'A unique tag to apply to all Neo4j nodes and relationships created or updated during the sync run. '
                'This tag is used by cleanup jobs to identify nodes and relationships that are stale and need to be '
                'removed from the graph. By default, cartography will use a UNIX timestamp as the update tag.'
            ),
        )
        parser.add_argument(
            '--aws-sync-all-profiles',
            action='store_true',
            help=(
                'Enable AWS sync for all discovered named profiles. When this parameter is supplied cartography will '
                'discover all configured AWS named profiles (see '
                'https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html) and run the AWS sync '
                'job for each profile not named "default". If this parameter is not supplied, cartography will use the '
                'default AWS credentials available in your environment to run the AWS sync once. When using this '
                'parameter it is suggested that you create an AWS config file containing a named profile for each AWS '
                'account you want to sync and use the AWS_CONFIG_FILE environment variable to point to that config '
                'file (see https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html). cartography '
                'respects the AWS CLI/SDK environment variables and does not override them.'
            ),
        )
        parser.add_argument(
            '--crxcavator-api-base-uri',
            type=str,
            default='https://api.crxcavator.io/v1',
            help=(
                'Base URI for the CRXcavator API. Defaults to public API endpoint.'
            ),
        )
        parser.add_argument(
            '--crxcavator-api-key-env-var',
            type=str,
            default=None,
            help=(
                'The name of an environment variable containing a key with which to auth to the CRXcavator API. '
                'Required if you are using the CRXcavator intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--analysis-job-directory',
            type=str,
            default=None,
            help=(
                'A path to a directory containing analysis jobs to run at the conclusion of the sync. cartography will '
                'discover all JSON files in the given directory (and its subdirectories) and pass them to the GraphJob '
                'API to execute against the graph. This allows you to apply data transformation and augmentation at '
                'the end of a sync run without writing code. cartography does not guarantee the order in which the '
                'jobs are executed.'
            ),
        )
        parser.add_argument(
            '--okta-org-id',
            type=str,
            default=None,
            help=(
                'Okta organizational id to sync. Required if you are using the Okta intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--okta-api-key-env-var',
            type=str,
            default=None,
            help=(
                'The name of an environment variable containing a key with which to auth to the Okta API.'
                'Required if you are using the Okta intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--okta-saml-role-regex',
            type=str,
            default=r"^aws\#\S+\#(?{{role}}[\w\-]+)\#(?{{accountid}}\d+)$",
            help=(
                'The regex used to map Okta groups to AWS roles when using okta as a SAML provider.'
                'The regex is the one entered in Step 5: Enabling Group Based Role Mapping in Okta'
                'https://saml-doc.okta.com/SAML_Docs/How-to-Configure-SAML-2.0-for-Amazon-Web-Service#c-step5'
                'The regex must contain the {{role}} and {{accountid}} tags'
            ),
        )
        parser.add_argument(
            '--github-config-env-var',
            type=str,
            default=None,
            help=(
                'The name of an environment variable containing a Base64 encoded GitHub config object.'
                'Required if you are using the GitHub intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--permission-relationships-file',
            type=str,
            default="cartography/data/permission_relationships.yaml",
            help=(
                'The path to the permission relationships mapping file.'
                'If omitted the default permission relationships will be created'
            ),
        )
        parser.add_argument(
            '--jamf-base-uri',
            type=str,
            default=None,
            help=(
                'Your Jamf base URI, e.g. https://hostname.com/JSSResource.'
                'Required if you are using the Jamf intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--jamf-user',
            type=str,
            default=None,
            help='A username with which to authenticate to Jamf.',
        )
        parser.add_argument(
            '--jamf-password-env-var',
            type=str,
            default=None,
            help='The name of an environment variable containing a password with which to authenticate to Jamf.',
        )
        parser.add_argument(
            '--statsd-enabled',
            action='store_true',
            help=(
                'If set, enables sending metrics using statsd to a server of your choice.'
            ),
        )
        parser.add_argument(
            '--statsd-prefix',
            type=str,
            default='',
            help=(
                'The string to prefix statsd metrics with. Only used if --statsd-enabled is on. Default = empty string.'
            ),
        )
        parser.add_argument(
            '--statsd-host',
            type=str,
            default='127.0.0.1',
            help=(
                'The IP address of your statsd server. Only used if --statsd-enabled is on. Default = 127.0.0.1.'
            ),
        )
        parser.add_argument(
            '--statsd-port',
            type=int,
            default=8125,
            help=(
                'The port of your statsd server. Only used if --statsd-enabled is on. Default = UDP 8125.'
            ),
        )
        return parser

    def main(self, argv):
        """
        Entrypoint for the command line interface.

        :type argv: string
        :param argv: The parameters supplied to the command line program.
        """
        # TODO support parameter lookup in environment variables if not present on command line
        config = self.parser.parse_args(argv)
        # Logging config
        if config.verbose:
            logging.getLogger('cartography').setLevel(logging.DEBUG)
        elif config.quiet:
            logging.getLogger('cartography').setLevel(logging.WARNING)
        else:
            logging.getLogger('cartography').setLevel(logging.INFO)
        logger.debug("Launching cartography with CLI configuration: %r", vars(config))
        # Neo4j config
        if config.neo4j_user:
            config.neo4j_password = None
            if config.neo4j_password_prompt:
                logger.info("Reading password for Neo4j user '%s' interactively.", config.neo4j_user)
                config.neo4j_password = getpass.getpass()
            elif config.neo4j_password_env_var:
                logger.debug(
                    "Reading password for Neo4j user '%s' from environment variable '%s'.",
                    config.neo4j_user,
                    config.neo4j_password_env_var,
                )
                config.neo4j_password = os.environ.get(config.neo4j_password_env_var)
            if not config.neo4j_password:
                logger.warning("Neo4j username was provided but a password could not be found.")
        else:
            config.neo4j_password = None

        # Okta config
        if config.okta_org_id and config.okta_api_key_env_var:
            logger.debug(f"Reading API key for Okta from environment variable {config.okta_api_key_env_var}")
            config.okta_api_key = os.environ.get(config.okta_api_key_env_var)
        else:
            config.okta_api_key = None

        # CRXcavator config
        if config.crxcavator_api_base_uri and config.crxcavator_api_key_env_var:
            logger.debug(f"Reading API key for CRXcavator from env variable {config.crxcavator_api_key_env_var}.")
            config.crxcavator_api_key = os.environ.get(config.crxcavator_api_key_env_var)
        else:
            config.crxcavator_api_key = None

        # GitHub config
        if config.github_config_env_var:
            logger.debug(f"Reading config string for GitHub from environment variable {config.github_config_env_var}")
            config.github_config = os.environ.get(config.github_config_env_var)
        else:
            config.github_config = None

        # Jamf config
        if config.jamf_base_uri:
            if config.jamf_user:
                config.jamf_password = None
                if config.jamf_password_env_var:
                    logger.debug(
                        "Reading password for Jamf user '%s' from environment variable '%s'.",
                        config.jamf_user,
                        config.jamf_password_env_var,
                    )
                    config.jamf_password = os.environ.get(config.jamf_password_env_var)
            if not config.jamf_user:
                logger.warning("A Jamf base URI was provided but a user was not.")
            if not config.jamf_password:
                logger.warning("A Jamf password could not be found.")
        else:
            config.jamf_user = None
            config.jamf_password = None

        if config.statsd_enabled:
            logger.debug(
                f'statsd enabled. Sending metrics to server {config.statsd_host}:{config.statsd_port}. '
                f'Metrics have prefix "{config.statsd_prefix}".',
            )

        # Run cartography
        try:
            return cartography.sync.run_with_config(self.sync, config)
        except KeyboardInterrupt:
            return 130


def main(argv=None):
    """
    Entrypoint for the default cartography command line interface.

    This entrypoint build and executed the default cartography sync. See cartography.sync.build_default_sync.

    :rtype: int
    :return: The return code.
    """
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('googleapiclient').setLevel(logging.WARNING)
    logging.getLogger('neo4j.bolt').setLevel(logging.WARNING)
    argv = argv if argv is not None else sys.argv[1:]
    default_sync = cartography.sync.build_default_sync()
    return CLI(default_sync, prog='cartography').main(argv)
