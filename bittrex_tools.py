#!/usr/bin/env python3.5

import json
from bittrex.bittrex import Bittrex
import time
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
            # order['completed']
            try:
                status['thresholded']
            except:
                print('initiating new tracking order...')
                status['thresholded'] = False
                status['buy_sell_signal'] = False
                status['order_completed'] = False
                status['new_threshold'] = 0.0
                status['last_value'] = 0.0

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
            if not market['active']:
                break
            live_market = self.bittrex.get_ticker(market['market'])['result']
            market['last_value'] = live_market['Last']

            if market['thresholded'] == "False":
                    if live_market['Last'] >= market['threshold'] and market['order'] == 'sell':
                        market['thresholded'] = True
                        market['new_threshold'] = live_market['Last']
                    if live_market['Last'] <= market['threshold'] and market['order'] == 'buy':
                        market['thresholded'] = True
                        market['new_threshold'] = live_market['Last']
            else:
                if market['order'] == 'sell':
                    if live_market['Last'] > market['new_threshold']:
                        market['new_threshold'] = live_market['Last']
                    elif float(live_market['Last']) <= (float(market['new_threshold']) * (1 - float(market['max_gap'])/100)):
                        market['buy_sell_signal'] = True
                elif market['order'] == 'buy':
                    if live_market['Last'] < market['new_threshold']:
                        market['new_threshold'] = live_market['Last']
                        # market['last'] = market_status['Last']
                    elif float(live_market['Last']) >= (float(market['new_threshold']) * (1 + float(market['max_gap'])/100.0)):
                        market['buy_sell_signal'] = True
        
        print(json.dumps(self.tracker_status))

        with open('tracker_status.csv', 'w') as f:
            writer = csv.DictWriter(f, tracker.tracker_status[0].keys(), delimiter=',')
            writer.writeheader()
            for market in self.tracker_status:
                writer.writerow(market)





class Bittrex_Handler():
    '''docu'''
    def __init__(self):
        with open("secrets.json") as secrets_file:
            self.secrets = json.load(secrets_file)
            secrets_file.close()
        self.bittrex = Bittrex(self.secrets['key'], self.secrets['secret'])
        self.balances = {}
        self.tracker_status = tracker_setting_
        for market in self.tracker_status:
            market['thresholded'] = False
            market['buy_sell_signal'] = False
            market['order_completed'] = False
            market['new_threshold'] = 0.0
            market['last'] = 0.0
            market['order_completed'] = False
        self.get_balances()


    def get_balances(self):
        ''' docu '''
        actual = self.bittrex.get_balances()
        self.balances = actual['result']
        for e in actual['result']:
            print(e['CryptoAddress'], '\t', e['Currency'], '\t', e['Balance'], '\t', e['Available'])


    def tracker(self, log_level=0):
        ''' docu'''
        for market in self.tracker_status:
            if not market['active']:
                break
            market_status = self.bittrex.get_ticker(market['ticker'])['result']
            market['last'] = market_status['Last']

            # print(market['ticker'], ':' , json.dumps(market_status))
            if not market['thresholded']:
                if market_status['Last'] >= market['threshold'] and market['order'] == 'sell':
                    market['thresholded'] = True
                    market['new_threshold'] = market_status['Last']
                if market_status['Last'] <= market['threshold'] and market['order'] == 'buy':
                    market['thresholded'] = True
                    market['new_threshold'] = market_status['Last']
            else:
                if market['order'] == 'sell':
                    if market_status['Last'] > market['new_threshold']:
                        market['new_threshold'] = market_status['Last']
                    elif market_status['Last'] <= (market['new_threshold'] * (1 - market['max_gap']/100)):
                        market['buy_sell_signal'] = True
                elif market['order'] == 'buy':
                    if market_status['Last'] < market['new_threshold']:
                        market['new_threshold'] = market_status['Last']
                        # market['last'] = market_status['Last']
                    elif market_status['Last'] >= (market['new_threshold'] * (1 + market['max_gap']/100)):
                        market['buy_sell_signal'] = True


    def sell_buy(self, log_level=0):
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
            


    def sell_limit(self, market, quantity, rate):
        """ docu here """
        result = self.bittrex.sell_limit(market, str(quantity), str(rate))
        print(json.dumps(result, indent=4))


# This should be placed in a file using a CSV table...
tracker_setting_ = [
    {
        'index': 1,
        'active': True,
        'order': 'sell',
        'ticker': 'USDT-ZEC',
        'threshold': 300,
        'max_gap': 3,
        'quantity': 0.1
    },{
        'index': 2,
        'active': True,
        'order': 'buy',
        'ticker': 'USDT-ZEC',
        'threshold': 270,
        'max_gap': 3,
        'quantity': 0.2
    }, {
        'index': 3,
        'active': True,
        'order': 'sell',
        'ticker': 'USDT-BTC',
        'threshold': 4380,
        'max_gap': 3,
        'quantity': 0.1
    }, {
        'index': 4,
        'active': True,
        'order': 'buy',
        'ticker': 'USDT-BTC',
        'threshold': 3000,
        'max_gap': 3,
        'quantity': 0.01
    }
]

if __name__ == '__main__':
    
    while True:
        tracker = Tracker()
        tracker.track()

        time.sleep(2)
        del tracker




# if __name__ == '__main__':
#     bittrex_handler = Bittrex_Handler()

#     # print(json.dumps(bittrex_handler.tracker_status, indent=4))

#     # bittrex_handler.sell_limit('USDT-ZEC', 0.1, 500.0)

#     while True:
#         tracker_setting = []
#         with open('tracker_settings.csv') as f:
#             reader = csv.DictReader(f)
#             for row in reader:
#                 tracker_setting.append(row)
#             print(tracker_setting)

#         bittrex_handler.tracker()
#         print(json.dumps(bittrex_handler.tracker_status, indent=4))
#         bittrex_handler.sell_buy()

#         with open('tracker_status.csv', 'w') as f:

#             writer = csv.DictWriter(f, bittrex_handler.tracker_status[0].keys(), delimiter=',')
#             writer.writeheader()

#             for market in bittrex_handler.tracker_status:
#                 writer.writerow(market)

#         time.sleep(10)
