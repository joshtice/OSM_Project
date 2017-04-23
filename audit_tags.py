# -*- coding: utf-8 -*-
"""
Script audit_tags.py takes a raw OpenStreetMaps XML file and audits the tag 
elements for errors. Specifically, the script looks for:
 - Street names that are abbreviated
 - Tags with problematic characters (e.g., spaces)
 - Incorrect zip codes
 - Incorrect phone numbers
 
Acknowledgments:
https://classroom.udacity.com/nanodegrees/nd002/parts/0021345404/modules/
      316820862075461/lessons/5436095827/concepts/54456296460923#
https://classroom.udacity.com/nanodegrees/nd002/parts/0021345404/modules/
      316820862075461/lessons/5436095827/concepts/54446302850923#
"""

from collections import defaultdict
import pprint
import re
import xml.etree.cElementTree as ET


FILENAME = "Rochester.osm"
"""str: Path to OpenStreetMaps XML file to be analyzed"""

################################################################################
#                              HELPER FUNCTIONS                                #
################################################################################

def print_sorted_dict(d):
    """Print key/value pairs from a dictionary, sorted by key.
    
    Parameters
    ----------
    
    d : dict
        A dictionary with keys of type 'str'.
    """
    keys = d.keys()
    keys = sorted(keys, key=lambda s: s.lower())
    for k in keys:
        v = d[k]
        print "%s: %d" % (k, v)
     
        
def iter_elements(filename=FILENAME, tags=('node', 'way', 'relation')):
    """Yield an OSM element if it is a node, way, or relation.
    
    Parameters
    ----------
        filename : str
            A string containing the path to an OSM file. Defaults to the module 
            level variable FILENAME.
        tags : tuple
            The type of tags to be yielded by the function. Defaults to nodes, 
            ways, and relations.
            
    Yields
    ------
        xml.etree.cElementTree.Element
            An element of the OSM file that belongs to a type identified in the 
            parameter tags.
    """
    context = ET.iterparse(filename, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()
    
            
def aggregate_tag_keys(filename=FILENAME):
    """Compile all the keys found in tag subelements
    
    Parameters
    ----------
    filename : str
        A string containing the path to an OSM file. Defaults to the module 
        level variable FILENAME.
        
    Returns
    -------
    collections.defaultdict
        A dictionary containing counts of all the tag keys in an OSM file.
    """
    keys = defaultdict(int)
    for element in iter_elements(filename):
        for subelement in element:
            if (subelement.tag == 'tag') and ('k' in subelement.attrib):
                keys[subelement.get('k')] += 1
    return keys


def categorize_tags(filename=FILENAME):
    """Compile all the keys that contain problem characters
    
    Parameters
    ----------
    filename : str
        A string containing the path to an OSM file. Defaults to the module 
        level variable FILENAME.
        
    Returns
    -------
    dict
        A dictionary containing counts of five categories of tags: (i) 'fixme', 
        (ii) 'tiger', (iii) 'gnis', (iv) problematic characters, and (v) other.
    """
    problem_chars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
    key_categories = {'fixme':0, 'tiger':0, 'gnis':0, 'problem':0, 'other':0}
    keys = aggregate_tag_keys(filename)
    for key in keys:
        if problem_chars.search(key):
            key_categories['problem'] += keys[key]
        elif ('FIXME' in key) or ('fixme' in key):
            key_categories['fixme'] += keys[key]
        elif 'tiger' in key:
            key_categories['tiger'] += keys[key]
        elif 'gnis' in key:
            key_categories['gnis'] += keys[key]
        else:
            key_categories['other'] += keys[key]
    return key_categories


def aggregate_problem_tags(filename=FILENAME):
    """Compile all tags that contain problem characters
    
    Parameters
    ----------
    filename : str
        A string containing the path to an OSM file. Defaults to the module 
        level variable FILENAME.
    
    Returns
    -------
    collections.defaultdict
        A dictionary containing counts of specific problematic keys in the OSM
        file.
    """
    problem_keys = defaultdict(int)
    problem_chars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
    keys = aggregate_tag_keys(filename)
    for key in keys:
        if problem_chars.search(key):
            problem_keys[key] += 1
    return problem_keys
      
    
def aggregate_addr_tags(filename=FILENAME):
    """Compile all tags that contain information related to address
    
    Parameters
    ----------
    filename : str
        A string containing the path to an OSM file. Defaults to the module 
        level variable FILENAME.
        
    Returns
    -------
    collections.defaultdict
        A dictionary containing counts of keys that indicate an address 
        component.
    """
    addr_keys = defaultdict(int)
    keys = aggregate_tag_keys(filename)
    for key in keys:
        if 'addr' in key:
            addr_keys[key] += keys[key]
    return addr_keys
    
    
def aggregate_street_abbrevs(filename=FILENAME):
    """Compile abbreviations found in tags related to address
    
    Parameters
    ----------
    filename : str
        A string containing the path to an OSM file. Defaults to the module 
        level variable FILENAME.
        
    Returns
    -------
    collections.defaultdict
        A dictionary containing counts of common street abbreviations found in
        tags.
    """
    streets = defaultdict(int)
    street_tag = re.compile(r'^(addr:street)\w*')
    
    # Assume that street abbreviations, if they exist, will be the last word 
    # character at the end of the full street string
    street_name = re.compile(r'\b\w+\b$')
    
    for element in iter_elements(filename):
        for subelement in element:
            if subelement.tag == 'tag' \
            and ('k' in subelement.attrib):
                key = subelement.get('k')
                if street_tag.search(key):
                    street = street_name.search(subelement.get('v'))
                    if street:
                        streets[street.group()] += 1
    return streets
    
    
def aggregate_zips(filename=FILENAME):
    """Compile zip codes
    
    Parameters
    ----------
    filename : str
        A string containing the path to an OSM file. Defaults to the module 
        level variable FILENAME.
        
    Returns
    -------
    collections.defaultdict
        A dictionary containing counts of unique zip codes in the OSM file.
    """
    zips = defaultdict(int)
    for element in iter_elements(filename):
        for subelement in element:
            if subelement.tag == 'tag' \
            and ('k' in subelement.attrib) \
            and (subelement.get('k') == 'addr:postcode'):
                key = subelement.get('v')
                zips[key] += 1
    return zips    
    

################################################################################
#                                MAIN FUNCTION                                 #
#############################################@##################################

def audit_osm_file(filename=FILENAME):
    """Perform audit of OSM file.
    
    Parameters
    ----------
    filename : str
        A string containing the path to an OSM file. Defaults to the module 
        level variable FILENAME.
    """
    keys = aggregate_tag_keys(filename)

    print "#################### KEYS ####################\n"
    print "Total unique keys: ", len(keys)
    print_sorted_dict(keys)

    print "\n\n"
    print "############### KEY CATEGORIES ###############\n"
    print_sorted_dict(categorize_tags(filename))

    print "\n\n"
    print "################ PROBLEM KEYS ################\n"
    print_sorted_dict(aggregate_problem_tags(filename))

    print "\n\n"
    print "########## KEYS RELATED TO ADDRESS ###########\n"
    print_sorted_dict(aggregate_addr_tags(filename))

    print "\n\n"
    print "############ STREET ABBREVIATIONS ############\n"
    print_sorted_dict(aggregate_street_abbrevs(filename))

    print "\n\n"
    print "################# ZIP CODES ##################\n"
    print ""
    print_sorted_dict(aggregate_zips(filename))


if __name__ == '__main__':
    audit_osm_file()