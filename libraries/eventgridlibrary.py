import datetime
import logging
import uuid

from azure.core.credentials import AzureKeyCredential
from azure.eventgrid import EventGridEvent
from azure.eventgrid import EventGridPublisherClient

logger = logging.getLogger(__name__)


class EventGridLibrary():
    def __init__(self, topic, access_key):
        # authenticate client
        self.credential = AzureKeyCredential(access_key)
        self.client = EventGridPublisherClient(topic, self.credential)

    def publish_event(self, message):
        event_list = []

        try:
            event = EventGridEvent(
                id=str(uuid.uuid4()),
                subject="inventoryviews-request",
                data=message,
                event_type="inventoryviews",
                event_time=datetime.datetime.now(datetime.timezone.utc),
                data_version="1.0",
            )

            event_list.append(event)
            self.client.send(event_list)

            return {
                "status": "success",
                "message": "successfully published message to queue",
            }

        except Exception as e:
            logging.error(f"failed to publish message to queue: {e}", exc_info=True, stack_info=True)

            return {
                "status": "failure",
                "message": "failed to publish message to queue",
            }
