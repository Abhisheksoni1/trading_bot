import requests
import json
import time
import base64
import hashlib
import hmac
import logging
from urllib3.request import urlencode
import os.path
import datetime
dir = os.path.dirname(os.path.abspath(__file__)) + '/'


class Ice3x(object):
    def __init__(self, key=None, secret=None, client_id=None, coins=None):
        self.logger = logging.getLogger('ICE3X')
        self.BASE_URL = 'https://ice3x.com/api/v1/'
        self.handler = logging.FileHandler(dir+'logs/ice3x.log')
        self.is_continuous = False
        self.key = key
        self.secret = secret
        self.client_id = client_id
        self.coins = coins
        self._init_logger()

    def _init_logger(self):
        self.logger.setLevel(logging.INFO)
        self.handler.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

    def _format_log(self, string, level):
        return '{} {}: {}'.format(level, datetime.datetime.now(), string)

    def min_ask_price_ice(self):
        min_ask_price_ice = {}
        currency_pair_id = {}
        response = requests.get(self.BASE_URL + 'stats/marketdepthbtcav').text
        result = json.loads(response)
        if result['errors'] == 'false' or result['errors'] == False:
            for data in result['response']['entities']:
                if str(data['pair_name']).split('/')[1] == 'zar' and str(data['pair_name']).split('/')[0] in self.coins:
                    min_ask_price_ice[str(data['pair_name']).split('/')[0]] = data['min_ask']
                    currency_pair_id[str(data['pair_name']).split('/')[0]] = data['pair_id']
            self.logger.info(self._format_log(response, 'INFO'))
            return min_ask_price_ice, currency_pair_id

    def place_order(self, pair_id, amount, type, price):
        nonce = str(int(time.time()) * 1e6)
        uri = 'order/new'
        post_data = {'nonce' : nonce,
                     'pair_id': pair_id,
                     'amount': amount,
                     'type': type,
                     'price': price
                     }
        str_to_sign = str(urlencode(post_data))
        signature = hmac.new(self.secret.encode('utf-8'), msg=str_to_sign.encode('utf-8'), digestmod=hashlib.sha512).hexdigest()
        headers = {'Key': self.key,
                   'Sign': signature}
        r = requests.post(self.BASE_URL + uri, data=post_data, headers=headers)
        response = json.loads(r.text)
        self.logger.info(self._format_log(response, 'INFO'))
        return response



