#!/bin/sh

echo "Starting up..."

# Boto3 has a bug where passing in environment variables does not work as documented in
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#environment-variables
#echo "Settings AWS Credentials File"
#echo -e "[default]\naws_access_key_id=${AWS_ACCESS_KEY_ID}\naws_secret_access_key=${AWS_SECRET_ACCESS_KEY}\naws_session_token=${AWS_SESSION_TOKEN}" >> ~/.aws/credentials
#echo "Done with settings aws credentials"

# Test that env vars are passed successfully
#echo $AWS_ACCESS_KEY_ID
#echo $AWS_SECRET_ACCESS_KEY
#echo $AWS_SESSION_TOKEN
#echo $AWS_DEFAULT_REGION

echo "Starting Cartography..."
cartography --neo4j-uri bolt://neo4j:7687 --neo4j-user $NEO4J_USERNAME --neo4j-password-env-var NEO4J_PASSWORD --aws-sync-all-profiles
