# -*- coding: utf-8 -*-
"""
Script csv_to_database.py takes a series of csv files containing records with 
an appropriate schema and transfers the records to a database. The csv files 
should be created with script osm_to_csv.py, which extracts records from an 
OpenStreetMaps XML file.
 
Acknowledgments:
[1] http://stackoverflow.com/questions/2887878/importing-a-csv-file-into-a-
    sqlite3-database-table-using-python
"""


import csv
from pprint import pprint
import sqlite3


SQLITE_FILE = 'mydb.db'
"""str: Path to the database to be created."""

NODES = 'nodes.csv'
"""str: Path to the csv file containing data for the 'nodes' table."""

NODES_TAGS = 'nodes_tags.csv'
"""str: Path to the csv file containing data for the 'nodes_tags' table."""

WAYS = 'ways.csv'
"""str: Path to the csv file containing data for the 'ways' table."""

WAYS_NODES = 'ways_nodes.csv'
"""str: Path to the csv file containing data for the 'ways_nodes' table."""

WAYS_TAGS = 'ways_tags.csv'
"""str: Path to the csv file containing data for the 'ways_tags' table."""


def convert_csv_to_database(sqlite_file=SQLITE_FILE, nodes=NODES, 
                            nodes_tags=NODES_TAGS, ways=WAYS, 
                            ways_nodes=WAYS_NODES, ways_tags=WAYS_TAGS,
                            check_tables=True):
    """Transfers records from csv files to a sqlite database.
    
    Parameters
    ----------
    sqlite_file : str
        Path to the sqlite database file to be created.
    
    nodes : str
        Path to the csv file containing data for the 'nodes' table.
    
    nodes_tags : str
        Path to the csv file containing data for the 'nodes_tags' table.
    
    ways : str
        Path to the csv file containing data for the 'ways' table.
    
    ways_nodes : str
        Path to the csv file containing data for the 'ways_nodes' table.
    
    ways_tags : str
        Path to the csv file containing data for the 'ways_tags' table.
    """
    # Connect to the database
    conn = sqlite3.connect(sqlite_file)
    # Get a cursor object
    cur = conn.cursor()
    # Drop the table if it already exists
    cur.execute('DROP TABLE IF EXISTS nodes')
    cur.execute('DROP TABLE IF EXISTS nodes_tags')
    cur.execute('DROP TABLE IF EXISTS ways')
    cur.execute('DROP TABLE IF EXISTS ways_nodes')
    cur.execute('DROP TABLE IF EXISTS ways_tags')
    conn.commit()

    # Create the table, specifying the column names and data types
    cur.execute('''CREATE TABLE nodes(
                   id INTEGER PRIMARY KEY, 
                   lat REAL, 
                   lon REAL, 
                   user TEXT,
                   uid INTEGER, 
                   version TEXT, 
                   changeset INTEGER, 
                   timestamp TEXT)'''
                )
    cur.execute('''CREATE TABLE nodes_tags(
                   id INTEGER REFERENCES nodes(id), 
                   key TEXT, 
                   value TEXT, 
                   type TEXT)'''
                )
    cur.execute('''CREATE TABLE ways(
                   id INTEGER PRIMARY KEY, 
                   user TEXT, 
                   uid INTEGER, 
                   version TEXT,
                   changeset INTEGER, 
                   timestamp TEXT)'''
                )
    cur.execute('''CREATE TABLE ways_nodes(
                   id INTEGER REFERENCES ways(id), 
                   node_id INTEGER REFERENCES nodes(id), 
                   position INTEGER)'''
                )
    cur.execute('''CREATE TABLE ways_tags(
                   id INTEGER REFERENCES ways(id)	, 
                   key TEXT, 
                   value TEXT, 
                   type TEXT)'''
                )
    # Commit the changes
    conn.commit() 

    # Read in the csv file as a dictionary; format the data as a list of tuples;
    # upload to db
    with open('nodes.csv', 'rb') as fin:
        dr = csv.DictReader(fin)
        to_db = [(i['id'].decode('utf-8'), i['lat'].decode('utf-8'), \
                  i['lon'].decode('utf-8'), i['user'].decode('utf-8'), \
                  i['uid'].decode('utf-8'), i['version'].decode('utf-8'), \
                  i['changeset'].decode('utf-8'), \
                  i['timestamp'].decode('utf-8')) for i in dr]
    cur.executemany('INSERT INTO nodes(id, lat, lon, user, uid, version, \
                    changeset, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?);', \
                    to_db)
    conn.commit()

    with open('nodes_tags.csv', 'rb') as fin:
        dr = csv.DictReader(fin)
        to_db = [(i['id'].decode('utf-8'), i['key'].decode('utf-8'), \
                  i['value'].decode('utf-8'), i['type'].decode('utf-8')) \
                  for i in dr] 
    cur.executemany('INSERT INTO nodes_tags(id, key, value, type) VALUES \
                    (?, ?, ?, ?);', to_db)
    conn.commit()

    with open('ways.csv', 'rb') as fin:
        dr = csv.DictReader(fin)
        to_db = [(i['id'].decode('utf-8'), i['user'].decode('utf-8'), \
                  i['uid'].decode('utf-8'), i['version'].decode('utf-8'), \
                  i['changeset'].decode('utf-8'), \
                  i['timestamp'].decode('utf-8')) for i in dr]
    cur.executemany('INSERT INTO ways(id, user, uid, version, changeset, \
                    timestamp) VALUES (?, ?, ?, ?, ?, ?);', to_db)
    conn.commit()

    with open('ways_nodes.csv', 'rb') as fin:
        dr = csv.DictReader(fin)
        to_db = [(i['id'].decode('utf-8'), i['node_id'].decode('utf-8'), \
                  i['position'].decode('utf-8')) for i in dr]
    cur.executemany('INSERT INTO ways_nodes(id, node_id, position) VALUES \
                    (?, ?, ?);', to_db)
    conn.commit()

    with open('ways_tags.csv', 'rb') as fin:
        dr = csv.DictReader(fin)
        to_db = [(i['id'].decode('utf-8'), i['key'].decode('utf-8'), \
                  i['value'].decode('utf-8'), i['type'].decode('utf-8')) \
                  for i in dr]
    cur.executemany('INSERT INTO ways_tags(id, key, value, type) VALUES \
                    (?, ?, ?, ?);', to_db)
    conn.commit()

    # Check that the data imported correctly
    if check_tables == True:
        for f in ('nodes', 'nodes_tags', 'ways', 'ways_nodes', 'ways_tags'):
            table = (f,)
            cur.execute('SELECT * FROM %s LIMIT 10;' % f)
            all_rows = cur.fetchall()
            pprint(all_rows)

    # Close the connection
    conn.close()


if __name__ == '__main__':
    convert_csv_to_database(check_tables=False)