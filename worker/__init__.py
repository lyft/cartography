import datetime
import json
import logging
import os
import uuid

import azure.functions as func

import cartography.cli
from libraries.eventgridlibrary import EventGridLibrary


def process_request(msg):
    logging.info(f'{msg["templateType"]} request received - {msg["eventId"]} - {msg["workspace"]}')

    body = {
        "azure": {
            "client_id": os.environ.get('client_id'),
            "client_secret": os.environ.get('client_secret'),
            "redirect_uri": os.environ.get('redirect_uri'),
            "subscription_id": msg['workspace']['account_id'],
            "refresh_token": msg['refreshToken'],
            "graph_scope": os.environ.get('graph_scope'),
            "azure_scope": os.environ.get('azure_scope'),
        },
        "neo4j": {
            "uri": os.environ.get('neo4juri'),
            "user": os.environ.get('neo4juser'),
            "pwd": os.environ.get('neo4jpwd'),
        },
        "logging": {
            "mode": "verbose",
        },
        "params": {
            "sessionString": msg['sessionString'],
            "eventId": msg['eventId'],
            "templateType": msg['templateType'],
            "workspace": msg['workspace'],
        },
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
            "status": resp['status'],
            "params": {
                "sessionString": msg['sessionString'],
                "eventId": msg['eventId'],
                "templateType": msg['templateType'],
                "subscriptions": msg['subscriptions'],
                "workspace": msg['workspace'],
                "actions": msg['actions'],
                "resultTopic": msg['resultTopic'],
                "requestTopic": msg.get("requestTopic", None),
            },
            "response": resp,
            "services": resp.get("services", None),
            "updateTag": resp.get("updateTag", None),
        }

        if message.get('services', None):
            if 'requestTopic' in message['params']:
                logging.info(f'inventoryRefresh - {msg["inventoryRefresh"]}')
                # Push message to Cartography Queue, if refresh is needed
                # Post processing, result should be pushed to Inventory Views Request Topic
                # without 'inventoryRefresh' field
                topic = message['requestTopic']
                access_key = msg['requestTopicAccessKey']

                lib = EventGridLibrary(topic, access_key)
                resp = lib.publish_event(message)

            logging.info('Result not published anywhere. since we want to avoid query when inventory is refreshed')

            logging.info(f'inventoryRefresh completed: {resp}')

        elif 'resultTopic' in message['params']:
            topic = message['resultTopic']
            access_key = msg['resultTopicAccessKey']

            lib = EventGridLibrary(topic, access_key)
            resp = lib.publish_event(message)

        else:
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

    except Exception as e:
        logging.info(f'failed to process request from event grid: {str(e)}')
