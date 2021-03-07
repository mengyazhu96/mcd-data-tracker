import sqlite3


def create_tables(connection):
    cursor = connection.cursor()
    # cursor.execute('''CREATE TABLE metric_type (
    #     -- id integer PRIMARY KEY,
    #     metric_type_name TEXT
    # )''')
    # cursor.execute('''INSERT INTO metric_type VALUES ("volume")''')

    # volume_id = cursor.execute('''
    #     SELECT rowid FROM metric_type WHERE metric_type_name = "volume"
    # ''').fetchone()[0]
    # print(volume_id)

    # cursor.execute('''CREATE TABLE metric(
    #     -- id integer PRIMARY KEY,
    #     metric_type_id integer,
    #     metric_identifier TEXT
    # )''')



    cursor.execute('''CREATE TABLE metric_history(
        -- id integer PRIMARY KEY,
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
