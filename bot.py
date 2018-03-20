from ice3x import Ice3x
import requests
import json
from bitstamp import Bitstamp
import email.mime.application
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email
import smtplib
import datetime
import csv
import time
from settings import *

CURRENCIES = ['BTC', 'LTC', 'ETH', 'BCH']

EMAIL_HEADING = ('coin', 'date', 'min_ask_price_ice', 'max_bid_price_bitstamp', 'coin_amount', 'fund_buy_usd',
                 'fund_sell_usd', 'variance')

FILE_HEADING = ('coin', 'date', 'min_ask_price_ice', 'max_bid_price_bitstamp', 'coin_amount', 'fund_buy_usd',
                'fund_sell_usd', 'variance', 'currency_pair_id', 'price_bitstamp', 'min_ask_price_usd',
                'max_bid_amount', 'coin_amount', 'response_buy', 'fund_buy_usd', 'ice_order_id', 'ice_transaction_id',
                'response_sell', 'fund_sell_usd', 'bitstamp_order_id')


def currency_exchange_rate():
    res = requests.get('https://forex.1forge.com/1.0.3/quotes?pairs=ZARUSD&api_key=THMvdfzLLoxEa3GVIb2mKBhvD8vaP3Mx')
    return (json.loads(res.text)[0])['price']


def currency_conversion(rate, price_zar):
    for coin in CURRENCIES:
        price_zar[coin] = float(price_zar[coin]) * float(rate)
    return price_zar


def createHTMLtable(table_heading, heading, data):
    htmltable = '<table border="1"><caption><b><u><font size=3>' + str(table_heading) + '</font></b></u></caption>'
    # Append Table Heading
    text = '<tr style = "background-color:rgb(221, 136, 151)">'
    for i in heading:
        text = text + '<th>' + str(i) + '</th>'
    text = text + '</tr>'
    # Append Table Data
    for row in data:
        text = text + '<tr>'
        for h in heading:
            text = text + '<td>' + str(row[h]) + '</td>'
        text = text + '</tr>'
    htmltable = htmltable + text + '</table>'
    return htmltable


def sendEmail(email_sub, email_body_text, email_body, email_text_end, attachments=[]):
    msg = MIMEMultipart()
    msg['Subject'] = email_sub
    msg['From'] = EMAIL_FROM
    msg['To'] = ','.join(EMAIL_TO)
    msg['Cc'] = ','.join(EMAIL_CC)

    body = MIMEText(email_body_text)
    msg.attach(body)
    for i in email_body:
        body = MIMEText(i, 'html')
        msg.attach(body)
        body = MIMEText('\n')
        msg.attach(body)

    body = MIMEText(email_text_end)
    msg.attach(body)
    for row in attachments:
        fp = open(row, 'rb')
        att = email.mime.application.MIMEApplication(fp.read(), _subtype="csv")
        fp.close()
        att.add_header('Content-Disposition', 'attachment', filename='fullreport.csv')
        msg.attach(att)

    s = smtplib.SMTP('smtp.gmail.com')
    s.starttls()
    s.login(EMAIL_FROM, EMAIL_PASSWORD)

    FROM = EMAIL_FROM
    TO = EMAIL_TO
    CC = EMAIL_CC
    s.sendmail(FROM, TO + CC, msg.as_string())
    s.quit()


def variance(val1, val2):
    val1 = float(val1)
    val2 = float(val2)
    mean = (val1 + val2) / 2
    val1_sqr = (val1 - mean) ** 2
    val2_sqr = (val2 - mean) ** 2
    variance = val1_sqr + val2_sqr
    return variance


