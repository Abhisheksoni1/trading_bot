import requests
import json
import time
import base64
import hashlib
import hmac


class Ice3x(object):
    ETH_ADDRESS = ""
    BTC_ADDRESS = ""
    LTC_ADDRESS = ""
    BTC_BALANCE = 10
    ETH_BALANCE = 100
    LTC_BALANCE = 0

    def __init__(self, key=None, secret=None, client_id=None, coins=None):
        # self.logger = logging.getLogger("BITSTAMP")
        self.BASE_URL = "https://ice3x.com/api/v1/"
        # self.handler = logging.FileHandler(dir + 'logs/bitstamp.log')
        self.is_continuous = False
        self.key = key
        self.secret = secret
        self.client_id = client_id
        self.coins = coins
        # self._init_logger()
        self.currency_pair = 'ethbtc'
        self.summary = None

    def min_ask_price_ice(self):
        min_ask_price_ice = {}
        currency_pair_id = {}
        response = requests.get(self.BASE_URL + 'stats/marketdepthbtcav').text
        print(response)
        result = json.loads(response)
        if result['errors'] == 'false' or result['errors'] == False:
            for data in result['response']['entities']:
                if str(data['pair_name']).split('/')[1] == 'zar' and str(data['pair_name']).split('/')[0] in self.coins:
                    min_ask_price_ice[str(data['pair_name']).split('/')[0]] = data['min_ask']
                    currency_pair_id[str(data['pair_name']).split('/')[0]] = data['pair_id']
            return min_ask_price_ice, currency_pair_id

    def place_order(self, pair_id, amount, type, price):
        nonce = str(int(time.time()) * 1e6)
        uri = 'order/create'
        post_data = {'nonce': nonce,
                     'pair_id': pair_id,
                     'amount': amount,
                     'type': type,
                     'price': price
                     }
        str_to_sign = uri + '\n' + nonce + '\n' + str(post_data)
        signature = hmac.new(self.secret.encode('utf-8'), msg=str_to_sign.encode('utf-8'), digestmod=hashlib.sha256)
        headers = {"Accept": "application/json",
                   "Accept-Charset": "UTF-8",
                   "Content-Type": "application/json",
                   "Key": self.key,
                   "timestamp": nonce,
                   "Sign": signature}
        r = requests.post(self.BASE_URL + uri, data=post_data)
        print(r.text)
        response = r.json()
        print(response)

