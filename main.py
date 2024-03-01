# Unused file
# Used by GCP Functions
import base64
import json
import logging
import os

import requests
from requests import Response
from requests.exceptions import RequestException

import cartography.cli
import utils.logger as lgr
from libraries.pubsublibrary import PubSubLibrary
from utils.errors import PubSubPublishError

# Used by GCP Functions


def cartography_worker(event, ctx):
    logging.getLogger('cartography').setLevel(os.environ.get('LOG_LEVEL'))
    # logging.getLogger('cartography.intel').setLevel(os.environ.get('LOG_LEVEL'))
    logging.getLogger('cartography.sync').setLevel(os.environ.get('LOG_LEVEL'))
    logging.getLogger('cartography.graph').setLevel(os.environ.get('LOG_LEVEL'))
    logging.getLogger('cartography.cartography').setLevel(os.environ.get('LOG_LEVEL'))

    logger = lgr.get_logger("DEBUG")
    logger.info('inventory sync gcp worker request received via PubSub')

    if 'data' in event:
        message = base64.b64decode(event['data']).decode('utf-8')

    else:
        logger.info('invalid message format in PubSub')
        return {
            "status": 'failure',
            "message": 'unable to parse PubSub message',
        }

    logger.info(f'message from PubSub: {message}')

    try:
        params = json.loads(message)

    except Exception as e:
        logger.error(f'error while parsing request json: {e}')
        return {
            "status": 'failure',
            "message": 'unable to parse request',
        }
    if params.get("templateType") == "GCPINVENTORYVIEWS":
        gcp_process_request(logger, params)
    elif params.get("templateType") == "GITHUBINVENTORYVIEWS":
        github_process_request(logger, params)
    elif params.get("templateType") == "BITBUCKETINVENTORYVIEWS":
        bitbucket_process_request(logger, params)

    return {
        'statusCode': 200,
        'body': json.dumps({
            "status": 'success',
        }),
    }


def gcp_process_request(logger, params):
    logger.info(f'request - {params.get("templateType")} - {params.get("eventId")} - {params.get("workspace")}')

    svcs = []
    for svc in params.get('services', []):
        page = svc.get('pagination', {}).get('pageSize')
        if page:
            svc['pagination']['pageSize'] = 10000

        svcs.append(svc)

    body = {
        "credentials": {
            'account_email': params['accountEmail'],
            'token_uri': os.environ['CDX_TOKEN_URI'],
        },
        "neo4j": {
            "uri": os.environ.get('neo4juri'),
            "user": os.environ.get('neo4juser'),
            "pwd": os.environ.get('neo4jpwd'),
            "connection_lifetime": 200,
        },
        "logging": {
            "mode": "verbose",
        },
        "params": {
            "sessionString": params.get('sessionString'),
            "eventId": params.get('eventId'),
            "templateType": params.get('templateType'),
            "workspace": params.get('workspace'),
            "actions": params.get('actions'),
            "resultTopic": params.get('resultTopic'),
            "requestTopic": params.get('requestTopic'),
            "iamEntitlementRequestTopic": params.get('iamEntitlementRequestTopic'),
        },
        "services": svcs,
        "updateTag": params.get('updateTag'),
    }

    resp = cartography.cli.run_gcp(body)

    if 'status' in resp and resp['status'] == 'success':
        if resp.get('pagination', None):
            services = []
            for service, pagination in resp.get('pagination', {}).items():
                if pagination.get('hasNextPage', False):
                    services.append({
                        "name": service,
                        "pagination": {
                            "pageSize": pagination.get('pageSize', 1),
                            "pageNo": pagination.get('pageNo', 0) + 1,
                        },
                    })
            if len(services) > 0:
                resp['services'] = services
            else:
                del resp['updateTag']
            del resp['pagination']
        logger.info(f'successfully processed cartography: {resp}')

    else:
        logger.info(f'failed to process cartography: {resp["message"]}')

    publish_response(logger, body, resp, params)

    logger.info(f'inventory sync gcp response - {params.get("eventId")}: {json.dumps(resp)}')


def publish_response(logger, req, resp, params):
    body = {
        "status": resp['status'],
        "params": req['params'],
        "accountEmail": req['credentials']['account_email'],
        "sessionString": req['params']['sessionString'],
        "eventId": req['params']['eventId'],
        "templateType": req['params']['templateType'],
        "workspace": req['params']['workspace'],
        "actions": req['params']['actions'],
        "resultTopic": req['params'].get('resultTopic'),
        "requestTopic": req['params'].get('requestTopic'),
        "response": resp,
        "services": resp.get("services", None),
        "updateTag": resp.get("updateTag", None),
    }

    pubsub_helper = PubSubLibrary()

    status = None
    try:
        if body.get('services', None):
            if 'requestTopic' in req['params']:
                # Result should be pushed to "requestTopic" passed in the request
                status = pubsub_helper.publish(
                    os.environ['CDX_PROJECT_ID'], json.dumps(body), req['params']['requestTopic'],
                )

        elif 'resultTopic' in req['params']:
            # Result should be pushed to "resultTopic" passed in the request
            # status = pubsub_helper.publish(
            #     os.environ['CDX_PROJECT_ID'], json.dumps(body), req['params']['resultTopic'],
            # )

            logger.info(f'Result not published anywhere. since we want to avoid query when inventory is refreshed')
            status = True
            status = pubsub_helper.publish(
                os.environ['CDX_PROJECT_ID'], json.dumps(params), req['params']['iamEntitlementRequestTopic'],
            )

        else:
            logger.info('publishing results to CARTOGRAPHY_RESULT_TOPIC')
            status = pubsub_helper.publish(
                os.environ['CDX_PROJECT_ID'], json.dumps(body), os.environ['CARTOGRAPHY_RESULT_TOPIC'],
            )
            status = pubsub_helper.publish(
                os.environ['CDX_PROJECT_ID'], json.dumps(params), req['params']['iamEntitlementRequestTopic'],
            )

        logger.info(f'result published to PubSub with status: {status}')

    except PubSubPublishError as e:
        logger.error(f'Failed while publishing response to PubSub: {str(e)}')


