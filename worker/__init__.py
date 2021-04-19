import datetime
import json
import logging
import os
import time

from libraries.eventgridlibrary import EventGridLibrary

import azure.functions as func
import cartography.cli


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
            "workspace": msg['workspace']
        }
    }

    resp = cartography.cli.run_azure(body)

    return resp


def main(event: func.EventGridEvent, outputEvent: func.Out[func.EventGridOutputEvent]):
    logging.info('worker request received via EventGrid')

    try:
        msg = event.get_json()

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
                "workspace": msg['workspace']
            },
            "response": resp
        }

        if msg.get('inventoryRefresh'):
            logging.info(f'inventoryRefresh - {msg["inventoryRefresh"]}')
            # Push message to Cartography Queue, if refresh is needed
            # Post processing, result should be pushed to Inventory Views Request Topic
            # without 'inventoryRefresh' field
            topic = msg['resultTopic']
            access_key = msg['resultTopicAccessKey']

            lib = EventGridLibrary(topic, access_key)
            resp = lib.publish_event(message)
            return resp

        outputEvent.set(
            func.EventGridOutputEvent(
                id=time.time(),
                data=message,
                subject="cartography-response",
                event_type="inventory",
                event_time=datetime.datetime.utcnow(),
                data_version="1.0"))

        logging.info(f'worker processed successfully: {msg["eventId"]}')

    except Exception as e:
        logging.info(f'failed to process request from event grid: {str(e)}')
