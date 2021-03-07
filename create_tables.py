import sqlite3


def create_tables(connection):
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE metric_history(
        metric_type text,
        symbol text,
        value real,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    connection.commit()


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Provide db_file_name.')
        exit(1)
    with sqlite3.connect(sys.argv[1]) as conn:
        create_tables(conn)
