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


CURRENCIES = ['BTC', 'LTC', 'ETH', 'BCH', 'XRP']


def currency_exchange_rate():
    res = requests.get('https://forex.1forge.com/1.0.3/quotes?pairs=ZARUSD&api_key=THMvdfzLLoxEa3GVIb2mKBhvD8vaP3Mx')
    return (json.loads(res.text)[0])['price']


def currency_conversion(rate, price_zar):
    for coin in CURRENCIES:
        price_zar[coin] = price_zar[coin] * rate
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
        for y in row:
            text = text + '<td>' + str(y) + '</td>'
        text = text + '</tr>'
    htmltable = htmltable + text + '</table>'
    return htmltable


def sendEmail(email_sub, email_body_text, email_body, email_text_end, email_to, email_cc, attachments=[]):
    # print 'in function'
    msg = MIMEMultipart()
    msg['Subject'] = email_sub
    msg['From'] = '30ankitbansal@gmail.com'
    msg['To'] = ','.join(email_to)
    msg['Cc'] = ','.join(email_cc)

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
    s.login('30ankitbansal@gmail.com', '@nkitone97')

    FROM = '30ankitbansal@gmail.com'
    TO = email_to
    CC = email_cc
    s.sendmail(FROM, TO + CC, msg.as_string())
    s.quit()


def variance(val1, val2):
    mean = (val1 + val2)/2
    val1_sqr = (val1 - mean)**2
    val2_sqr = (val2 - mean)**2
    variance = val1_sqr + val2_sqr
    return variance


def main():
    ice = Ice3x(key='IYBV1EGYESOGEHACTSKQ0ERQIMEJ0DQBGEDPCTTSARDLWNRIEFVVFLOO5TDGAXHY',
                secret='cyv4pnqqxvqhdp6minydzjpsdgcnlxuieckgi8pilkfnuxgsbuk89lbwq6s1alpe', coins=CURRENCIES)

    bitstamp = Bitstamp(key='WtoXTeix4LBUQkJAkeilYowmMUbfVK4r', secret='lPu2EMyoV7gpKsuy1fRnxT1sAkfJVSS',
                        client_id='gugo5564', coins=CURRENCIES)

    min_ask_price_ice, currency_pair_id = ice.min_ask_price_ice()
    max_bid_price_bitstamp, price_bitstamp = bitstamp.max_bid_price_bitstamp()

    htmlcontent = []
    heading = ('coin', 'date min_ask_price_ice', 'max_bid_price_bitstamp', 'coin_amount', 'fund_buy_usd',
               'fund_sell_usd', 'variance')
    summary = []
    record_fl = open('trade_record', 'a')
    file_writer = csv.writer(record_fl, delimiter=',', quotechar='|', quoting=csv.QUOTE_ALL)

    print(max_bid_price_bitstamp)
    print(price_bitstamp)
    exchange_rate = currency_exchange_rate()
    print(exchange_rate)
    min_ask_price_usd = currency_conversion(exchange_rate, min_ask_price_ice)

    for coin in CURRENCIES:
        summary_coin = []
        variance_coin = variance(min_ask_price_usd[coin], max_bid_price_bitstamp[coin])

        if variance_coin > -2:
            wallet_Amount = bitstamp.get_balance('BTC')

            if wallet_Amount * price_bitstamp[coin] > 30:
                MaxBidAmount = XXX    ########## amount of coin to buy and sell yet to be calculated

                if MaxBidAmount > wallet_Amount:
                    CoinAmount = wallet_Amount
                else:
                    CoinAmount = MaxBidAmount
                response_buy = ice.place_order(amount=CoinAmount, price=min_ask_price_ice[coin], type='buy',
                                           pair_id=currency_pair_id[coin])
                if response_buy['status'] == 'success':
                    fund_buy_usd = CoinAmount * min_ask_price_usd[coin]
                    response_sell = bitstamp.send_bets(amount=CoinAmount, price=max_bid_price_bitstamp[coin], coin=coin,
                                                       side='sell')
                    if response_sell['status'] == 'success':
                        fund_sell_usd = CoinAmount * max_bid_price_bitstamp[coin]

                        summary_coin = (coin, datetime.datetime.now(), min_ask_price_ice[coin], max_bid_price_bitstamp[coin],
                                        CoinAmount, fund_buy_usd, fund_sell_usd, variance_coin)
                        summary.append(summary_coin)
                        file_writer.writerow(summary_coin)
            else:
                message = 'Wallet amount is less than $30'

    htmlcontent.append(createHTMLtable('Audit Report Reviewed Order', heading, summary))
    email_sub = 'Audit Report Reviewed Order'
    email_body_text = 'Hi All,\n\nPFB the audit summary of reviewed orders:'
    email_to = ['rachit.mehra@paytm.com', 'mohit.singh@paytm.com']
    email_cc = ['sumit@paytm.com', 'ankit1.bansal@paytm.com', 'hitesh.goyal@paytm.com',
                'nikita.kindra@paytm.com']
    # email_to = ['ankit1.bansal@paytm.com']
    # email_cc = ['nikita.kindra@paytm.com', 'hitesh.goyal@paytm.com']
    email_body = htmlcontent
    email_text_end = '\n\nRegards\nKingCobraTeam'
    sendEmail(email_sub, email_body_text, email_body, email_text_end, email_to, email_cc)
    record_fl.close()


# main()

sendEmail('test', 'test', [], 'regards', ['30ankitbansal@gmail.com'], [''])
