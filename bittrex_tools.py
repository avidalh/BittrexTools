#!/usr/bin/env python3.5

import json
from bittrex.bittrex import Bittrex
import time
import datetime
import csv


class Tracker():
    '''docu'''
    def __init__(self):
        with open("secrets.json") as secrets_file:
            self.secrets = json.load(secrets_file)
            secrets_file.close()
        self.bittrex = Bittrex(self.secrets['key'], self.secrets['secret'])

        self.tracker_setting = []
        with open('tracker_settings.csv') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.tracker_setting.append(row)
            print(self.tracker_setting)

        self.tracker_status = []
        with open('tracker_status.csv') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.tracker_status.append(row)
            print(self.tracker_status)

        # check if exist new orders:
        while not len(self.tracker_status) == len(self.tracker_setting):
            print('not equal!')
            self.tracker_status.append({})
        print(self.tracker_status)

        # update tracking orders:
        for order, status in zip(self.tracker_setting, self.tracker_status):
            status['id'] = order['id']
            status['market'] = order['market']
            status['order'] = order['order']
            status['quantity'] = order['quantity']
            status['threshold'] = order['threshold']
            status['max_gap'] = order['max_gap']
            status['active'] = order['active']
            if len(status) == 7:
                print('initiating new tracking order...')
                status['thresholded'] = 'False'
                status['buy_sell_signal'] = 'False'
                status['order_completed'] = 'False'
                status['new_threshold'] = 0.0
                status['last_value'] = 0.0
                status['TimeStamp'] = str(datetime.datetime.now())
            else:
                # if in any order was changed its threshold levels during a run:
                if status['order'] == 'sell':
                    if float(status['new_threshold']) < float(order['threshold']):
                        status['thresholded'] = 'False'
                elif status['order'] == 'sell':
                    if float(status['new_threshold']) > float(order['threshold']):
                        status['thresholded'] = 'False'

        # write status to file
        with open('tracker_status.csv', 'w') as f:
            writer = csv.DictWriter(f, self.tracker_status[0].keys(), delimiter=',')
            writer.writeheader()
            for market in self.tracker_status:
                writer.writerow(market)

        print(json.dumps(self.tracker_status, indent=4))

    def track(self):
        ''' docu '''
        for market in self.tracker_status:
            if market['active'] == 'False':
                break
            live_market = self.bittrex.get_ticker(market['market'])['result']
            market['last_value'] = live_market['Last']
            market['TimeStamp'] = str(datetime.datetime.now())

            if market['thresholded'] == 'False':
                if market['order'] == 'sell':
                    if float(live_market['Last']) >= float(market['threshold']):
                        market['thresholded'] = 'True'
                        market['new_threshold'] = live_market['Last']
                if market['order'] == 'buy':
                    if float(live_market['Last']) <= float(market['threshold']):
                        market['thresholded'] = 'True'
                        market['new_threshold'] = live_market['Last']
            else:
                if market['order'] == 'sell':
                    if float(live_market['Last']) > float(market['new_threshold']):
                        market['new_threshold'] = live_market['Last']
                    elif float(live_market['Last']) <= (float(market['new_threshold']) * (1 - float(market['max_gap'])/100)):
                        market['buy_sell_signal'] = 'True'
                elif market['order'] == 'buy':
                    if float(live_market['Last']) < float(market['new_threshold']):
                        market['new_threshold'] = live_market['Last']
                        # market['last'] = market_status['Last']
                    elif float(live_market['Last']) >= (float(market['new_threshold']) * (1 + float(market['max_gap'])/100.0)):
                        market['buy_sell_signal'] = 'True'
        
        print(json.dumps(self.tracker_status))

        with open('tracker_status.csv', 'w') as f:
            writer = csv.DictWriter(f, tracker.tracker_status[0].keys(), delimiter=',')
            writer.writeheader()
            for market in self.tracker_status:
                writer.writerow(market)

    def sell_buy(self):
        ''' insert docu '''
        for market in self.tracker_status:
            if not market['active']:
                break
            if market['order_completed']:
                break
            if market['buy_sell_signal'] and market['order'] == 'sell':
                print('selling...')
                result = self.bittrex.sell_limit(market=market['ticker'], quantity=market['quantity'], rate=float(market['last']))
                print(json.dumps(result, indent=4))
                if result['success']:
                    market['order_completed'] = True
                    market['active'] = False
            
            elif market['buy_sell_signal'] and market['order'] == 'buy':
                print('buying...')
                result = self.bittrex.buy_limit(market=market['ticker'], quantity=market['quantity'], rate=float(market['last']))
                print(json.dumps(result, indent=4))
                if result['success']:
                    print('Order completed!')
                    market['order_completed'] = True
                    market['active'] = False


if __name__ == '__main__':
    
    while True:
        tracker = Tracker()
        tracker.track()

        time.sleep(15)
        del tracker
