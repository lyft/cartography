import logging
from time import sleep

import multiprocessing_logging

import lib.multiprocessing_dag as multiprocessing_dag
import cartography.config
import cartography.sync
import cartography.intel.create_indexes
from cartography.intel.github import start_github_ingestion
from cartography.intel.aws import start_aws_ingestion
from cartography.intel.gcp import start_gcp_ingestion
from cartography.intel.gsuite import start_gsuite_ingestion



logger = logging.getLogger(__name__)

def mock_sync_1(neo4j_session=None, config=None):
    sleep(5)


def mock_sync_2(neo4j_session=None, config=None):
    sleep(10)


class SyncStage:
    def __init__(self, name, func):
        self.name = name
        self.func = func
        self.logger = logging.getLogger(self.name)

    def run(self, neo4j_driver, config):
        self.logger.info("Starting sync stage '%s' with update tag '%d'", self.name, config.update_tag)
        with neo4j_driver.session() as neo4j_session:
            try:
                # Note to self - this set of params _must_ be followed for all start_* funcs
                self.func(neo4j_session, config)
            except (KeyboardInterrupt, SystemExit):
                self.logger.warning("Sync stage '%s' interrupted", self.name)
                raise
            except Exception:
                self.logger.exception("Unhandled exception during sync stage '%s'", self.name)
                raise
        self.logger.info("Finishing sync stage '%s' with update tag '%d'", self.name, config.update_tag)


class SyncCommand(multiprocessing_dag.BaseCommand):
    def __init__(self, sync, config):
        super().__init__()

        self.sync = sync
        self.config = config

    def run(self):
        cartography.sync.run_with_config(self.sync, self.config)
        return True


def build_cartography_sync_task(config, name, func):
    sync = SyncStage(name, func)
    return multiprocessing_dag.Task(
        name=name,
        commands=[
            SyncCommand(sync, config),
        ],
    )


def build_mainline_sync():
    sync = cartography.sync.Sync()
    # KEEP ORDER
    sync_stages = [
        # TODO - fill these in
    ]
    sync.add_stages(sync_stages)
    return sync


def build_pipeline(config):
    # The pipeline for the overall sync.
    pipeline = multiprocessing_dag.Pipeline(name='sync')

    # Initialization pipeline -- all subsequent pipelines should have this upstream.
    pipeline_start = multiprocessing_dag.Pipeline(name='start')
    task_create_indexes = build_cartography_sync_task(
        config,
        'create-indexes',
        cartography.intel.create_indexes.run,
    )
    pipeline_start.add(task_create_indexes)
    pipeline.add(pipeline_start)

    # Multi pipeline -- eventually everything should be in here
    pipeline_multi = multiprocessing_dag.Pipeline(name='multi')

    task_aws = build_cartography_sync_task(
        config,
        'aws',
        mock_sync_1,
        # start_aws_ingestion,
    )
    pipeline_multi.add(task_aws)

    task_gcp = build_cartography_sync_task(
        config,
        'gcp',
        mock_sync_2,
        # start_gcp_ingestion,
    )
    pipeline_multi.add(task_gcp)

    # task_gsuite = build_cartography_sync_task(
    #     config,
    #     'gsuite',
    #     start_gsuite_ingestion,
    # )
    # pipeline_multi.add(task_gsuite)

    # task_github = build_cartography_sync_task(
    #     config,
    #     'github',
    #     start_github_ingestion,
    # )
    # pipeline_multi.add(task_github)

    pipeline.add(pipeline_multi, upstreams=[pipeline_start])

    # Sequential pipeline
    pipeline_sequential = multiprocessing_dag.Pipeline(name='sequential')

    # pipeline_sequential.add(
    #     multiprocessing_dag.Task(
    #         name='sequential',
    #         commands=[
    #             SyncCommand(
    #                 build_mainline_sync(),
    #                 config
    #             )
    #         ],
    #     )
    # )

    pipeline.add(pipeline_sequential, upstreams=[pipeline_start, pipeline_multi])

    return pipeline


# TODO - replace this with the config data from CLI.py
def build_config():
    config = cartography.config.Config(
        neo4j_uri='bolt://localhost:7687',
        statsd_enabled=True,
        statsd_host='127.0.0.1',
        statsd_port=8125,
        statsd_prefix='',
    )
    return config


def main():
    config = build_config()
    pipeline = build_pipeline(config)
    runner = multiprocessing_dag.Runner()
    return runner.run(pipeline)


if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.DEBUG)
    multiprocessing_logging.install_mp_handler()
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger('neo4j.bolt').setLevel(logging.WARNING)

    try:
        main()
    except Exception:
        logger.exception("Unhandled exception in multisync")
        sys.exit(1)
