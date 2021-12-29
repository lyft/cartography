import datetime
import uuid

from azure.core.credentials import AzureKeyCredential
from azure.eventgrid import EventGridEvent
from azure.eventgrid import EventGridPublisherClient


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
            print(f'error while publishing message to queue: {e}')

            return {
                "status": "failure",
                "message": "failed to publish message to queue",
            }
