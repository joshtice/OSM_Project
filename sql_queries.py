import sqlite3
from pprint import pprint
import matplotlib.pyplot as plt
import numpy as np

DB = 'mydb.db'

def distribution_way_nodes(db=DB):
    '''Characterize the number of nodes that are associated with ways'''
	
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
    print "On average, %d nodes are associated with each way.\n" % results[0]

    # Query the top 20 ways with the highest number of associated nodes
    query = '''SELECT id, COUNT(node_id) AS num
			   FROM ways_nodes
			   GROUP BY id
			   ORDER BY num DESC
			   LIMIT 20;'''
    cur.execute(query)
    results = cur.fetchall()
    print 'WAY ID\t\tNODE COUNT'
    for result in results:
        print result[0], '\t', result[1]

    # Plot a histogram of the distribution of number of nodes per way
    query = '''SELECT COUNT(node_id) AS num
			   FROM ways_nodes
			   GROUP BY id
			   ORDER BY num DESC;'''
    cur.execute(query)
    results = cur.fetchall()
    results = [result[0] for result in results]
    plt.hist(results)
    plt.title('Distribution of Number of Nodes per Way')
    plt.xlabel('Number of nodes')
    plt.ylabel('Frequency')
    plt.show()
	
    conn.close()


def db_statistics(db=DB):
    '''Collect basic statistics on the database'''

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    
    # Count the total number of nodes
    query = '''SELECT COUNT(*)
			   FROM nodes;'''
    cur.execute(query)
    results = cur.fetchall()
    print "The database contains %d nodes." % results[0]
    
    # Count the total number of ways
    query = '''SELECT COUNT(*)
			   FROM ways;'''
    cur.execute(query)
    results = cur.fetchall()
    print "The database contains %d ways." % results[0]

    # Count the number of restaurant nodes
    query = '''SELECT COUNT(id)
               FROM nodes_tags
               WHERE value='restaurant' OR value='Restaurant'
               GROUP BY id;'''
    cur.execute(query)
    results = cur.fetchall()
    if results:
        print "The database contains %d restaurants in the nodes table." % results[0]
    else:
        print "The database does not contain any restaurants in the nodes table."


def describe_large_ways(db=DB):
    query = '''SELECT subquery.id, num, key, value, type
			   FROM 
				   (SELECT id, COUNT(node_id) AS num
					FROM ways_nodes
					GROUP BY id
					ORDER BY num DESC
					LIMIT 20) AS subquery
			   JOIN ways_tags
			   ON subquery.id=ways_tags.id
			   ORDER BY num DESC;'''
    cur.execute(query)
    results = cur.fetchall()
    #pprint(results)           
					   
			   
#distribution_way_nodes()
db_statistics()
           