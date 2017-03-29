import sqlite3
from pprint import pprint
import matplotlib.pyplot as plt
import numpy as np


DB = 'mydb.db'


##########################################################################################
#                                   HELPER FUNCTIONS                                     #
##########################################################################################

def db_statistics(db=DB):
    '''Collect basic statistics on the database'''

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
    print "The number of unique users in the database is: %d" % results[0]
    
    # Count the number of unique users represented in the 'nodes' table
    query = '''SELECT user, COUNT(*) AS num
               FROM nodes
               GROUP BY user
               ORDER BY num DESC;'''
    cur.execute(query)
    results = cur.fetchall()
    print "################# USER SUMMARY - NODES ##################"
    print "Number of unique users in the 'node' table: %d" % len(results)
    print "User / Number of contributions"
    for user, contribs in results:
        print "%s: %d" % (user, contribs)
        
    # Count the number of unique users represented in the 'ways' table
    query = '''SELECT user, COUNT(*) AS num
               FROM ways
               GROUP BY user
               ORDER BY num DESC;'''
    cur.execute(query)
    results = cur.fetchall()
    print "################# USER SUMMARY - WAYS ###################"
    print "Number of unique users in the 'way' table: %d" % len(results)
    print "User / Number of contributions"
    for user, contribs in results:
        print "%s: %d" % (user, contribs)
    
    # Count the total number of nodes
    query = '''SELECT COUNT(*)
			   FROM nodes;'''
    cur.execute(query)
    results = cur.fetchall()
    print "################# OTHER DB STATISTICS ###################"
    print "The database contains %d nodes." % results[0]
    
    # Count the total number of ways
    query = '''SELECT COUNT(*)
			   FROM ways;'''
    cur.execute(query)
    results = cur.fetchall()
    print "The database contains %d ways." % results[0]

    # Count the number of restaurant nodes
    query = '''SELECT COUNT(*)
               FROM nodes_tags
               WHERE value LIKE "%restaurant%"
               GROUP BY id
               ;'''
    cur.execute(query)
    results = cur.fetchall()
    if results:
        print "The database contains %d restaurants in the nodes_tags table." % results[0]
    else:
        print "The database does not contain any restaurants in the nodes_tags table."
        
    # Count the number of restaurant ways
    query = '''SELECT COUNT(*)
               FROM ways_tags
               WHERE value LIKE "%restaurant%"
               GROUP BY id
               ;'''
    cur.execute(query)
    results = cur.fetchall()
    if results:
        print "The database contains %d restaurants in the ways_tags table." % results[0]
    else:
        print "The database does not contain any restaurants in the ways_tags table."
        
    # Count the number of school nodes
    query = '''SELECT COUNT(*)
               FROM nodes_tags
               WHERE value LIKE "%school%"
               GROUP BY id;'''
    cur.execute(query)
    results = cur.fetchall()
    if results:
        print "The database contains %d schools in the nodes_tags table." % results[0]
    else:
        print "The database does not contain any schools in the nodes_tags table."
        
    # Count the number of school ways
    query = '''SELECT COUNT(*)
               FROM ways_tags
               WHERE value LIKE "%school%"
               GROUP BY id;'''
    cur.execute(query)
    results = cur.fetchall()
    if results:
        print "The database contains %d schools in the ways_tags table." % results[0]
    else:
        print "The database does not contain any schools in the ways_tags table."
        
        
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
    print "################# WAY-NODE RELATIONSHIPS ##################"
    print "On average, %d nodes are associated with each way." % results[0]

    # Query the top 20 ways with the highest number of associated nodes
    query = '''SELECT id, COUNT(node_id) AS num
			   FROM ways_nodes
			   GROUP BY id
			   ORDER BY num DESC
			   LIMIT 20;'''
    cur.execute(query)
    results = cur.fetchall()
    print 'WAY ID / NODE COUNT'
    for (way_id, node_count) in results:
        print "%s: %d" % (way_id, node_count)

    # Plot a histogram of the distribution of number of nodes per way
    query = '''SELECT COUNT(node_id) AS num
			   FROM ways_nodes
			   GROUP BY id
			   ORDER BY num DESC;'''
    cur.execute(query)
    results = cur.fetchall()
    results = [result[0] for result in results]
    plt.hist(results, bins=200, alpha=0.5)
    plt.title('Distribution of Number of Nodes per Way')
    plt.xlabel('Number of nodes')
    plt.ylabel('Frequency')
    plt.show()
	
    conn.close()


def describe_large_ways(db=DB):
    '''Output ways with the most number of nodes; Include tag information'''

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
    print "way id\t\tcount\tkey\tvalue\ttype"
    for (id, num, key, value, type) in results:
        print "%d\t%d\t%s\t%s\t%s" % (id, num, key, value, type)  
					   

##########################################################################################
#                                     MAIN FUNCTION                                      #
##########################################################################################

def run_all_queries(db=DB):
    db_statistics(db)
    distribution_way_nodes(db)
    describe_large_ways(db)




if __name__ == '__main__':			   
    run_all_queries(DB)
    
           