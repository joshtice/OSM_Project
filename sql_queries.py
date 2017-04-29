# -*- coding: utf-8 -*-
"""
Script sql_queries.py performs a series of SQL queries on a database created 
from an OpenStreetMaps file processed with scripts osm_to_csv.py and 
csv_to_database.py.
 
Acknowledgments:
[1] https://gist.github.com/carlward/54ec1c91b62a5f911c42#file-sample_project-md
"""


import matplotlib.pyplot as plt
import numpy as np
from pprint import pprint
import seaborn
import sqlite3


DB = 'mydb.db'
"""str: Path to the sqlite database to be queried."""


################################################################################
#                              HELPER FUNCTIONS                                #
################################################################################

def db_statistics(db=DB):
    """Collect basic statistics on the database.
    
    Parameters
    ----------
    db : str
        Path to the sqlite database to be queried.
    """
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    
    # Count the number of unique users in the entire OSM file
    query = '''SELECT COUNT(DISTINCT(subquery.uid))
               FROM
                   (SELECT uid FROM nodes
                    UNION ALL
                    SELECT uid FROM ways)
                   AS subquery;'''
    cur.execute(query)
    results = cur.fetchall()
    print "Number of unique users in the database is: %d" % results[0]
    
    # Identify the most active users and their number of contributions
    query = '''SELECT subquery.user, count(*) AS num
               FROM
                   (SELECT user from nodes
                    UNION ALL
                    SELECT user from ways)
                   AS subquery
               GROUP BY subquery.user
               ORDER BY num DESC
               LIMIT 10;'''
    cur.execute(query)
    results = cur.fetchall()
    print "Top contributors|Number of contibutions: "
    for user, contribs in results:
        print "%s|%r" % (user, contribs)
    
    # Count the total number of nodes
    query = '''SELECT COUNT(*)
			   FROM nodes;'''
    cur.execute(query)
    results = cur.fetchall()
    print "Number of nodes: %d" % results[0]
    
    # Count the total number of ways
    query = '''SELECT COUNT(*)
			   FROM ways;'''
    cur.execute(query)
    results = cur.fetchall()
    print "Nuber of ways: %d" % results[0]

    # Count the number of nodes and ways related to restaurants
    query = '''SELECT COUNT(DISTINCT(value))
               FROM 
                   (SELECT value from nodes_tags
                    UNION ALL
                    SELECT value from ways_tags)
                   AS subquery 
               WHERE subquery.value LIKE "%restaurant%";'''
    cur.execute(query)
    results = cur.fetchall()
    print "Number of restaurants: %d" %  results[0]
        
    # Count the number of school nodes
    query = '''SELECT COUNT(DISTINCT(value))
               FROM 
                   (SELECT value from nodes_tags
                    UNION ALL
                    SELECT value from ways_tags)
                   AS subquery 
               WHERE subquery.value LIKE "%school%";'''
    cur.execute(query)
    results = cur.fetchall()
    print "Number of schools: %d" % results[0]
                
        
def distribution_way_nodes(db=DB):
    """Characterize the number of nodes that are associated with ways.
    
    Parameters
    ----------
    db : str
        Path to the sqlite database to be queried.
    """
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    # Calculate the average number of nodes associated with a way
    query = '''SELECT AVG(num)
               FROM
                   (SELECT COUNT(node_id) AS num
                    FROM ways_nodes
                    GROUP BY id)
               AS subquery;'''
    
    cur.execute(query)
    results = cur.fetchall()
    print "Average nodes associated with each way: %d" % results[0]

    # Query the top 20 ways with the highest number of associated nodes
    query = '''SELECT id, COUNT(node_id) AS num
			   FROM ways_nodes
			   GROUP BY id
			   ORDER BY num DESC
			   LIMIT 20;'''
    cur.execute(query)
    results = cur.fetchall()
    print 'WAY ID|NODE COUNT'
    for (way_id, node_count) in results:
        print "%s|%d" % (way_id, node_count)

    # Plot a histogram of the distribution of number of nodes per way
    query = '''SELECT COUNT(node_id) AS num
			   FROM ways_nodes
			   GROUP BY id
			   ORDER BY num DESC;'''
    cur.execute(query)
    results = cur.fetchall()
    results = [result[0] for result in results]
    plt.hist(results, bins=100, range=(0, 100))
    plt.title('Distribution of Number of Nodes per Way')
    plt.xlabel('Number of nodes')
    plt.ylabel('Frequency')
    plt.show()
	
    conn.close()


def describe_large_ways(db=DB):
    """Output ways with the most number of nodes; Include tag information.
    
    Parameters
    ----------
    db : str
        Path to the sqlite database to be queried.
    """

    conn = sqlite3.connect(db)
    cur = conn.cursor()

    query = '''SELECT subquery.id, num, key, value, type
			   FROM 
				   (SELECT id, COUNT(node_id) AS num
					FROM ways_nodes
					GROUP BY id
					ORDER BY num DESC
					LIMIT 20) AS subquery
			   JOIN ways_tags
			   ON subquery.id=ways_tags.id
			   ORDER BY num DESC
			   LIMIT 10;'''
    cur.execute(query)
    results = cur.fetchall()
    print "way id|num nodes|key|value|type"
    for (id, num, key, value, type) in results:
        print "%d|%d|%s|%s|%s" % (id, num, key, value, type)  
					   

################################################################################
#                                MAIN FUNCTION                                 #
################################################################################

def run_all_queries(db=DB):
    """Run all SQL queries from helper functions.
    
    Parameters
    ----------
    db : str
        Path to the sqlite database to be queried.
    """
    db_statistics(db)
    distribution_way_nodes(db)
    describe_large_ways(db)


if __name__ == '__main__':			   
    run_all_queries()
    
           