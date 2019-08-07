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


def fetch_info(username, password, user_id, device_id):
    s = requests.Session()
    log.info(s.cookies)
    s.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:58.0) Gecko/20100101 Firefox/58.0';

    res = s.get('http://mytkstar.net/Login.aspx')
    soup_mysite = BeautifulSoup(res.text, "html.parser")
    input_fields = {input.get('name'): input.get('value') for input in soup_mysite.find_all("input")}
    input_fields['txtImeiNo'] = username
    input_fields['txtImeiPassword'] = password
    res = s.post('http://mytkstar.net/Login.aspx', data=input_fields, allow_redirects=False)
    log.info('login POST request headers: ' + str(res.request.headers))
    log.info('login POST response headers: ' + str(res.headers))
    if res.status_code != 200 or '.ASPXAUTH' not in s.cookies:
        log.info('login response status_code=' + str(res.status_code))
        log.info('session cookies=' + str(s.cookies))
        raise LoginException()

    def post():
        return s.post('http://mytkstar.net/Ajax/DevicesAjax.asmx/GetDevicesByUserID',
                 json={'UserID': user_id,'isFirst':False,'TimeZones':'2:00','DeviceID':device_id,'IsKM':1},
                 headers={'Accept': 'application/json'})

    res = post()
    if res.status_code != 200:
        log.info(res.status_code)
        log.info(res.headers)
        raise DownloadException()

    encoded_json_str = res.json()['d']
    log.info('encoded_json_str=' + encoded_json_str)
    if not encoded_json_str:
        raise DownloadException()

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
