import argparse
import logging
import time
from collections import OrderedDict
from typing import Callable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import neo4j.exceptions
from neo4j import GraphDatabase
from statsd import StatsClient

import cartography.intel.analysis
import cartography.intel.aws
import cartography.intel.azure
import cartography.intel.create_indexes
import cartography.intel.crowdstrike
import cartography.intel.crxcavator.crxcavator
import cartography.intel.cve
import cartography.intel.digitalocean
import cartography.intel.gcp
import cartography.intel.github
import cartography.intel.gsuite
import cartography.intel.kubernetes
import cartography.intel.oci
import cartography.intel.okta
from cartography.config import Config
from cartography.stats import set_stats_client
from cartography.util import STATUS_FAILURE
from cartography.util import STATUS_SUCCESS

logger = logging.getLogger(__name__)


class SessionWrapper:
    """
    A wrapper around neo4j.Session that provides a context manager interface and a few convenience methods.
    """

    _session: Optional[neo4j.Session] = None
    _driver: Optional[neo4j.Driver] = None
    _config: Union[Config, argparse.Namespace]

    def __init__(self, config: Union[Config, argparse.Namespace]):
        self._config = config

    def new_driver(self):
        neo4j_auth = None
        if self._config.neo4j_user or self._config.neo4j_password:
            neo4j_auth = (self._config.neo4j_user, self._config.neo4j_password)
        try:
            return GraphDatabase.driver(
                self._config.neo4j_uri,
                auth=neo4j_auth,
                max_connection_lifetime=self._config.neo4j_max_connection_lifetime,
            )
        except neo4j.exceptions.ServiceUnavailable as e:
            logger.debug("Error occurred during Neo4j connect.", exc_info=True)
            logger.error(
                (
                    "Unable to connect to Neo4j using the provided URI '%s', an error occurred: '%s'."
                    "Make sure the Neo4j server is running and accessible from your network."
                ),
                self._config.neo4j_uri,
                e,
            )
            raise
        except neo4j.exceptions.AuthError as e:
            logger.debug("Error occurred during Neo4j auth.", exc_info=True)
            if not neo4j_auth:
                logger.error(
                    (
                        "Unable to auth to Neo4j, an error occurred: '%s'. cartography attempted to connect to Neo4j "
                        "without any auth. Check your Neo4j server settings to see if auth is required and, if it is, "
                        "provide cartography with a valid username and password."
                    ),
                    e,
                )
            else:
                logger.error(
                    (
                        "Unable to auth to Neo4j, an error occurred: '%s'. "
                        "cartography attempted to connect to Neo4j with a username and password. Check your Neo4j "
                        "server settings to see if the username and password provided to cartography are valid "
                        "credentials."
                    ),
                    e,
                )
            raise

    def get_session(self):
        if self._driver is None:
            self._driver = self.new_driver()
        if self._session is None:
            self._session = self._driver.session(database=self._config.neo4j_database)

        return self._session

    def _wrap(self, func: str, *args, **kwargs):
        for i in range(0, 3):
            try:
                sess = self.get_session()
                return sess.__getattribute__(func)(*args, **kwargs)
            except neo4j.exceptions.SessionExpired:
                logger.debug("Error occurred during Neo4j session run.", exc_info=True)
                self._session = None
                self._driver = None
                continue

    def run(self, *args, **kwargs):
        return self._wrap("run", *args, **kwargs)

    def read_transaction(self, *args, **kwargs):
        return self._wrap("read_transaction", *args, **kwargs)

    def write_transaction(self, *args, **kwargs):
        return self._wrap("write_transaction", *args, **kwargs)

    def begin_transaction(self, *args, **kwargs):
        return self._wrap("begin_transaction", *args, **kwargs)

    def close(self):
        if self._session is not None:
            try:
                self._session.close()
            except Exception:
                logger.exception("Error occurred during Neo4j session close.", exc_info=True)
                raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()


