#!/usr/bin/env zsh

# Reference - https://medium.com/better-programming/how-to-store-your-aws-lambda-secrets-cheaply-without-compromising-scalability-or-security-d3e8a250f12c

echo "Begin Set Environment Variables"

# Parse Arguments
# Parse Arguments
ENV=${1-}
filename=".env.${ENV}.json"

if [[ $ENV == "" ]]
then
	echo "Environment name is required, supported values: development, production"

	exit
fi

region=$(cat $filename | jq -r '.region')
export CLOUDANIX_DEFAULT_REGION=$region

logLevel=$(cat $filename | jq -r '.logLevel')
export CLOUDANIX_DEFAULT_LOG_LEVEL=$logLevel

appEnv=$(cat $filename | jq -r '.appEnv')
export CLOUDANIX_APP_ENV=$appEnv

echo "End Set Environment Variables"

echo "Begin deployment for AWS Service Worker"

sls deploy --force

echo "End deployment for AWS Service Worker"
