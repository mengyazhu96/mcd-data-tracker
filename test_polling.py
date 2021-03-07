from datetime import datetime
import sqlite3
import unittest
from unittest.mock import MagicMock, create_autospec

import requests

from db import DBClient
from create_tables import create_tables
from write_metrics import DataFetcher

SAMPLE_MARKET_SUMMARY_RETURN_VALUE = {
    'binance-us:adabtc': {'price': {'last': 2.283e-05, 'high': 2.432e-05, 'low': 2.259e-05, 'change': {'percentage': -0.0511221945137157, 'absolute': -1.23e-06}}, 'volume': 2394892, 'volumeQuote': 55.92753027},
    'binance-us:adausd': {'price': {'last': 1.1122, 'high': 1.198, 'low': 1.0855, 'change': {'percentage': -0.0603244339303819, 'absolute': -0.0714}}, 'volume': 28411055.5, 'volumeQuote': 32258916.86776},
    'binance-us:adausdt': {'price': {'last': 1.11197, 'high': 1.19694, 'low': 1.08603, 'change': {'percentage': -0.0604711289859236, 'absolute': -0.07157}}, 'volume': 3360835.4, 'volumeQuote': 3787793.538279},
    'binance-us:algobusd': {'price': {'last': 1.0364, 'high': 1.0858, 'low': 1.004, 'change': {'percentage': -0.0388574608179542, 'absolute': -0.0419}}, 'volume': 238431.83, 'volumeQuote': 249344.065173},
    'binance-us:algousd': {'price': {'last': 1.037, 'high': 1.088, 'low': 1.005, 'change': {'percentage': -0.0371402042711235, 'absolute': -0.04}}, 'volume': 3326136.807, 'volumeQuote': 3487736.67522},
}
SAMPLE_PAIRS_RETURN_VALUE = [
    {'id': 313, 'symbol': 'adabtc', 'base': {'id': 166, 'symbol': 'ada', 'name': 'Cardano', 'fiat': False, 'route': 'https://api.cryptowat.ch/assets/ada'}, 'quote': {'id': 60, 'symbol': 'btc', 'name': 'Bitcoin', 'fiat': False, 'route': 'https://api.cryptowat.ch/assets/btc'}, 'route': 'https://api.cryptowat.ch/pairs/adabtc'},
    {'id': 1488, 'symbol': 'adausd', 'base': {'id': 166, 'symbol': 'ada', 'name': 'Cardano', 'fiat': False, 'route': 'https://api.cryptowat.ch/assets/ada'}, 'quote': {'id': 98, 'symbol': 'usd', 'name': 'United States Dollar', 'fiat': True, 'route': 'https://api.cryptowat.ch/assets/usd'}, 'route': 'https://api.cryptowat.ch/pairs/adausd'},
    {'id': 315, 'symbol': 'adausdt', 'base': {'id': 166, 'symbol': 'ada', 'name': 'Cardano', 'fiat': False, 'route': 'https://api.cryptowat.ch/assets/ada'}, 'quote': {'id': 2, 'symbol': 'usdt', 'name': 'Tether', 'fiat': False, 'route': 'https://api.cryptowat.ch/assets/usdt'}, 'route': 'https://api.cryptowat.ch/pairs/adausdt'},
    {'id': 119843, 'symbol': 'algobusd', 'base': {'id': 2773, 'symbol': 'algo', 'name': 'Algorand', 'fiat': False, 'route': 'https://api.cryptowat.ch/assets/algo'}, 'quote': {'id': 3664, 'symbol': 'busd', 'name': 'Binance USD', 'fiat': False, 'route': 'https://api.cryptowat.ch/assets/busd'}, 'route': 'https://api.cryptowat.ch/pairs/algobusd'},
    {'id': 4857, 'symbol': 'algousd', 'base': {'id': 2773, 'symbol': 'algo', 'name': 'Algorand', 'fiat': False, 'route': 'https://api.cryptowat.ch/assets/algo'}, 'quote': {'id': 98, 'symbol': 'usd', 'name': 'United States Dollar', 'fiat': True, 'route': 'https://api.cryptowat.ch/assets/usd'}, 'route': 'https://api.cryptowat.ch/pairs/algousd'},
]


class MockRequestsClient:
    def get(self, uri):
        response = create_autospec(requests.Response, autospec=True)
        if uri == 'https://api.cryptowat.ch/pairs':
            response.json = MagicMock(
                return_value={'result': SAMPLE_PAIRS_RETURN_VALUE},
            )
        elif uri == 'https://api.cryptowat.ch/markets/summaries':
            response.json = MagicMock(
                return_value={'result': SAMPLE_MARKET_SUMMARY_RETURN_VALUE},
            )
        else:
            raise NotImplementedError
        return response


class TestPolling(unittest.TestCase):
    def test_update_data(self):
        db_client = DBClient(':memory:')
        with sqlite3.connect(':memory:') as conn:
            create_tables(conn)
            db_client.get_connection = MagicMock(return_value=conn)
            data_fetcher = DataFetcher(db_client, MockRequestsClient())
            data_fetcher.update_data()

            timestamp_after_insert = datetime.utcnow().isoformat()
            inserted_rows = db_client.get_all(
                conditions=(f'timestamp < "{timestamp_after_insert}"',)
            )
            num_assets = len(
                {pair['base']['symbol'] for pair in SAMPLE_PAIRS_RETURN_VALUE}
                | {pair['quote']['symbol'] for pair in SAMPLE_PAIRS_RETURN_VALUE},
            )
            self.assertEqual(
                len(SAMPLE_MARKET_SUMMARY_RETURN_VALUE) + num_assets, len(inserted_rows),
            )

            previous_rows = db_client.get_all(
                conditions=(f'timestamp > "{timestamp_after_insert}"',)
            )
            self.assertEqual(0, len(previous_rows))


if __name__ == '__main__':
    unittest.main()
