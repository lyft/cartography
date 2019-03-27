#!/bin/sh

echo "Starting up..."

echo "Settings AWS Credentials File"
echo -e "[default]\naws_access_key_id=${AWS_ACCESS_KEY_ID}\naws_secret_access_key=${AWS_SECRET_ACCESS_KEY}\naws_session_token=${AWS_SESSION_TOKEN}" >> ~/.aws/credentials
echo "Done with settings aws credentials"

echo "Starting Cartography..."
cartography --neo4j-uri bolt://neo4j:7687 --neo4j-user $USERNAME --neo4j-password-env-var NEO4J_PASS
