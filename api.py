from flask import Flask
from flask_restful import Resource, Api, abort

from db import DBClient
from write_metrics import METRIC_TYPES


app = Flask(__name__)
api = Api(app)


def get_db_client():
    return DBClient('data_history.db')


class Ping(Resource):
    def get(self):
        return {'status': 'ok'}


class MetricTypesList(Resource):
    def get(self):
        return {
            'metric_types': [
                {'metric_type': metric_type}
                for metric_type in METRIC_TYPES
            ]
        }


def abort_if_metric_type_does_not_exist(metric_type):
    if metric_type not in METRIC_TYPES:
        abort(404, message=f'Metric type "{metric_type}" does not exist')


class MetricType(Resource):
    def get(self, metric_type):
        abort_if_metric_type_does_not_exist(metric_type)
        return {'metric_type': metric_type}


class MetricTypeMetricsList(Resource):
    def get(self, metric_type):
        abort_if_metric_type_does_not_exist(metric_type)
        symbols = get_db_client().get_symbols_for_metric_type(metric_type)
        return {
            'metrics': [
                {
                    'metric_type': metric_type,
                    'symbol': symbol,
                }
                for symbol in symbols
            ]
        }


def abort_if_symbol_does_not_exist(metric_type, symbol):
    if symbol not in get_db_client().get_symbols_for_metric_type(metric_type):
        abort(
            404,
            message=f'Metric of type "{metric_type}" for symbol "{symbol}" does not exist',
        )


class Metric(Resource):
    def get(self, metric_type, symbol):
        abort_if_metric_type_does_not_exist(metric_type)
        abort_if_symbol_does_not_exist(metric_type, symbol)
        return {
            'metric_type': metric_type,
            'symbol': symbol,
        }


class MetricHistory(Resource):
    def get(self, metric_type, symbol):
        abort_if_metric_type_does_not_exist(metric_type)
        abort_if_symbol_does_not_exist(metric_type, symbol)
        return get_db_client().get_values_in_last_24h(metric_type, symbol)


class MetricRank(Resource):
    def get(self, metric_type, symbol):
        abort_if_metric_type_does_not_exist(metric_type)
        abort_if_symbol_does_not_exist(metric_type, symbol)
        raise NotImplementedError


api.add_resource(Ping, '/')
api.add_resource(MetricTypesList, '/metric_types')
api.add_resource(MetricType, '/metric_types/<metric_type>')
api.add_resource(MetricTypeMetricsList, '/metric_types/<metric_type>/metrics')
api.add_resource(Metric, '/metric_types/<metric_type>/metrics/<symbol>')
api.add_resource(MetricHistory, '/metric_types/<metric_type>/metrics/<symbol>/history')
api.add_resource(MetricRank, '/metric_types/<metric_type>/metrics/<symbol>/rank')


if __name__ == '__main__':
    app.run(debug=True)
