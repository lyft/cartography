from flask import Flask, jsonify, request
from flask_executor import Executor
from typing import List
import logging
import os
import sys

import cartography.config
import cartography.sync
import cartography.cli

from cartography.intel.aws.util.common import parse_and_validate_aws_custom_sync_profile

logger = logging.getLogger(__name__)
app = Flask(__name__)
executor = Executor(app)

@app.get('/get_status')
def get_status():
    """
    Rurns status of job: READY if job can be started or RUNNING.
    """
    done_status = executor.futures.done('cartography_job')
    if done_status is None or done_status:
        return jsonify({'status':'READY'})
    return jsonify({'status': 'RUNNING'})

def run_cartography_job(aws_custom_sync_profile: str):
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('googleapiclient').setLevel(logging.WARNING)
    logging.getLogger('neo4j').setLevel(logging.WARNING)

    logger.info("Starting cartography job")

    default_sync = cartography.sync.build_default_sync()
    cliObj = cartography.cli.CLI(default_sync, prog='cartography')
    args: List[str] = ['--neo4j-clear-db']
    if os.environ.get('CARTOGRAPHY_VERBOSE', "False") == "True":
        args.append('-v')
    args.append(
        f'--neo4j-uri={os.environ.get("CARTOGRAPHY_NEO4J_URI", "bolt://localhost:7687")}'
    )
    config = cliObj.parser.parse_args(args)
    config.aws_custom_sync_profile=aws_custom_sync_profile
    cliObj.run_from_config(config)

    logger.info("Finished cartography job")

@app.post('/start_job')
def start_job():
    """
    Starts job if it is not already running.
    Returns state STARTED if job was started by request.
    Returns state RUNNING if job was already running.
    """
    # Validate request input
    request_text = request.get_data(as_text=True)
    try:
        parse_and_validate_aws_custom_sync_profile(request_text)
    except ValueError:
        return jsonify({'status': 'FAILED'})

    # Run job if not already started  
    done_status = executor.futures.done('cartography_job')
    if done_status:
        executor.futures.pop('cartography_job')
    if done_status is None or done_status:
        executor.submit_stored(
            'cartography_job',
            run_cartography_job,
            request_text,
        )
        return jsonify({'status':'STARTED'})
    return jsonify({'status': 'RUNNING'})

def main(argv=None):
    app.run(port=6000, debug=True)
