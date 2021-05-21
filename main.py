import base64
import json
import logging
import os
import cartography.cli
from libraries.pubsublibrary import PubSubLibrary


def cartography_worker(event, ctx):
    logging.info('inventory sync gcp worker request received via PubSub')

    if 'data' in event:
        message = base64.b64decode(event['data']).decode('utf-8')

    else:
        logging.info('invalid message format in PubSub')
        return {
            "status": 'failure',
            "message": 'unable to parse PubSub message'
        }

    logging.info(f'message from PubSub: {message}')

    try:
        params = json.loads(message)

    except Exception as e:
        logging.error(f'error while parsing request json: {e}')
        return {
            "status": 'failure',
            "message": 'unable to parse request'
        }

    process_request(params)

    return {
        'statusCode': 200,
        'body': json.dumps({
            "status": 'success'
        })
    }


def process_request(params):
    logging.info(f'{params["templateType"]} request received - {params["eventId"]}')
    logging.info(f'workspace - {params["workspace"]}')

    body = {
        "credentials": {
            'account_email': params['accountEmail'],
            'token_uri': os.environ['CLOUDANIX_TOKEN_URI'],
        },
        "neo4j": {
            "uri": os.environ.get('neo4juri'),
            "user": os.environ.get('neo4juser'),
            "pwd": os.environ.get('neo4jpwd'),
            "connection_lifetime": 3600
        },
        "logging": {
            "mode": "verbose",
        },
        "params": {
            "sessionString": params['sessionString'],
            "eventId": params['eventId'],
            "templateType": params['templateType'],
            "workspace": params['workspace'],
            "actions": params['actions'],
            "resultTopic": params['resultTopic']
        }
    }

    resp = cartography.cli.run_gcp(body)

    if 'status' in resp and resp['status'] == 'success':
        logging.info(f'successfully processed cartography: {resp}')

    else:
        logging.info(f'failed to process cartography: {resp["message"]}')

    publish_response(body, resp)

    logging.info(f'inventory sync gcp response - {params["eventId"]}: {json.dumps(resp)}')


def publish_response(req, resp):
    body = {
        "status": resp['status'],
        "params": req['params'],
        "sessionString": req['params']['sessionString'],
        "eventId": req['params']['eventId'],
        "templateType": req['params']['templateType'],
        "workspace": req['params']['workspace'],
        "actions": req['params']['actions'],
        "response": resp
    }

    pubsub_helper = PubSubLibrary()

    if 'resultTopic' in req['params']:
        # Result should be pushed to "resultTopic" passed in the request
        status = pubsub_helper.publish(os.environ['CLOUDANIX_PROJECT_ID'], json.dumps(body), req['params']['resultTopic'])

    else:
        status = pubsub_helper.publish(os.environ['CLOUDANIX_PROJECT_ID'], json.dumps(body), os.environ['CARTOGRAPHY_RESULT_TOPIC'])

    logging.info(f'result published to PubSub with status: {status}')
