import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import cerberus
import schema

OSM_PATH = "webster_sample.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

##########################################################################################
#                                   HELPER FUNCTIONS                                     #
##########################################################################################

def fix_prob_chars(key):
    '''Eliminate problematic characters from keys'''
    
    if ' ' in key:
        new_key = list(key)
        for i, char in enumerate(new_key):
            if char == ' ':
                new_key[i] = '_'
    new_key = ''.join(new_key)
    return new_key
            

def fix_street_abbrevs(street):
    '''Expand abbreviations in street names'''
    
    mapping = {
        'ave': 'Avenue',
        'Ave': 'Avenue',
        'Avenu': 'Avenue',
        'Bl': 'Boulevard',
        'Blvd': 'Boulevard',
        'Cir': 'Circle',
        'Ct': 'Court',
        'Dr': 'Drive',
        'line': 'Line',
        'Pkwy': 'Parkway',
        'PW': 'Parkway',
        'Rd': 'Road',
        'St': 'Street',
        'Stree': 'Street',
        'N': 'North',
        'S': 'South',
        'E': 'East',
        'W': 'West'
    }
    
    elements = street.split()
    for i in range(len(elements)):
        if elements[i] in mapping:
            elements[i] = mapping[elements[i]]
    updated_street = ' '.join(elements)
    return updated_street


def fix_zipcode(zipcode):
    '''Check the zipcode for the proper format'''
    
    zipformat = re.compile(r"(^[0-9]{5})(-[0-9]{4})?")
    if zipformat.match(zipcode):
        return zipcode
    else:
        return 'fixme'


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, lower_colon=LOWER_COLON, \
                  default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []

    # If the element is a node, extract the appropriate tags with valid keys
    if element.tag == 'node':
        for attrib in element.attrib:
            if attrib in node_attr_fields:
                node_attribs[attrib] = element.attrib[attrib]
        for child in element:
            temp_attrib = {}
            if child.tag == 'tag':
                key = child.get('k')
                if problem_chars.search(key):
                    continue
                elif LOWER_COLON.search(key):
                    key_segments = key.split(':')
                    temp_attrib['type'] = key_segments[0]
                    temp_attrib['key'] = ':'.join(key_segments[1:])
                else:
                    temp_attrib['key'] = key
                temp_attrib['id'] = node_attribs['id']
                temp_attrib['type'] = default_tag_type
                temp_attrib['value'] = child.get('v')
                tags.append(temp_attrib)
                
    # If the element is a way, extract the appropriate tags with valid keys            
    if element.tag == 'way':
        for attrib in element.attrib:
            if attrib in way_attr_fields:
                way_attribs[attrib] = element.attrib[attrib]
        i = 0
        for child in element:
            temp_attrib = {}
            if child.tag == 'tag':
                key = child.get('k')
                if problem_chars.search(key):
                    continue
                elif LOWER_COLON.search(key):
                    key_segments = key.split(':')
                    temp_attrib['type'] = key_segments[0]
                    temp_attrib['key'] = ':'.join(key_segments[1:])
                else:
                    temp_attrib['key'] = key
                temp_attrib['id'] = way_attribs['id']
                temp_attrib['type'] = default_tag_type
                temp_attrib['value'] = child.get('v')
                tags.append(temp_attrib)
            if child.tag == 'nd':
                temp_attrib['id'] = way_attribs['id']
                temp_attrib['node_id'] = child.get('ref')
                temp_attrib['position'] = i
                way_nodes.append(temp_attrib)
                i += 1
	   
    # Clean the element's tags
    problem_chars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
    
    for tag in tags:
        
        # Eliminate problematic characters in keys
        if problem_chars.search(tag['key']):
            tag['key'] = fix_prob_chars(tag['key'])
        
        # Expand abbreviations in address fields
        if (tag['key'] == 'address') or \
           (tag['key'] == 'addr' and 'street' in tag['type']):
            tag['value'] = fix_street_abbrevs(tag['value'])
        
        # Replace invalid zipcodes with 'fixme'
        if (tag['key'] in ('zip_left', 'zip_right')) or \
           (tag['key'] == 'addr' and tag['type'] == 'postcode'):
            tag['value'] = fix_zipcode(tag['value'])     
    
    # Shape the element for integration into the database            
    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}



def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) \
            for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


##########################################################################################
#                                     MAIN FUNCTION                                      #
##########################################################################################

def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
            


if __name__ == '__main__':
    process_map(OSM_PATH, validate=True)