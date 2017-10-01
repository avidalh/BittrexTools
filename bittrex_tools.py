#!/usr/bin/env python3.5

import json
from bittrex.bittrex import Bittrex
import time


class Bittrex_Handler():
    '''docu'''
    def __init__(self):
        with open("secrets.json") as secrets_file:
            self.secrets = json.load(secrets_file)
            secrets_file.close()
        self.bittrex = Bittrex(self.secrets['key'], self.secrets['secret'])
        self.balances = {}
        self.tracker_status = tracker_setting
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
tracker_setting = [
    {
        'active': True,
        'order': 'sell',
        'ticker': 'USDT-ZEC',
        'threshold': 300,
        'max_gap': 3,
        'quantity': 0.1
    },{
        'active': True,
        'order': 'buy',
        'ticker': 'USDT-ZEC',
        'threshold': 270,
        'max_gap': 3,
        'quantity': 0.2
    }, {
        'active': True,
        'order': 'sell',
        'ticker': 'USDT-BTC',
        'threshold': 4380,
        'max_gap': 3,
        'quantity': 0.1
    }, {
        'active': True,
        'order': 'buy',
        'ticker': 'USDT-BTC',
        'threshold': 3000,
        'max_gap': 3,
        'quantity': 0.01
    }
]


if __name__ == '__main__':
    bittrex_handler = Bittrex_Handler()

    print(json.dumps(bittrex_handler.tracker_status, indent=4))

    # bittrex_handler.sell_limit('USDT-ZEC', 0.1, 500.0)

    while True:

        bittrex_handler.tracker()
        print(json.dumps(bittrex_handler.tracker_status, indent=4))
        bittrex_handler.sell_buy()

        time.sleep(10)
