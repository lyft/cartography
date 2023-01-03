import json
import os

import cartography.cli
from libraries.authlibrary import AuthLibrary
from libraries.kmslibrary import KMSLibrary
from libraries.snslibrary import SNSLibrary
from utils.context import AppContext
from utils.logger import get_logger
# import requests
# from requests.exceptions import RequestException
# from flask import Flask, jsonify, request


lambda_init = None
context = None


def init_lambda(ctx):
    global lambda_init, context

    context = AppContext(
        region=os.environ['CLOUDANIX_DEFAULT_REGION'],
        log_level=os.environ['CLOUDANIX_DEFAULT_LOG_LEVEL'],
        app_env=os.environ['CLOUDANIX_APP_ENV'],
    )
    context.logger = get_logger(context.log_level)

    config = os.environ['CLOUDANIX_CONFIG']

    kms_library = KMSLibrary(context)
    decrypted_value = kms_library.decrypt(config)

    # Cloudanix AWS AccountID
    context.aws_account_id = ctx.invoked_function_arn.split(":")[4]
    context.parse(decrypted_value)

    lambda_init = True


def load_cartography(event, ctx):
    global lambda_init, context
    if not lambda_init:
        init_lambda(ctx)

    # params = json.loads(event['body'])

    # context.logger.info(f'request: {params}')

    context.logger.info('inventory sync aws worker request received via SNS')

    record = event['Records'][0]
    message = record['Sns']['Message']

    # context.logger.info(f'message from SNS: {message}')
    try:
        params = json.loads(message)

    except Exception as e:
        context.logger.error(f'error while parsing inventory sync aws request json: {e}', exc_info=True, stack_info=True)

        return {
            "status": 'failure',
            "message": 'unable to parse request',
        }

    process_request(context, params)

    return {
        'statusCode': 200,
        'body': json.dumps({
            "status": 'success',
        }),
    }


def process_request(context, args):
    context.logger.info(f'{args["templateType"]} request received - {args["eventId"]}')
    context.logger.info(f'workspace - {args["workspace"]}')

    creds = get_auth_creds(context, args)

    body = {
        "credentials": creds,
        "neo4j": {
            "uri": context.neo4j_uri,
            "user": context.neo4j_user,
            "pwd": context.neo4j_pwd,
        },
        "logging": {
            "mode": "verbose",
        },
        "params": {
            "sessionString": args['sessionString'],
            "eventId": args['eventId'],
            "templateType": args['templateType'],
            "workspace": args['workspace'],
        },
    }

    resp = cartography.cli.run_aws(body)

    if 'status' in resp and resp['status'] == 'success':
        context.logger.info(f'successfully processed cartography: {resp}')

    else:
        context.logger.info(f'failed to process cartography: {resp["message"]}')

    publish_response(context, body, resp)

    context.logger.info(f'inventory sync aws response - {args["eventId"]}: {json.dumps(resp)}')


def publish_response(context, req, resp):
    if context.app_env != 'production':
        try:
            with open('response.json', 'w') as outfile:
                json.dump(resp, outfile, indent=2)

        except Exception as e:
            context.logger.error(f'Failed to write to file: {e}', exc_info=True, stack_info=True)

    else:
        body = {
            "status": resp['status'],
            "params": req['params'],
            "response": resp,
        }

        # context.logger.info(f'response from cartography: {body}')

        sns_helper = SNSLibrary(context)
        status = sns_helper.publish(json.dumps(body), context.aws_inventory_sync_response_topic)

        context.logger.info(f'result published to SNS with status: {status}')


def get_auth_creds(context, args):
    auth_helper = AuthLibrary(context)

    if context.app_env == 'production' or context.app_env == 'debug':
        auth_params = {
            'aws_access_key_id': auth_helper.get_assume_role_access_key(),
            'aws_secret_access_key': auth_helper.get_assume_role_access_secret(),
            'role_session_name': args['sessionString'],
            'role_arn': args['externalRoleArn'],
            'external_id': args['externalId'],
        }

        auth_creds = auth_helper.assume_role(auth_params)
        auth_creds['type'] = 'assumerole'

    else:
        auth_creds = {
            'type': 'self',
            'aws_access_key_id': args['credentials']['awsAccessKeyID'] if 'credentials' in args else None,
            'aws_secret_access_key': args['credentials']['awsSecretAccessKey'] if 'credentials' in args else None,
        }

    return auth_creds

# Flask code starts here
# # Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
# _TIMEOUT = (60, 60)

# app = Flask(__name__)
# # app.config["DEBUG"] = True


# @app.route('/', methods=["GET"])
# def index():
#     return jsonify({"message": "Welcome to Cartography!"})


# @app.route("/sync", methods=["POST"])
# def initiate_sync():
#     req = request.get_json()

#     isAuthorized = False
#     config = get_config()
#     if 'Authorization' in request.headers:
#         if request.headers['Authorization'] == config['authorization']['value']:
#             isAuthorized = True

#     if not isAuthorized:
#         return jsonify({
#             "status": "failure",
#             "message": "Invalid Authorization Code"
#         })

#     resp = cartography.cli.run(req)

#     send_response_to_lambda(config, req, resp)

#     return jsonify(resp)


# def send_response_to_lambda(config, req, resp):
#     headers = {
#         'Authorization': config['lambda']['authorization'],
#         'content-type': 'application/json'
#     }

#     body = {
#         "status": "success",
#         "params": req['params'],
#         "response": resp
#     }

#     r = ""
#     try:
#         r = requests.post(
#             req['callbackURL'],
#             data=json.dumps(body),
#             headers=headers,
#             timeout=_TIMEOUT,
#         )

#         print(f"response from processor: {r.status_code} - {r.content}")

#     except RequestException as e:
#         print(f"failed to publish results to lambda: {e}")


# if __name__ == "__main__":
#     # sys.exit(process_request())
#     app.run(host="0.0.0.0", port=7000)
