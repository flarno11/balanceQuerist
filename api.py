import os
import json
import datetime

from flask import Flask, jsonify
from flask.helpers import make_response

import easym2m
import tkstar

app = Flask(__name__)

TimeFormat = "%Y-%m-%dT%H:%M:%S.%fZ"


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime(TimeFormat)
        return json.JSONEncoder.default(self, o)

app.json_encoder = JSONEncoder


@app.errorhandler(500)
def handle_internal_server_error(e):
    response = jsonify({'message': str(e)})
    response.status_code = 500
    return response


def fetch_tkstar():
    return tkstar.fetch_info(
        username=os.environ['TKSTAR_USERNAME'],
        password=os.environ['TKSTAR_PASSWORD'],
        user_id=os.environ['TKSTAR_USERID'],
        device_id=os.environ['TKSTAR_DEVICEID'],
    )


@app.route('/simCards')
def sim_card_info():
    return jsonify(easym2m.fetch_balance(os.environ['EASYM2M_USERNAME'], os.environ['EASYM2M_PASSWORD']))


@app.route('/tkStar')
def tkstar_info():
    return jsonify(fetch_tkstar())


@app.route('/metrics')
def metrics():
    data = easym2m.fetch_balance(os.environ['EASYM2M_USERNAME'], os.environ['EASYM2M_PASSWORD'])
    results = ['total_balance ' + str(data['total_balance'])]
    for sim_card_data in data['sim_cards']:
        if sim_card_data['status'] != 'DEACTIVATED':
            results.append('balance{iccid="' + sim_card_data['iccid'] + '"} ' + str(sim_card_data['balance']))
            results.append('usage_data{iccid="' + sim_card_data['iccid'] + '"} ' + str(sim_card_data['usage_data']))

    device = fetch_tkstar()
    device_id = str(device['id'])
    results.append('updated_at{deviceId="' + device_id + '"} ' + str(device['deviceUtcDate'].timestamp()))
    results.append('battery_level{deviceId="' + device_id + '"} ' + str(-float(device['dataContext'])))

    response = make_response("\n".join(results) + "\n")
    response.headers["content-type"] = "text/plain"
    return response


if __name__ == "__main__":
    # port = int(os.getenv("VCAP_APP_PORT", "-1"))
    app.run()
