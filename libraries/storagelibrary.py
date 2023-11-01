# https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/pubsub/cloud-client/publisher.py
# https://pypi.org/project/google-cloud-storage/
# https://googleapis.dev/python/storage/latest/client.html
# https://github.com/GoogleCloudPlatform/python-docs-samples/tree/master/storage/signed_urls
import logging
import traceback
from datetime import timedelta

from google.auth import compute_engine
from google.auth.transport import requests
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError


class StorageLibrary:
    def upload_payload(self, bucket, file_name, payload):
        storage_client = storage.Client()
        try:
            bucket = storage_client.get_bucket(bucket)

            blob = bucket.blob(file_name)

            blob.upload_from_string(payload)

            blob.content_type = 'application/json'
            blob.content_disposition = f'attachment; filename={file_name}'
            blob.patch()

            return True

        except (AttributeError, GoogleCloudError) as ex:
            logging.error(f'error while uploading payload to google storage: {str(ex)}')

            traceback.print_exception(type(ex), ex, ex.__traceback__)

            return False

    def generate_signed_uri(self, bucket, file_name, duration):
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket)

        blob = bucket.get_blob(file_name)

        # To fix you need a private key to sign credentials.the credentials you are currently using <class 'google.auth.compute_engine.credentials.Credentials'> just contains a token. see https://googleapis.dev/python/google-api-core/latest/auth.html#setting-up-a-service-account for more details.
        # Reference - https://gist.github.com/jezhumble/91051485db4462add82045ef9ac2a0ec

        auth_request = requests.Request()
        signing_credentials = compute_engine.IDTokenCredentials(auth_request, "", storage_client._credentials.service_account_email)

        url = blob.generate_signed_url(
            version="v4",
            # This URL is valid for 15 minutes
            expiration=timedelta(minutes=duration),
            # Allow GET requests using this URL.
            method='GET',
            credentials=signing_credentials,
        )

        return url
