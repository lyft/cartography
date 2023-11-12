# https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/pubsub/cloud-client/publisher.py
# https://google-cloud-python.readthedocs.io/en/0.32.0/pubsub/index.html#publishing
import logging
import traceback

from google.cloud import pubsub_v1

from utils.errors import PubSubPublishError


class PubSubLibrary:
    def publish(self, project_id, message, topic):
        publisher = pubsub_v1.PublisherClient()

        topic_path = publisher.topic_path(project_id, topic)

        # Data must be a bytestring
        data = message.encode("utf-8")

        try:
            # When you publish a message, the client returns a message_id
            message_id = publisher.publish(topic_path, data=data).result()
            logging.info(f'PubSub publish payload success: {message_id}')

            return True

        except Exception as ex:
            logging.error(f'PubSub publish payload failed: {str(ex)}')

            traceback.print_exception(type(ex), ex, ex.__traceback__)

            raise PubSubPublishError(f'failed to publish message to {topic}')
