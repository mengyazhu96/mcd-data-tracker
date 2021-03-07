from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
import requests

from db import DBClient


METRIC_PRICE = 'price'
METRIC_VOLUME = 'volume'
METRIC_TYPES = (
    METRIC_PRICE,
    METRIC_VOLUME,
)


class DataFetcher:
    def __init__(self, db_client: DBClient, requests_client):
        self.db_client = db_client
        self.requests_client = requests_client
        self.pairs = {}  # pair symbols to {'base': base, 'quote': quote}

    def update_data(self):
        response_24h_summary = self.get_24h_summary()
        self.process_24h_summary(response_24h_summary)

    def update_pairs(self):
        pairs = self.requests_client.get('https://api.cryptowat.ch/pairs').json()['result']
        for pair in pairs:
            if pair['symbol'] not in self.pairs:
                self.pairs[pair['symbol']] = {
                    'base': pair['base']['symbol'],
                    'quote': pair['quote']['symbol'],
                }

    def get_24h_summary(self):
        result = self.requests_client.get(
            'https://api.cryptowat.ch/markets/summaries'
        ).json()
        if 'allowance' in result:
            print(result['allowance'])
        return result['result']

    def process_24h_summary(self, response_24h_summary):
        volumes = defaultdict(list)
        prices = defaultdict(list)
        fetch_timestamp = datetime.utcnow().isoformat()
        for symbol, summary_24h in response_24h_summary.items():
            _, pair_symbol = symbol.split(':')
            if pair_symbol not in self.pairs:
                self.update_pairs()

            base_symbol = self.pairs[pair_symbol]['base']
            quote_symbol = self.pairs[pair_symbol]['quote']
            try:
                base_volume = float(summary_24h['volume'])
                quote_volume = float(summary_24h['volumeQuote'])
                price = float(summary_24h['price']['last'])
            except ValueError as e:
                print(e)
                print(symbol)

            volumes[base_symbol].append(base_volume)
            volumes[quote_symbol].append(quote_volume)
            prices[pair_symbol].append(price)
        self.db_client.insert_many_metric_history(
            self.get_volume_insert_rows(volumes, fetch_timestamp)
            + self.get_price_insert_rows(prices, fetch_timestamp)
        )

    def get_volume_insert_rows(self, volumes, fetch_timestamp):
        return [
            (METRIC_VOLUME, symbol, np.sum(symbol_volumes), fetch_timestamp)
            for symbol, symbol_volumes in volumes.items()
        ]

    def get_price_insert_rows(self, prices, fetch_timestamp):
        return [
            (METRIC_PRICE, symbol, np.mean(symbol_prices), fetch_timestamp)
            for symbol, symbol_prices in prices.items()
        ]


if __name__ == '__main__':
    last_data_fetch_time = datetime.utcnow() - timedelta(seconds=60)
    data_fetcher = DataFetcher(
        db_client=DBClient('data_history.db'),
        requests_client=requests,
    )
    while True:
        current_time = datetime.utcnow()
        if (current_time - last_data_fetch_time).seconds >= 60:
            print(f'Updating data at {current_time.isoformat()}...')
            data_fetcher.update_data()
            print('Data updated.\n')
            last_data_fetch_time = current_time
