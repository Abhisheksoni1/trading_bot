# -*- coding: utf-8 -*-
import hashlib
import hmac
import json
import datetime
import logging
import threading
import time
import datetime
import calendar
import requests
import os.path
dir = os.path.dirname(os.path.abspath(__file__)) + "/"


class Bitstamp(object):
    def __init__(self, key=None, secret=None, client_id=None, coins=None):
        self.logger = logging.getLogger("BITSTAMP")
        self.BASE_URL = "https://www.bitstamp.net/api/v2/"
        self.handler = logging.FileHandler(dir+'logs/bitstamp.log')
        self.is_continuous = False
        self.key = key
        self.secret = secret
        self.client_id = client_id
        self._init_logger()
        self.coins = coins

    def _init_logger(self):
        self.logger.setLevel(logging.INFO)
        self.handler.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

    def _format_log(self, string, level):
        return "{} {}: {}".format(level, datetime.datetime.now(), string)

    def max_bid_price_bitstamp(self):
        max_bid_price_bitstamp = {}
        price_bitstamp = {}
        response_log = ''
        for coin in self.coins:
            found = False
            while not found:
                try:
                    response = requests.get(self.BASE_URL + 'ticker/' + str(coin) + 'USD',
                                            headers={'User-Agent': 'Mozilla/5.0'}).text
                    response = json.loads(response)
                    max_bid_price_bitstamp[str(coin)] = response['bid']
                    price_bitstamp[str(coin)] = response['last']
                    found = True
                    response_log = response_log + response
                except Exception as e:
                    pass
        self.logger.info(self._format_log(response_log, "INFO"))
        return max_bid_price_bitstamp, price_bitstamp

    def max_bid_amount(self, coin):
        response = requests.get(self.BASE_URL + 'order_book/' + str(coin).lower() + 'usd/')
        response = json.loads(response.text)['bids']
        MaxBidAmount = response[0][1]
        for data in response:
            if data[1] > MaxBidAmount:
                MaxBidAmount = data[1]
        self.logger.info(self._format_log(response, "INFO"))
        return MaxBidAmount

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
            url = self.BASE_URL + params['side'] + "/" + params['coin'] + 'usd/'
            r = requests.post(url, data=params)
            response = json.loads(r.text)
            self.logger.info(self._format_log(response, "INFO"))
            return response
        else:
            return "KEY AND SECRET NEEDED FOR BETTING"

    def get_balance(self, coin):
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
            url = self.BASE_URL + 'balance/' + coin + 'usd/'
            r = requests.post(url=url, data=params)
            response = json.loads(r.text)
            balance_key = coin + '_available'
            balance = response[balance_key]
            self.logger.info(self._format_log(response, "INFO"))
            return balance
        else:
            return "KEY AND SECRET NEEDED FOR BETTING"


