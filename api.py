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
        device_id=os.environ['TKSTAR_DEVICEID'],
        key=os.environ['TKSTAR_KEY'],
    )


@app.route('/simCards')
def sim_card_info():
    return jsonify(easym2m.fetch_balance(os.environ['EASYM2M_USERNAME'], os.environ['EASYM2M_PASSWORD'], os.environ['EASYM2M_APIKEY']))


@app.route('/tkStar')
def tkstar_info():
    return jsonify(fetch_tkstar())


@app.route('/metrics')
def metrics():
    results = []

    data = easym2m.fetch_balance(os.environ['EASYM2M_USERNAME'], os.environ['EASYM2M_PASSWORD'], os.environ['EASYM2M_APIKEY'])
    results.append('total_balance ' + str(data['total_balance']))
    for sim_card_data in data['sim_cards']:
        results.append('sim_status{iccid="' + sim_card_data['iccid'] + '"} ' + str(sim_card_data['status']))
        results.append('balance{iccid="' + sim_card_data['iccid'] + '"} ' + str(sim_card_data['balance']))
        results.append('usage_data{iccid="' + sim_card_data['iccid'] + '"} ' + str(sim_card_data['consumptionMonthlyDataValue']))

    device = fetch_tkstar()
    device_id = str(device['id'])
    results.append('updated_at{deviceId="' + device_id + '"} ' + str(device['positionTime'].timestamp()))
    results.append('battery_level{deviceId="' + device_id + '"} ' + str(device['battery']))

    response = make_response("\n".join(results) + "\n")
    response.headers["content-type"] = "text/plain"
    return response


if __name__ == "__main__":
    # port = int(os.getenv("VCAP_APP_PORT", "-1"))
    app.run()
