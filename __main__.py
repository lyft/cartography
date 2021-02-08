# AWS_PROFILE=cloudanix-qa-admin && python3 . --neo4j-uri bolt://127.0.0.1:7687 -v --neo4j-user neo4j --neo4j-password-env-var NEO4J_PWD
# export GOOGLE_APPLICATION_CREDENTIALS=~/.gcloud/cloudanix-qa-cartography-service.json && python3 . --neo4j-uri bolt://127.0.0.1:7687 -v --neo4j-user neo4j --neo4j-password-env-var NEO4J_PWD


import sys
import logging
import cartography.cli


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


if __name__ == "__main__":

    body = {
        "credentials": {
            "type": 'self',
            "aws_access_key_id": 'test-key',
            "aws_secret_access_key": 'test-secret'
        },
        "neo4j": {
            "uri": "bolt://127.0.0.1:7687",
            "user": "neo4j",
            "pwd": "pwd"
        },
        "logging": {
            "mode": "verbose",
        },
        "params": {
            "sessionString": "session-123",
            "eventId": "eventId-123",
            "templateType": "AWSINVENTORYSYNC",
            "workspace": {
                "id_string": "workspace-id_string",
                "name": "workspace_name",
                "account_id": "workspace-account_id"
            }
        }
    }

    resp = cartography.cli.run(body)

    logger.info(f'response from cartography: {resp}')

    sys.exit()
