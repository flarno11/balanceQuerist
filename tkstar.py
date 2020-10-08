from datetime import timezone
from json.decoder import JSONDecodeError

import requests
import json
import datetime
from bs4 import BeautifulSoup

from lib import fix_lazy_json
import logging

log = logging.getLogger('werkzeug')


class BalanceException(Exception):
    def __str__(self):
        return 'BalanceException'


class LoginException(BalanceException):
    def __str__(self):
        return 'LoginException'


class DownloadException(BalanceException):
    def __str__(self):
        return 'DownloadException'


def fetch_info(device_id, key):
    res = requests.post('https://www.mytkstar.net:8089/openapiv3.asmx/GetTracking', data={
        'DeviceID': device_id,
        'Key': key,
        'MapType': 'Google',
        'TimeZones': '2:00',
        'Model': '0',
        'Language': 'en_US'
    }, headers={
        'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.1; Pixel Build/NMF26U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.91 Mobile Safari/537.36'
    })

    if res.status_code != 200:
        raise DownloadException()

    soup_mysite = BeautifulSoup(res.text, "html.parser")
    result = json.loads(soup_mysite.find_all()[0].text)
    result['id'] = device_id
    result['positionTime'] = datetime.datetime.strptime(result['positionTime'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    return result