def bitbucket_process_request(logger, params):
    logger.info(f'request - {params.get("templateType")} - {params.get("eventId")} - {params.get("workspace")}')

    svcs = []
    for svc in params.get('services', []):
        page = svc.get('pagination', {}).get('pageSize')
        if page:
            svc['pagination']['pageSize'] = 10000

        svcs.append(svc)

    body = {
        "credentials": {
            'account_email': params['accountEmail'],
            'token_uri': os.environ['CDX_TOKEN_URI'],
        },
        "neo4j": {
            "uri": os.environ.get('neo4juri'),
            "user": os.environ.get('neo4juser'),
            "pwd": os.environ.get('neo4jpwd'),
            "connection_lifetime": 200,
        },
        "logging": {
            "mode": "verbose",
        },
        "bitbucket": {
            'client_id': os.environ['bitbucket_client_id'],
            'client_secret': os.environ['bitbucket_client_secret'],
            "refresh_token": os.environ['bitbucket_refresh_token'],
            "access_token": get_access_token(os.environ['bitbucket_client_id'], os.environ['bitbucket_client_secret'], os.environ['bitbucket_refresh_token']),
        },
        "params": {
            "sessionString": params.get('sessionString'),
            "eventId": params.get('eventId'),
            "templateType": params.get('templateType'),
            "workspace": params.get('workspace'),
            "actions": params.get('actions'),
            "resultTopic": params.get('resultTopic'),
            "requestTopic": params.get('requestTopic'),
        },
        "services": svcs,
        "updateTag": params.get('updateTag'),
    }

    resp = cartography.cli.run_bitbucket(body)

    if 'status' in resp and resp['status'] == 'success':
        if resp.get('pagination', None):
            services = []
            for service, pagination in resp.get('pagination', {}).items():
                if pagination.get('hasNextPage', False):
                    services.append({
                        "name": service,
                        "pagination": {
                            "pageSize": pagination.get('pageSize', 1),
                            "pageNo": pagination.get('pageNo', 0) + 1,
                        },
                    })
            if len(services) > 0:
                resp['services'] = services
            else:
                del resp['updateTag']
            del resp['pagination']
        logger.info(f'successfully processed cartography: {resp}')

    else:
        logger.info(f'failed to process cartography: {resp["message"]}')

    publish_response(logger, body, resp, params)

    logger.info(f'inventory sync gcp response - {params.get("eventId")}: {json.dumps(resp)}')


def github_process_request(logger, params):
    logger.info(f'request - {params.get("templateType")} - {params.get("eventId")} - {params.get("workspace")}')

    svcs = []
    for svc in params.get('services', []):
        page = svc.get('pagination', {}).get('pageSize')
        if page:
            svc['pagination']['pageSize'] = 10000

        svcs.append(svc)
    # github_config must be encoded
    # format={"organization":[{"token":"",url="","name":""}]}
    body = {
        "credentials": {
            'account_email': params['accountEmail'],
            'token_uri': os.environ['CDX_TOKEN_URI'],
        },
        "neo4j": {
            "uri": os.environ.get('neo4juri'),
            "user": os.environ.get('neo4juser'),
            "pwd": os.environ.get('neo4jpwd'),
            "connection_lifetime": 200,
        },
        "logging": {
            "mode": "verbose",
        },
        "github_config": params['github_config'],
        "params": {
            "sessionString": params.get('sessionString'),
            "eventId": params.get('eventId'),
            "templateType": params.get('templateType'),
            "workspace": params.get('workspace'),
            "actions": params.get('actions'),
            "resultTopic": params.get('resultTopic'),
            "requestTopic": params.get('requestTopic'),
        },
        "services": svcs,
        "updateTag": params.get('updateTag'),
    }

    resp = cartography.cli.run_github(body)

    if 'status' in resp and resp['status'] == 'success':
        if resp.get('pagination', None):
            services = []
            for service, pagination in resp.get('pagination', {}).items():
                if pagination.get('hasNextPage', False):
                    services.append({
                        "name": service,
                        "pagination": {
                            "pageSize": pagination.get('pageSize', 1),
                            "pageNo": pagination.get('pageNo', 0) + 1,
                        },
                    })
            if len(services) > 0:
                resp['services'] = services
            else:
                del resp['updateTag']
            del resp['pagination']
        logger.info(f'successfully processed cartography: {resp}')

    else:
        logger.info(f'failed to process cartography: {resp["message"]}')

    publish_response(logger, body, resp, params)

    logger.info(f'inventory sync gcp response - {params.get("eventId")}: {json.dumps(resp)}')


def get_access_token(client_id: str, client_secret: str, refresh_token: str):
    try:
        TOKEN_URL = 'https://bitbucket.org/site/oauth2/access_token'
        token_req_payload = {'grant_type': 'refresh_token', 'refresh_token': refresh_token}
        response: Response = requests.post(TOKEN_URL, data=token_req_payload, allow_redirects=False, auth=(client_id, client_secret))
        if response.status_code == requests.codes['ok']:
            output: dict = response.json()
            return output.get('access_token')
        return None
    except RequestException as e:
        logging.info(f"geting error access token{e}")
        return None