class Sync:
    """
    A cartography sync task.

    The role of the sync task is to ensure the data in the graph database represents reality. It does this by executing
    a sequence of sync "stages" which are responsible for retrieving data from various sources (APIs, files, etc.),
    pushing that data to Neo4j, and removing now-invalid nodes and relationships from the graph. An instance of this
    class can be configured to run any number of stages in a specific order.
    """

    def __init__(self):
        # NOTE we may need meta-stages at some point to allow hooking into pre-sync, sync, and post-sync
        self._stages = OrderedDict()

    def add_stage(self, name: str, func: Callable) -> None:
        """
        Add one stage to the sync task.

        :type name: string
        :param name: The name of the stage.
        :type func: Callable
        :param func: The object to call when the stage is executed.
        """
        self._stages[name] = func

    def add_stages(self, stages: List[Tuple[str, Callable]]) -> None:
        """
        Add multiple stages to the sync task.

        :type stages: List[Tuple[string, Callable]]
        :param stages: A list of stage names and stage callable pairs.
        """
        for name, func in stages:
            self.add_stage(name, func)

    def run(self, sw: SessionWrapper, config: Union[Config, argparse.Namespace]) -> int:
        """
        Execute all stages in the sync task in sequence.

        :type sw: SessionWrapper
        :param sw: A SessionWrapper object to use for Neo4j transactions.
        :type config: cartography.config.Config
        :param config: Configuration for the sync run.
        """

        logger.info("Starting sync with update tag '%d'", config.update_tag)
        for stage_name, stage_func in self._stages.items():
            logger.info("Starting sync stage '%s'", stage_name)
            try:
                stage_func(sw, config)
            except (KeyboardInterrupt, SystemExit):
                logger.warning("Sync interrupted during stage '%s'.", stage_name)
                raise
            except Exception:
                logger.exception("Unhandled exception during sync stage '%s'", stage_name)
                raise  # TODO this should be configurable
            logger.info("Finishing sync stage '%s'", stage_name)
        logger.info("Finishing sync with update tag '%d'", config.update_tag)
        return STATUS_SUCCESS


def run_with_config(sync: Sync, config: Union[Config, argparse.Namespace]) -> int:
    """
    Execute the cartography.sync.Sync.run method with parameters built from the given configuration object.

    This function will create a Neo4j driver object from the given Neo4j configuration options (URI, auth, etc.) and
    will choose a sensible update tag if one is not specified in the given configuration.

    :type sync: cartography.sync.Sync
    :param sync: A sync task to run.
    :type config: cartography.config.Config
    :param config: The configuration to use to run the sync task.
    """
    # Initialize statsd client if enabled
    if config.statsd_enabled:
        set_stats_client(
            StatsClient(
                host=config.statsd_host,
                port=config.statsd_port,
                prefix=config.statsd_prefix,
            ),
        )

    default_update_tag = int(time.time())
    if not config.update_tag:
        config.update_tag = default_update_tag

    sw = SessionWrapper(config)
    try:
        sw.run("RETURN 1")
    except neo4j.exceptions.Neo4jError:
        return STATUS_FAILURE

    return sync.run(sw, config)


def build_default_sync() -> Sync:
    """
    Build the default cartography sync, which runs all intelligence modules shipped with the cartography package.

    :rtype: cartography.sync.Sync
    :return: The default cartography sync object.
    """
    sync = Sync()
    sync.add_stages([
        ('create-indexes', cartography.intel.create_indexes.run),
        ('aws', cartography.intel.aws.start_aws_ingestion),
        ('azure', cartography.intel.azure.start_azure_ingestion),
        ('crowdstrike', cartography.intel.crowdstrike.start_crowdstrike_ingestion),
        ('gcp', cartography.intel.gcp.start_gcp_ingestion),
        ('gsuite', cartography.intel.gsuite.start_gsuite_ingestion),
        ('crxcavator', cartography.intel.crxcavator.start_extension_ingestion),
        ('cve', cartography.intel.cve.start_cve_ingestion),
        ('oci', cartography.intel.oci.start_oci_ingestion),
        ('okta', cartography.intel.okta.start_okta_ingestion),
        ('github', cartography.intel.github.start_github_ingestion),
        ('digitalocean', cartography.intel.digitalocean.start_digitalocean_ingestion),
        ('kubernetes', cartography.intel.kubernetes.start_k8s_ingestion),
        ('analysis', cartography.intel.analysis.run),
    ])
    return sync
