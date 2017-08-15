import requests
from bs4 import BeautifulSoup


class BalanceException(Exception):
    pass


class LoginException(BalanceException):
    pass


class DownloadException(BalanceException):
    pass


def fetch_balance(username, password):
    s = requests.Session()
    s.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:54.0) Gecko/20100101 Firefox/54.0';
    s.headers['Referer'] = 'https://www.easym2m.eu/login.php'
    # s.get('http://httpbin.org/cookies/set/sessioncookie/123456789')
    # r = s.get('http://httpbin.org/cookies')
    # print(r.text)
    # '{"cookies": {"sessioncookie": "123456789"}}'

    s.get('https://www.easym2m.eu/login.php')

    fields = {
        'username': username,
        'data[User][username]': '',
        'password': password,
        'data[User][password]': '',
        'token': '',
    }

    res = s.post('https://www.easym2m.eu/inside_new/users/login', data=fields, allow_redirects=False)

    if 'Location' in res.headers:
        print(res.headers['Location'])
        if not res.headers['Location'].startswith('https://www.easym2m.eu/inside_new/mains/home_customers/'):
            raise LoginException()
    else:
        raise LoginException()

    user_id = res.headers['Location'].split('/')[-1]

    res = s.get('https://www.easym2m.eu/inside_new/invoices/my_balance/' + user_id)

    if res.status_code != 200:
        raise DownloadException()

    soup_mysite = BeautifulSoup(res.text, "html.parser")
    fields = [div.contents for div in soup_mysite.find_all("div", class_='number')]

    if len(fields) != 1:
        raise DownloadException()

    total_balance = float(fields[0][0].strip('\r\n €'))

    res = s.get('https://www.easym2m.eu/inside_new/simcards/my_simcards_search/' + user_id)
    soup_mysite = BeautifulSoup(res.text, "html.parser")
    tokens = [input.get('value') for input in soup_mysite.find_all("input") if input.get('id') == 'token']

    data = 'token=' + tokens[0] + '&idcustomer=' + user_id + '&pagesize=25&pageinit=1&iccid=&msisdn=&imsi=&alias=&imei=&commmodulefacturer=&commmodulemodel=&gprs_status=&status=_&product=_&labels=&actions='
    res = s.post('https://www.easym2m.eu/inside_new/simcards/simcards_paged_definitive', data=data,
                 headers={'Accept': 'application/json, text/javascript, */*; q=0.01',
                          'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})

    #print(res.json())  # [{'checkbox': '<div class="checker"><span><input type="checkbox"  class="checkboxes" id="checkXXX"></span></div>', 'msisdn': '<a href="https://www.easym2m.eu/inside_new/simcards/details_simcard/XXX">XX</a>', 'imsi': '<a href="https://www.easym2m.eu/inside_new/simcards/details_simcard/XX">XX</a>', 'iccid': '<a href="https://www.easym2m.eu/inside_new/simcards/details_simcard/XX">XX</a>', 'alias': '<a href="https://www.easym2m.eu/inside_new/simcards/details_simcard/XX">GPS Tracker</a>', 'imei': 'xxx', 'commmodulemanufacturer': 'xxxy Limited', 'commmodulemodel': 'xx', 'labels': 'No Labels', 'gprs_status': 'Yes', 'status': 'ACTIVE', 'product': '<a href="https://www.easym2m.eu/inside_new/customers/details_product/xxx/GPS_ES_PPU_EU">Pay per use (GPL 5)</a>', 'callsV': '<a href="https://www.easym2m.eu/inside_new/simcards/view_calls/xxx/08/2017/V">0</a>', 'callsM': '<a href="https://www.easym2m.eu/inside_new/simcards/view_calls/xxx/08/2017/M">0</a>', 'calls': '<a href="https://www.easym2m.eu/inside_new/simcards/view_calls/xx/08/2017/D">1.18 </a>', 'balance': '---'}, {'checkbox': '<div class="checker"><span><input type="checkbox"  class="checkboxes" id="checxxx"></span></div>', 'msisdn': '<a href="https://www.easym2m.eu/inside_new/simcards/details_simcard/xxx">xx</a>', 'imsi': '<a href="https://www.easym2m.eu/inside_new/simcards/details_simcard/xxx">xx</a>', 'iccid': '<a href="https://www.easym2m.eu/inside_new/simcards/details_simcard/xx">xx</a>', 'alias': '<a href="https://www.easym2m.eu/inside_new/simcards/details_simcard/xx">xx</a>', 'imei': None, 'commmodulemanufacturer': '', 'commmodulemodel': '', 'labels': 'No Labels', 'gprs_status': 'n/a', 'status': 'INACTIVE_NEW', 'product': '<a href="https://www.easym2m.eu/inside_new/customers/details_product/xx/GPS_ES_PPU_EU">Pay per use (GPL 5)</a>', 'callsV': '<a href="https://www.easym2m.eu/inside_new/simcards/view_calls/xxx/08/2017/V">0</a>', 'callsM': '<a href="https://www.easym2m.eu/inside_new/simcards/view_calls/xxx/08/2017/M">0</a>', 'calls': '<a href="https://www.easym2m.eu/inside_new/simcards/view_calls/xxx/08/2017/D">0 </a>', 'balance': '---'}]

    if res.status_code != 200:
        raise DownloadException()

    def create_sim_card(data):
        data['usage_data'] = data['calls']
        del data['calls']

        data['usage_voice'] = data['callsV']
        del data['callsV']

        data['usage_messages'] = data['callsM']
        del data['callsM']

        del data['checkbox']

        # remove html tags
        return {k: BeautifulSoup(v, "html.parser").text.strip() if v else ''
                for k,v in data.items()}
    sim_cards = list(map(create_sim_card, res.json()))

    for sim_card in sim_cards:
        res = s.get('https://www.easym2m.eu/inside_new/simcards/details_simcard/' + sim_card['iccid'])
        soup_mysite = BeautifulSoup(res.text, "html.parser")
        balance_str = soup_mysite.find("b", text='Balance: ').parent.text.replace('Balance: ', '').strip(' €\r\n')
        sim_card['balance'] = float(balance_str) if balance_str != '---' else -1.0

        sim_card['usage_data'] = float(sim_card['usage_data'])
        sim_card['usage_voice'] = float(sim_card['usage_voice'])
        sim_card['usage_messages'] = float(sim_card['usage_messages'])

    return {'total_balance': total_balance, 'sim_cards': sim_cards}
