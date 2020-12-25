import json
import os
from flask import Flask, jsonify, request
import cartography.cli
import requests
from requests.exceptions import RequestException
from settings.config import get_config
from utils.logger import get_logger
from libraries.authlibrary import AuthLibrary
from libraries.snslibrary import SNSLibrary

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)

app = Flask(__name__)
# app.config["DEBUG"] = True


@app.route('/', methods=["GET"])
def index():
    return jsonify({"message": "Welcome to Cartography!"})


@app.route("/sync", methods=["POST"])
def initiate_sync():
    req = request.get_json()

    isAuthorized = False
    config = get_config()
    if 'Authorization' in request.headers:
        if request.headers['Authorization'] == config['authorization']['value']:
            isAuthorized = True

    if not isAuthorized:
        return jsonify({
            "status": "failure",
            "message": "Invalid Authorization Code"
        })

    resp = cartography.cli.run(req)

    send_response_to_lambda(config, req, resp)

    return jsonify(resp)


def send_response_to_lambda(config, req, resp):
    headers = {
        'Authorization': config['lambda']['authorization'],
        'content-type': 'application/json'
    }

    body = {
        "status": "success",
        "params": req['params'],
        "response": resp
    }

    r = ""
    try:
        r = requests.post(
            req['callbackURL'],
            data=json.dumps(body),
            headers=headers,
            timeout=_TIMEOUT,
        )

        print(f"response from processor: {r.status_code} - {r.content}")

    except RequestException as e:
        print(f"failed to publish results to lambda: {str(e)}")


def process_request(config, logger, args):
    creds = get_auth_creds(config, logger, args)

    body = {
        "credentials": creds,
        "neo4j": config['neo4j'],
        "logging": {
            "mode": "verbose",
        },
        "params": {
            "sessionString": args['sessionString'],
            "eventId": args['eventId'],
            "templateType": args['templateType'],
            "workspace": args['workspace']
        }
    }

    resp = cartography.cli.run(body)

    publish_response(config, logger, body, resp)

    return resp


def publish_response(config, logger, req, resp):
    if os.environ['LAMBDA_APP_ENV'] != 'production':
        try:
            with open('response.json', 'w') as outfile:
                json.dump(resp, outfile, indent=2)

        except Exception as e:
            logger.error(f'Failed to write to file: {str(e)}')

    else:
        body = {
            "status": "success",
            "params": req['params'],
            "response": resp
        }

        sns_helper = SNSLibrary(config['sns'], logger)
        status = sns_helper.publish(json.dumps(body), config['sns']['resultTopic'])

        logger.info(f'result published to SNS with status: {status}')


def get_auth_creds(config, logger, args):
    auth_helper = AuthLibrary(config, logger)

    # TODO: implement debug option for test without assume role creds
    if os.environ['LAMBDA_APP_ENV'] == 'production' or os.environ['LAMBDA_APP_ENV'] == 'debug':
        auth_params = {
            'aws_access_key_id': auth_helper.get_assume_role_access_key(),
            'aws_secret_access_key': auth_helper.get_assume_role_access_secret(),
            'role_session_name': args['sessionString'],
            'role_arn': args['externalRoleArn'],
            'external_id': args['externalId']
        }

        auth_creds = auth_helper.assume_role(auth_params)
        auth_creds['type'] = 'assumerole'

    else:
        auth_creds = {
            'type': 'self',
            'aws_access_key_id': args['credentials']['awsAccessKeyID'] if 'credentials' in args else None,
            'aws_secret_access_key': args['credentials']['awsSecretAccessKey'] if 'credentials' in args else None
        }

    return auth_creds


def read_cartography(event, context):
    print('inside read cartography')

    config = get_config()
    logger = get_logger(config)

    params = json.loads(event['body'])

    logger.info(f'request: {params}')

    for k, v in sorted(os.environ.items()):
        print(k + ':', v)

    print('\n')
    # list elements in path environment variable
    [print(item) for item in os.environ['PATH'].split(';')]

    return {
        'statusCode': 200,
        'body': json.dumps({
            "status": 'success'
        })
    }


def load_cartography(event, context):
    config = get_config()
    logger = get_logger(config)

    # params = json.loads(event['body'])

    # logger.info(f'request: {params}')

    logger.info('inventory sync aws worker request received via SNS')

    record = event['Records'][0]
    message = record['Sns']['Message']

    # logger.info(f'message from SNS: {message}')
    try:
        params = json.loads(message)

    except Exception as e:
        logger.error(f'error while parsing inventory sync aws request json: ${e}')

        return {
            "status": 'failure',
            "message": 'unable to parse request'
        }

    response = process_request(config, logger, params)

    logger.info(f'inventory sync aws response from worker: {json.dumps(response)}')

    return {
        'statusCode': 200,
        'body': json.dumps({
            "status": 'success'
        })
    }


if __name__ == "__main__":
    # sys.exit(process_request())
    app.run(host="0.0.0.0", port=7000)
