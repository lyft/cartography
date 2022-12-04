# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/kms-example-encrypt-decrypt-file.html
# https://github.com/awsdocs/aws-doc-sdk-examples/blob/master/python/example_code/kms/encrypt_decrypt_file.py
import base64

import boto3
from neo4j.exceptions import ClientError

from utils.errors import classify_error


class KMSLibrary:
    def __init__(self, context):
        self.context = context

    # create_key is tested and verified
    def create_key(self, key_desc, tags):
        # Create the KMS client
        kms_client = boto3.client('kms', self.context.region)

        try:
            response = kms_client.create_key(Description=key_desc, Tags=tags)

        except ClientError as e:
            raise classify_error(self.context.logger, e, 'Failed to create key')

        # Return the encrypted and plaintext data key
        return response['KeyMetadata']['KeyId']

    # encrypt is tested and verified
    def encrypt(self, key_id, plain_text):
        # Generate bytes from plain_text
        text_bytes = plain_text.encode('utf-8')

        # Create the KMS client
        kms_client = boto3.client('kms', self.context.region)

        try:
            # Encrypt the data plain_text with key_id
            response = kms_client.encrypt(
                KeyId=key_id,
                Plaintext=text_bytes,
            )

        except ClientError as e:
            raise classify_error(self.context.logger, e, 'Failed to encrypt data with key')

        # Generate base64 bytes from CiphertextBlob
        base64_bytes = base64.b64encode(response['CiphertextBlob'])

        # Generate utf-8 string from base64_byte
        return base64_bytes.decode('utf-8')

    # decrypt is tested and verified
    def decrypt(self, cipher):
        # Generate bytes from cipher
        cipher_bytes = cipher.encode('utf-8')

        # Base64 decode the bytes
        base64_bytes = base64.b64decode(cipher_bytes)

        # Create the KMS client
        kms_client = boto3.client('kms', self.context.region)

        try:
            # Decrypt the cipher
            response = kms_client.decrypt(
                CiphertextBlob=base64_bytes,
            )

        except ClientError as e:
            raise classify_error(self.context.logger, e, 'Failed to decrypt cipher')

        # Return plaintext decoded in utf-8
        return response['Plaintext'].decode('utf-8')