def strategy(coin, coin_data, bitstamp, ice):
    error_msg = ''
    coin_data['variance'] = variance(coin_data['min_ask_price_usd'], coin_data['max_bid_price_bitstamp'])
    coin_data['date'] = datetime.datetime.now()
    if coin_data['variance'] > -2:
        wallet_Amount = float(bitstamp.get_balance(coin_data['coin']))

        if wallet_Amount * float(coin_data['price_bitstamp']) > 30:
            MaxBidAmount = float(bitstamp.max_bid_amount(coin_data['coin']))
            coin_data['max_bid_amount'] = MaxBidAmount

            if MaxBidAmount > wallet_Amount:
                CoinAmount = wallet_Amount
            else:
                CoinAmount = MaxBidAmount
            coin_data['coin_amount'] = CoinAmount
            response_buy = ice.place_order(amount=CoinAmount, price=coin_data['min_ask_price_ice'], type='buy',
                                           pair_id=coin_data['currency_pair_id'])
            coin_data['response_buy'] = response_buy
            if response_buy['errors'] == 'false':
                fund_buy_usd = CoinAmount * coin_data['min_ask_price_usd']
                coin_data['fund_buy_usd'] = fund_buy_usd
                coin_data['ice_order_id'] = response_buy['response']['entity']['order_id']
                coin_data['ice_transaction_id'] = response_buy['response']['entity']['transaction_id']

                response_sell = bitstamp.send_bets(amount=CoinAmount, price=coin_data['max_bid_price_bitstamp'],
                                                   coin=coin_data['coin'], side='sell')
                coin_data['response_sell'] = response_sell
                if response_sell['status'] == 'success':
                    fund_sell_usd = CoinAmount * float(coin_data['max_bid_price_bitstamp'])
                    coin_data['fund_sell_usd'] = fund_sell_usd
                    coin_data['bitstamp_order_id'] = response_sell['id']

                else:
                    error_msg = error_msg + 'Unable to place sell order on BITSTAMP. ' + response_sell['reason']
            else:
                error_msg = error_msg + 'Unable to place buy order on ICE. ' + response_buy['error']
        else:
            error_msg = error_msg + 'Wallet amount is less than $30'
    else:
        error_msg = error_msg + 'variance is less than 2. '
    coin_data['error_msg'] = error_msg
    return coin_data


def summary_into_file(bot_summary):
    record_fl = open('trade_record.csv', 'a')
    file_writer = csv.writer(record_fl, delimiter=',', quotechar='', quoting=csv.QUOTE_ALL)
    for coin in bot_summary:
        row = []
        for heading in FILE_HEADING:
            row.append(coin.get(heading, '-'))
        file_writer.writerow(row)
    record_fl.close()


def main():
    bot_summary = []
    email_summary = []
    ice = Ice3x(key=Ice_key, secret=Ice_secret, coins=CURRENCIES)

    bitstamp = Bitstamp(key=Bitstamp_key, secret=Bitstamp_secret, client_id=Bitstamp_client_id, coins=CURRENCIES)

    min_ask_price_ice, currency_pair_id = ice.min_ask_price_ice()
    max_bid_price_bitstamp, price_bitstamp = bitstamp.max_bid_price_bitstamp()

    htmlcontent = []

    exchange_rate = currency_exchange_rate()
    min_ask_price_usd = currency_conversion(exchange_rate, min_ask_price_ice)

    for coin in CURRENCIES:
        coin_data = {'coin': coin, 'min_ask_price_ice': min_ask_price_ice[coin],
                     'max_bid_price_bitstamp': max_bid_price_bitstamp[coin],
                     'currency_pair_id': currency_pair_id[coin], 'price_bitstamp': price_bitstamp[coin],
                     'min_ask_price_usd': min_ask_price_usd[coin]}
        coin_summary = strategy(coin, coin_data, bitstamp, ice)
        bot_summary.append(coin_summary)

        if coin_summary['error_msg'] == '':
            email_summary.append(coin_summary)

    if len(email_summary) > 0:
        htmlcontent.append(createHTMLtable('Audit Report Reviewed Order', EMAIL_HEADING, email_summary))
        email_sub = 'Trading Bot Report'
        email_body_text = 'Hi All,\n\nPFB the summary of orders:'
        email_body = htmlcontent
        email_text_end = '\n\nRegards\nTrading Bot'
        sendEmail(email_sub, email_body_text, email_body, email_text_end, [])
    summary_into_file(bot_summary)


main()
