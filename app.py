import json
from flask import Flask, jsonify, request
import cartography.cli
import requests
from requests.exceptions import RequestException
from settings.config import get_config

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


def process_request(req):
    resp = cartography.cli.run(req)
    return resp


if __name__ == "__main__":
    # sys.exit(process_request())
    app.run(host="0.0.0.0", port=7000)
