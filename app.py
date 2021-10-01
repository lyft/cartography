import base64
import json
import logging
import os
import cartography.cli
from libraries.pubsublibrary import PubSubLibrary
from utils.logger import get_logger
from utils.context import AppContext


def load_cartography(event, ctx):
    context = AppContext(
        region=os.environ['CLOUDANIX_DEFAULT_REGION'],
        log_level=os.environ['CLOUDANIX_DEFAULT_LOG_LEVEL'],
        app_env=os.environ['CLOUDANIX_APP_ENV'],
    )
    context.logger = get_logger(context.log_level)

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

    process_request(context, params)

    return {
        'statusCode': 200,
        'body': json.dumps({
            "status": 'success'
        })
    }


def process_request(context, args):
    logging.info(f'{args["templateType"]} request received - {args["eventId"]}')
    logging.info(f'workspace - {args["workspace"]}')

    body = {
        "credentials": get_auth_creds(context, args),
        "neo4j": {
            "uri": context.neo4j_uri,
            "user": context.neo4j_user,
            "pwd": context.neo4j_pwd,
            "connection_lifetime": 3600
        },
        "logging": {
            "mode": "verbose",
        },
        "params": {
            "sessionString": args['sessionString'],
            "eventId": args['eventId'],
            "templateType": args['templateType'],
            "workspace": args['workspace'],
            "actions": args['actions'],
            "resultTopic": args['resultTopic']
        }
    }

    resp = cartography.cli.run_gcp(body)

    if 'status' in resp and resp['status'] == 'success':
        logging.info(f'successfully processed cartography: {resp}')

    else:
        logging.info(f'failed to process cartography: {resp["message"]}')

    publish_response(context, body, resp)

    logging.info(f'inventory sync gcp response - {args["eventId"]}: {json.dumps(resp)}')


def publish_response(context, req, resp):
    if context.app_env != 'production':
        try:
            with open('response.json', 'w') as outfile:
                json.dump(resp, outfile, indent=2)

        except Exception as e:
            logging.error(f'Failed to write to file: {e}')

    else:
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

        pubsub_helper = PubSubLibrary(context)

        if 'resultTopic' in req['params']:
            # Result should be pushed to "resultTopic" passed in the request
            status = pubsub_helper.publish(os.environ['CLOUDANIX_PROJECT_ID'], json.dumps(body), req['params']['resultTopic'])

        else:
            status = pubsub_helper.publish(os.environ['CLOUDANIX_PROJECT_ID'], json.dumps(body), os.environ['CARTOGRAPHY_RESULT_TOPIC'])

        logging.info(f'result published to PubSub with status: {status}')


def get_auth_creds(context, args):
    auth_creds = {
        'account_email': args['accountEmail'],
        'token_uri': os.environ['CLOUDANIX_TOKEN_URI'],
    }

    return auth_creds
