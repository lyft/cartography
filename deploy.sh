#!/usr/bin/env zsh

# Reference - https://medium.com/better-programming/how-to-store-your-aws-lambda-secrets-cheaply-without-compromising-scalability-or-security-d3e8a250f12c

echo "Begin Set Environment Variables"

# Parse Arguments
# Parse Arguments
ENV=${1-}
file_name=".env.aws.${ENV}.json"

if [[ $ENV == "" ]]
then
	echo "Environment name is required, supported values: development, production"

	exit
fi

region=$(cat $file_name | jq -r '.region')
export CLOUDANIX_DEFAULT_REGION=$region

log_level=$(cat $file_name | jq -r '.logLevel')
export CLOUDANIX_DEFAULT_LOG_LEVEL=$log_level

app_env=$(cat $file_name | jq -r '.appEnv')
export CLOUDANIX_APP_ENV=$app_env

echo "End Set Environment Variables"

echo "Begin deployment for AWS Service Worker"

# sls deploy --force

echo "End deployment for AWS Service Worker"
