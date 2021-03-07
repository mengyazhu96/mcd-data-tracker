from datetime import datetime, timedelta
import sqlite3

import numpy as np


def get_timestring_24h_ago():
    return (datetime.utcnow() - timedelta(days=1)).isoformat()


class DBClient:
    def __init__(self, db_file_name):
        self.db_file_name = db_file_name

    def get_connection(self):
        return sqlite3.connect(self.db_file_name)

    def get_symbols_for_metric_type(self, metric_type):
        result = self._read_all(f'''
            SELECT DISTINCT symbol FROM metric_history 
            WHERE metric_type = "{metric_type}"
        ''')
        return [elt[0] for elt in result]

    def get_values_in_last_24h(self, metric_type, symbol):
        result = self._read_all(f'''
            SELECT timestamp, value FROM metric_history 
            WHERE metric_type = "{metric_type}"
            AND symbol = "{symbol}"
            AND timestamp > "{get_timestring_24h_ago()}"
            ORDER BY timestamp ASC
        ''')
        return dict(result)

    def _read_all(self, statement):
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(statement)
            result = cursor.fetchall()
        return result

    def get_all(self, columns=('*',), conditions=tuple()):
        query = f'SELECT {",".join(columns)} FROM metric_history'
        if conditions:
            query += ' WHERE '
            query += ' AND '.join(conditions)
        return self._read_all(query)

    def insert_many_metric_history(self, rows):
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.executemany(
                'INSERT INTO metric_history VALUES (?, ?, ?, ?)',
                rows,
            )

    def get_sd_by_symbol(self, metric_type):
        with self.get_connection() as connection:
            connection.create_aggregate('sd', 1, SDAggregate)
            cursor = connection.cursor()
            cursor.execute(f'''
                SELECT symbol, sd(value)
                FROM metric_history
                WHERE metric_type = "{metric_type}"
                AND timestamp > "{get_timestring_24h_ago()}"
                ORDER BY sd(value) DESC
            ''')
            result = cursor.fetchall()
        return result


class SDAggregate:
    def __init__(self):
        self.values = []

    def step(self, value):
        self.values.append(value)

    def finalize(self):
        print(len(values))
        return np.std(self.values)

