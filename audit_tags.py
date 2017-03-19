import xml.etree.cElementTree as ET
import pprint
from collections import defaultdict
import re


FILENAME = "Rochester.osm"


##########################################################################################
#                                   HELPER FUNCTIONS                                     #
##########################################################################################

def print_sorted_dict(d):
    '''Print key/value pairs from a dictionary, sorted by key'''
    keys = d.keys()
    keys = sorted(keys, key=lambda s: s.lower())
    for k in keys:
        v = d[k]
        print "%s: %d" % (k, v)
     
        
def iter_elements(filename=FILENAME, tags=('node', 'way', 'relation')):
    '''Yield element if it is a node, way, or relation'''
    context = ET.iterparse(filename, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()
    
            
def aggregate_tag_keys(filename=FILENAME):
    '''Compile all the keys found in tag subelements'''
    
    keys = defaultdict(int)
    for element in iter_elements(filename):
        for subelement in element:
            if (subelement.tag == 'tag') and ('k' in subelement.attrib):
                keys[subelement.get('k')] += 1
    return keys


def categorize_tags(filename=FILENAME):
    '''Compile all the keys that contain problem characters'''
    
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
    '''Compile all tags that contain problem characters'''
    
    problem_keys = defaultdict(int)
    problem_chars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
    keys = aggregate_tag_keys(filename)
    for key in keys:
        if problem_chars.search(key):
            problem_keys[key] += 1
    return problem_keys
      
    
def aggregate_addr_tags(filename=FILENAME):
    '''Compile all tags that contain information related to address'''
    
    addr_keys = defaultdict(int)
    keys = aggregate_tag_keys(filename)
    for key in keys:
        if 'addr' in key:
            addr_keys[key] += keys[key]
    return addr_keys
    
    
def aggregate_street_abbrevs(filename=FILENAME):
    '''Compile abbreviations found in tags related to address'''
    
    streets = defaultdict(int)
    street_tag = re.compile(r'^(addr:street)\w*')
    
    # Assume that street abbreviations, if they exist, will be the last word character at
    # the end of the full street string
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
    '''Compile zip codes'''
    
    zips = defaultdict(int)
    for element in iter_elements(filename):
        for subelement in element:
            if subelement.tag == 'tag' \
            and ('k' in subelement.attrib) \
            and (subelement.get('k') == 'addr:postcode'):
                key = subelement.get('v')
                zips[key] += 1
    return zips    
    

##########################################################################################
#                                     MAIN FUNCTION                                      #
##########################################################################################

def audit_osm_file(filename):

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
    audit_osm_file(FILENAME)