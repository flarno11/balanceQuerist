import requests
from bs4 import BeautifulSoup


class BalanceException(Exception):
    pass


class LoginException(BalanceException):
    pass


class DownloadException(BalanceException):
    pass


def fetch_balance(username, password, apikey):
    s = requests.Session()
    s.auth = (username, password)
    s.headers['X-Api-Key'] = apikey

    res = s.get('https://www.easym2m.eu/api/v2/customer/balance')

    if res.status_code != 200:
        raise DownloadException()

    if 'balance' not in res.json():
        raise DownloadException()

    total_balance = float(res.json()['balance'])

    res = s.get('https://www.easym2m.eu/api/v2/customer/simcards/100/1/')

    if res.status_code != 200:
        raise DownloadException()

    sim_cards = res.json()['data']

    for sim_card in sim_cards:
        res = s.get('https://www.easym2m.eu/api/v2/customer/balance/' + sim_card['iccid'])

        if 'balance' not in res.json():
            raise DownloadException()

        sim_card['balance'] = float(res.json()['balance'])

    return {'total_balance': total_balance, 'sim_cards': sim_cards}
