from datetime import timezone
from json.decoder import JSONDecodeError

import requests
import json
import datetime
from bs4 import BeautifulSoup

from lib import fix_lazy_json


class BalanceException(Exception):
    def __str__(self):
        return 'BalanceException'


class LoginException(BalanceException):
    def __str__(self):
        return 'LoginException'


class DownloadException(BalanceException):
    def __str__(self):
        return 'DownloadException'


def fetch_info(username, password, user_id, device_id):
    s = requests.Session()
    s.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:54.0) Gecko/20100101 Firefox/54.0';

    res = s.get('http://mytkstar.net/Login.aspx')
    soup_mysite = BeautifulSoup(res.text, "html.parser")
    input_fields = {input.get('name'): input.get('value') for input in soup_mysite.find_all("input")}
    input_fields['txtImeiNo'] = username
    input_fields['txtImeiPassword'] = password
    res = s.post('http://mytkstar.net/Login.aspx', data=input_fields, allow_redirects=False)
    if res.status_code != 200:
        print(res.status_code)
        print(res.headers)
        for line in res.iter_lines():
            print(line)
        raise LoginException()

    def post():
        return s.post('http://mytkstar.net/Ajax/DevicesAjax.asmx/GetDevicesByUserID',
                 json={'UserID': user_id,'isFirst':False,'TimeZones':'2:00','DeviceID':device_id},
                 headers={'Accept': 'application/json'})

    res = post()
    if res.status_code != 200:
        print(res.status_code)
        print(res.headers)
        raise DownloadException()

    encoded_json_str = res.json()['d']
    print('encoded_json_str=' + encoded_json_str)
    if not encoded_json_str:
        print(res.headers)
        for line in res.iter_lines():
            print(line)
        res = post()
        encoded_json_str = res.json()['d']

    try:
        result = json.loads(fix_lazy_json(encoded_json_str))
    except JSONDecodeError:
        raise DownloadException()

    if len(result['devices']) != 1:
        raise DownloadException()

    device = result['devices'][0]

    device['deviceUtcDate'] = datetime.datetime.strptime(device['deviceUtcDate'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    device['serverUtcDate'] = datetime.datetime.strptime(device['serverUtcDate'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)

    return device