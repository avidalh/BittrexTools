#!/usr/bin/env python3.5

import json
from bittrex.bittrex import Bittrex
import time
import datetime
import csv

from logging.handlers import RotatingFileHandler
import logging


# TODO's:
# Check balances prior order selling or buying to avoid errors in thq quantities
# 

# settings for the logger tool/utility
# log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
log_formatter = logging.Formatter('%(asctime)s %(message)s')
log_formatter.converter = time.gmtime
logFile = 'tracker.log'

my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024**2,
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)

app_log = logging.getLogger('root')
app_log.setLevel(logging.INFO)
app_log.addHandler(my_handler)


class Tracker():
    '''docu'''
    def __init__(self):
        app_log.info('class constructor entry point...')
        app_log.info('loading secrets...')
        with open("secrets.json") as secrets_file:
            self.secrets = json.load(secrets_file)
            secrets_file.close()
        self.bittrex = Bittrex(self.secrets['key'], self.secrets['secret'])

        app_log.info('fetching avaliable balances...')
        self.balances = []
        self.get_balances()
        app_log.info(json.dumps(self.balances, indent=4))

        self.tracker_setting = []
        app_log.info('loading tracker settings...')
        with open('tracker_settings.csv') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.tracker_setting.append(row)
        app_log.info(json.dumps(self.tracker_setting, indent=4))

        self.tracker_status = []
        app_log.info('loading tracker status...')
        with open('tracker_status.csv') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.tracker_status.append(row)
        app_log.info(json.dumps(self.tracker_status, indent=4))

        # check if exist new orders:
        while not len(self.tracker_status) == len(self.tracker_setting):
            app_log.info('adding new elements to tracker...')
            self.tracker_status.append({})
        # app_log.info(json.dumps(self.tracker_status. indent=4))

        # update tracking orders:
        app_log.info('updating tracking orders...')
        for order, status in zip(self.tracker_setting, self.tracker_status):
            status['id'] = order['id']
            status['market'] = order['market']
            status['order'] = order['order']
            status['quantity'] = order['quantity']
            status['threshold'] = order['threshold']
            status['max_gap'] = order['max_gap']
            status['active'] = order['active']
            if len(status) == 7:
                app_log.info('initiating new tracking order...')
                status['thresholded'] = 'False'
                status['buy_sell_signal'] = 'False'
                status['order_completed'] = 'False'
                status['new_threshold'] = 0.0
                status['last_value'] = 0.0
                status['TimeStamp'] = str(datetime.datetime.now())
            else:
                # if in any order was changed its threshold levels during a run:
                if status['order'] == 'sell':
                    if float(status['new_threshold']) < float(order['threshold']) and status['thresholded'] == 'True':
                        app_log.info('updating threshold value for {} to {}'.format(status['market'], order['threshold']))
                        status['new_threshold'] = order['threshold']
                        # status['thresholded'] = 'False'
                elif status['order'] == 'buy':
                    if float(status['new_threshold']) > float(order['threshold']) and status['thresholded'] == 'True':
                        app_log.info('updating threshold value for {} to {}'.format(status['market'], order['threshold']))
                        status['new_threshold'] = order['threshold']
                        # status['thresholded'] = 'False'

        app_log.info(json.dumps(self.tracker_status, indent=4))

        # write status to file
        with open('tracker_status.csv', 'w') as f:
            app_log.info('saving tracker status to file...')
            writer = csv.DictWriter(f, self.tracker_status[0].keys(), delimiter=',')
            writer.writeheader()
            for market in self.tracker_status:
                writer.writerow(market)

        # app_log.info(json.dumps(self.tracker_status, indent=4))


    def get_balances(self):
        ''' docu '''
        actual = self.bittrex.get_balances()
        self.balances = actual['result']
        # for e in actual['result']:
        #     print(e['CryptoAddress'], '\t', e['Currency'], '\t', e['Balance'], '\t', e['Available'])
 

    def track(self):
        ''' docu '''
        app_log.info('track method entry point...')
        for market in self.tracker_status:
            if market['active'] == 'False':
                break
            app_log.info('fetch market live data...')
            live_market = self.bittrex.get_ticker(market['market'])['result']
            market['last_value'] = live_market['Last']
            market['TimeStamp'] = str(datetime.datetime.now())
            app_log.info(json.dumps(live_market, indent=None))
            if market['thresholded'] == 'False':
                if market['order'] == 'sell':
                    if float(live_market['Last']) >= float(market['threshold']):
                        app_log.info('market gets thresholded at {}...'.format(live_market['Last']))
                        market['thresholded'] = 'True'
                        market['new_threshold'] = live_market['Last']
                if market['order'] == 'buy':
                    if float(live_market['Last']) <= float(market['threshold']):
                        app_log.info('market gets thresholded at {}...'.format(live_market['Last']))
                        market['thresholded'] = 'True'
                        market['new_threshold'] = live_market['Last']
            else:
                if market['order'] == 'sell':
                    if float(live_market['Last']) > float(market['new_threshold']):
                        app_log.info('updating threshold level to {}...'.format(live_market['Last']))
                        market['new_threshold'] = live_market['Last']
                    elif float(live_market['Last']) <= (float(market['new_threshold']) * (1 - float(market['max_gap'])/100)):
                        app_log.info('selling signal activated at {}...'.format(live_market['Last']))
                        market['buy_sell_signal'] = 'True'
                elif market['order'] == 'buy':
                    if float(live_market['Last']) < float(market['new_threshold']):
                        app_log.info('updating threshold level to {}...'.format(live_market['Last']))
                        market['new_threshold'] = live_market['Last']
                        # market['last'] = market_status['Last']
                    elif float(live_market['Last']) >= (float(market['new_threshold']) * (1 + float(market['max_gap'])/100.0)):
                        app_log.info('selling signal activated at {}...'.format(live_market['Last']))
                        market['buy_sell_signal'] = 'True'
        
        app_log.info('saving status to file...')
        with open('tracker_status.csv', 'w') as f:
            writer = csv.DictWriter(f, tracker.tracker_status[0].keys(), delimiter=',')
            writer.writeheader()
            for market in self.tracker_status:
                writer.writerow(market)

    def sell_buy(self):
        ''' insert docu '''
        app_log.info('sell_buy entry point...')
        for market in self.tracker_status:
            if market['active'] == 'False':
                break
            if market['order_completed'] == 'True':
                break
            if market['buy_sell_signal'] and market['order'] == 'sell':
                app_log.info('selling {} at {}'.format(market['ticker'], market['last']))
                result = self.bittrex.sell_limit(market=market['ticker'], quantity=market['quantity'], rate=float(market['last']))
                # print(json.dumps(result, indent=4))
                if result['success']:
                    market['order_completed'] = 'True'
                    market['active'] = 'False'
            
            elif market['buy_sell_signal'] and market['order'] == 'buy':
                app_log.info('buying {} at {}'.format(market['ticker'], market['last']))
                result = self.bittrex.buy_limit(market=market['ticker'], quantity=market['quantity'], rate=float(market['last']))
                # print(json.dumps(result, indent=4))
                if result['success']:
                    app_log.info('order completed...')
                    market['order_completed'] = 'True'
                    market['active'] = 'False'


if __name__ == '__main__':  
    while True:
        tracker = Tracker()
        tracker.track()

        time.sleep(60)
        del tracker
