# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import json
import datetime
import logging
import threading
import time
import requests
import os.path
dir = os.path.dirname(os.path.abspath(__file__)) + "/"


class Bitstamp(object):
    ETH_ADDRESS = ""
    BTC_ADDRESS = ""
    LTC_ADDRESS = ""
    BTC_BALANCE = 10
    ETH_BALANCE = 100
    LTC_BALANCE = 0

    def __init__(self, key=None, secret=None, client_id=None, coins=None):
        # self.logger = logging.getLogger("BITSTAMP")
        self.BASE_URL = "https://www.bitstamp.net/api/v2/"
        # self.handler = logging.FileHandler(dir+'logs/bitstamp.log')
        self.is_continuous = False
        self.key = key
        self.secret = secret
        self.client_id = client_id
        # self._init_logger()
        self.coins = coins
        self.summary = None

    def max_bid_price_bitstamp(self):
        max_bid_price_bitstamp = {}
        price_bitstamp = {}
        for coin in self.coins:
            found = False
            while not found:
                try:
                    response = requests.get('https://www.bitstamp.net/api/v2/ticker/' + str(coin) + 'USD',
                                            headers={'User-Agent': 'Mozilla/5.0'}).text
                    response = json.loads(response)
                    max_bid_price_bitstamp[str(coin)] = response['bid']
                    price_bitstamp[str(coin)] = response['last']
                    found = True
                except Exception as e:
                    pass
        return max_bid_price_bitstamp, price_bitstamp

    # def _init_logger(self):
    #     self.logger.setLevel(logging.INFO)
    #     self.handler.setLevel(logging.INFO)
    #     self.logger.addHandler(self.handler)
    #
    # def _format_log(self, string, level):
    #     return "{} {}: {}".format(level, datetime.datetime.now(), string)

    def send_bets(self, **params):
        if self.key and self.secret:
            nonce = str(int(time.time() * 1e6))
            message = nonce + self.client_id + self.key
            signature = hmac.new(
                self.secret.encode('utf-8'), msg=message.encode('utf-8'), digestmod=hashlib.sha256)
            signature = signature.hexdigest().upper()
            params.update({
                'key': self.key, 'signature': signature, 'nonce': nonce
            })
            url = self.BASE_URL + params['side'] + "/" + params['coin'] + 'USD/'
            r = requests.post(url, data=params)
            response = r.json()
            #self.logger.info(self._format_log(response, "INFO"))
            return response
        else:
            return "KEY AND SECRET NEEDED FOR BETTING"

    def get_balance(self):
        url = "https://www.bitstamp.net/api/balance/"
        params = {}
        if self.key and self.secret:
            nonce = str(int(time.time() * 1e6))
            message = nonce + self.client_id + self.key
            signature = hmac.new(
                self.secret.encode('utf-8'), msg=message.encode('utf-8'), digestmod=hashlib.sha256)
            signature = signature.hexdigest().upper()
            params.update({
                'key': self.key, 'signature': signature, 'nonce': nonce
            })
            r = requests.post(url, data=params)
            response = r.json()
            # self.logger.info(self._format_log(response, "INFO"))
            if response.get("error", "") != "":
                print("Error while requesting {}".format(response['error']))
            elif isinstance(response, dict):
                if response.get("btc_available", "") != "":
                    self.BTC_BALANCE = response['btc_available']
                if response.get("eth_available", "") != "":
                    self.ETH_BALANCE = response['eth_available']
                if response.get('ltc_available', "") != "":
                    self.LTC_BALANCE = response['ltc_available']
            return response
        else:
            return "KEY AND SECRET NEEDED FOR BETTING"
