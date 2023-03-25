from typing import Dict
import datetime
import json
import logging
import os
import uuid

import azure.functions as func

import cartography.cli
from libraries.eventgridlibrary import EventGridLibrary


def process_request(msg: Dict):
    logging.info(f'{msg["templateType"]} request received - {msg["eventId"]} - {msg["workspace"]}')

    svcs = []
    for svc in msg.get('services', []):
        page = svc.get('pagination', {}).get('pageSize')
        if page:
            svc['pagination']['pageSize'] = 50000

        svcs.append(svc)

    body = {
        "azure": {
            "client_id": os.environ.get('client_id'),
            "client_secret": os.environ.get('client_secret'),
            "redirect_uri": os.environ.get('redirect_uri'),
            "subscription_id": msg.get('workspace', {}).get('account_id'),
            "tenant_id": msg.get('tenantId'),
            "refresh_token": msg.get('refreshToken'),
            "graph_scope": os.environ.get('graph_scope'),
            "azure_scope": os.environ.get('azure_scope'),
            "vault_scope": os.environ.get('vault_scope'),
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
            "sessionString": msg.get('sessionString'),
            "eventId": msg.get('eventId'),
            "templateType": msg.get('templateType'),
            "workspace": msg.get('workspace'),
            "subscriptions": msg.get('subscriptions'),
            "actions": msg.get('actions'),
            "resultTopic": msg.get('resultTopic'),
            "requestTopic": msg.get('requestTopic'),
        },
        "services": svcs,
        "updateTag": msg.get('updateTag'),
    }

    resp = cartography.cli.run_azure(body)

    if 'status' in resp and resp['status'] == 'success':
        if resp.get('pagination', None):
            services = []
            for service, pagination in resp.get('pagination', {}).items():
                if pagination.get('hasNextPage', False):
                    services.append({
                        "name": service,
                        "pagination": {
                            "pageSize": pagination.get('pageSize', 1),
                            "pageNo": pagination.get('pageNo', 0) + 1
                        }
                    })
            if len(services) > 0:
                resp['services'] = services
            else:
                del resp['updateTag']
            del resp['pagination']

        logging.info(f'successfully processed cartography: {resp}')

    return resp


def main(event: func.EventGridEvent, outputEvent: func.Out[func.EventGridOutputEvent]):
    logging.info('worker request received via EventGrid')

    try:
        msg = event.get_json()

        logging.info(f'request: {msg}')

        resp = process_request(msg)

        if resp.get('status') == 'success':
            logging.info(f'successfully processed cartography: {msg["eventId"]} - {json.dumps(resp)}')

        else:
            logging.info(f'failed to process cartography: {msg["eventId"]} - {resp["message"]}')

        message = {
            "status": resp.get('status'),
            "params": msg.get('params'),
            "sessionString": msg.get('sessionString'),
            "eventId": msg.get('eventId'),
            "templateType": msg.get('templateType'),
            "workspace": msg.get('workspace'),
            "subscriptions": msg.get('subscriptions'),
            "actions": msg.get('actions'),
            "resultTopic": msg.get('resultTopic'),
            "requestTopic": msg.get('requestTopic'),
            "response": resp,
            "services": resp.get("services", None),
            "updateTag": resp.get("updateTag", None),
        }

        if message.get('services', None):
            if 'requestTopic' in message:
                # Result should be pushed to "requestTopic" passed in the request

                # Push message to Cartography Queue, if refresh is needed
                topic = os.environ.get('requestTopic')
                access_key = os.environ.get('requestTopicAccessKey')

                lib = EventGridLibrary(topic, access_key)
                resp = lib.publish_event(message)

        elif 'resultTopic' in message:
            # topic = message['resultTopic']
            # access_key = msg['resultTopicAccessKey']

            # lib = EventGridLibrary(topic, access_key)
            # resp = lib.publish_event(message)

            logging.info(f'Result not published anywhere. since we want to avoid query when inventory is refreshed')

        else:
            logging.info('publishing results to CARTOGRAPHY_RESULT_TOPIC')
            outputEvent.set(
                func.EventGridOutputEvent(
                    id=str(uuid.uuid4()),
                    data=message,
                    subject="cartography-response",
                    event_type="inventory",
                    event_time=datetime.datetime.now(datetime.timezone.utc),
                    data_version="1.0",
                ),
            )

        logging.info(f'worker processed successfully: {msg["eventId"]}')

    except Exception as ex:
        logging.error(f"failed to process request from event grid: {ex}", exc_info=True, stack_info=True)
