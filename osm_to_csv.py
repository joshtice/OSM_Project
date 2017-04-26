# -*- coding: utf-8 -*-
"""
Script osm_to_csv.py takes an OpenStreetMaps XML file, cleans the tag data, and
outputs the data to .csv files with an SQL database schema. The data cleaning 
addresses the following:
 - Problematic characters in keys, spacifically spaces --> underscores
 - Abbreviated street names --> unabbreviated street names
 - Incorrect city names --> corrected city names
 - Incorrect zip codes --> labeled with 'fixme'
 - Multiple format phone numbers --> uniform format phone numbers
 
Acknowledgments:
[1] https://classroom.udacity.com/nanodegrees/nd002/parts/0021345404/modules/
    316820862075461/lessons/5436095827/concepts/54908788190923#
"""

import cerberus
import codecs
import csv
import pprint
import re
import schema
import xml.etree.cElementTree as ET


OSM_PATH = "Rochester.osm"
"""str: Path to OpenStreetMaps XML file to be analyzed."""

NODES_PATH = "nodes.csv"
"""str: File name for nodes data output."""

NODE_TAGS_PATH = "nodes_tags.csv"
"""str: File name for nodes' tags data output."""

WAYS_PATH = "ways.csv"
"""str: File name for ways data output."""

WAY_NODES_PATH = "ways_nodes.csv"
"""str: File name for ways' nodes data output."""

WAY_TAGS_PATH = "ways_tags.csv"
"""str: File name for ways' tags data output."""

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
"""re.RegexObject: Regular expression to identify colons in keys."""

PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
"""re.RegexObject: Regular expression to identify problematic characters."""

SCHEMA = schema.schema
"""dict: JSON-like dictionary to identify schema for csv files."""

NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset',
               'timestamp']
"""list: Fields for node entries."""

NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
"""list: Fields for node tag entries."""

WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
"""list: Fields for way entries."""

WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
"""list: Fields for way tag entries."""

WAY_NODES_FIELDS = ['id', 'node_id', 'position']
"""list: Fields for way's node entries."""


################################################################################
#                              HELPER FUNCTIONS                                #
################################################################################

def fix_prob_chars(key, problem_chars=PROBLEMCHARS):
    """Eliminate problematic characters from keys. Specifically replaces problem
    characters with underscores.
    
    Parameters
    ----------
    key : str
        Key to be fixed by replacing spaces with underscores.
        
    Returns
    -------
    str
        The updated key, with underscores inserted in the place of spaces.        
    """
    if problem_chars.search(key):
        new_key = re.sub(' ', '_', key)
    return new_key
            

def fix_street_abbrevs(street):
    """Expand abbreviations in street names.
    
    Parameters
    ----------
    street : str
        The name of a street to be cleaned.
        
    Returns
    -------
    str
        The cleaned street name, with abbreviations replaced with their full
        form.
    """
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


def fix_cities(city):
    """Fix erroneous cities in the OSM file. Specifically, make sure that cities
    are capitalized and valid.
    
    Parameters
    ----------
    city : str
        The name of a city.
        
    Returns
    -------
    str
        A clean version of the original city value.  
    """
    mapping = {
        'East Rochester Town': 'East Rochester',
        'Rochester, NY': 'Rochester',
        'Rochestet': 'Rochester',
        'W Commercial St': 'East Rochester'
    }
    
    city = city.capitalize()
    if city in mapping:
        city = mapping[city]
    return city


def fix_zipcode(zipcode):
    """Check the zipcode for the proper format. Relabel with 'fixme' if
    incorrect.
    
    Parameters
    ----------
    zipcode : str
        The zipcode to be cleaned.
        
    Returns
    -------
    str
        The unchanged zipcode, if formatted correctly. The label 'fixme' if 
        erroneous.
    """
    # Look for zipcodes that have the format '12345', with optional trailing
    # four digits '-6789'
    zipformat = re.compile(r"(^[0-9]{5})(-[0-9]{4})?")
    if zipformat.search(zipcode):
        return zipcode
    else:
        return 'fixme'


def fix_phone_numbers(phone_number):
    """Change all phone numbers to format '123-456-7890'.
    
    Parameters
    ----------
    phone_number : str
        A phone number extracted from the OSM file.
        
    Returns
    -------
    str
        The phone number in format '123-456-7890'. Country code omitted.        
    """
    # Find clusters of digits between 3 and 10 numbers in length
    number_re = re.compile(r'[0-9]{3,10}')
    digits = number_re.findall(phone_number)
    # If more than 3 clusters are present, then omit the first cluster, the 
    # country code (note: the initial audit showed that no extensions were 
    # present)
    if len(digits) > 3:
        digits = digits[1:]
    # Reformat the digits to '123-456-7890'
    digits = ''.join(digits)
    new_phone_number = '-'.join([digits[0:3], digits[3:6], digits[6:10]])
    return new_phone_number
    

def clean_tags(tags, problem_chars=PROBLEMCHARS):
    """Clean tags from the OSM file.
    
    Parameters
    ----------
    tags : list
        A list of tag attributes to be cleaned.
        
    problem_chars : re.RegexObject
        Regular expression to identify problematic characters.
        
    Returns
    -------
    list
        A cleaned version of the input tag attribute list.
    """   
    for tag in tags:
        # Eliminate problematic characters in keys
        if problem_chars.search(tag['key']):
            tag['key'] = fix_prob_chars(tag['key'])
        # Expand abbreviations in address fields
        if (tag['key'] == 'address') or \
           (tag['key'] == 'street' and 'street' in tag['type']):
            tag['value'] = fix_street_abbrevs(tag['value'])
        # Fix erroneous city values
        if tag['key'] in ('city', 'city_1'):
            tag['value'] = fix_cities(tag['value'])
        # Replace invalid zipcodes with 'fixme'
        if (tag['key'] in ('zip_left', 'zip_right')) or \
           (tag['key'] == 'addr' and tag['type'] == 'postcode'):
            tag['value'] = fix_zipcode(tag['value'])   
        # Reformat phone numbers
        if tag['key'] == 'phone':
            tag['value'] = fix_phone_numbers(tag['value'])
    return tags
            

def shape_element(element, node_attr_fields=NODE_FIELDS, 
                  way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, lower_colon=LOWER_COLON,
                  default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict.
    
    Parameters
    ----------
    element : xml.etree.cElementTree.Element
        An element of the OSM file.
        
    node_attr_fields : list
        Fields from node elements to be transferred to database.
        
    way_attr_fields : list
        Fields from way elements to be transferred to database.
        
    problem_chars : re.RegexObject
        Regular expression to identify problematic characters.
        
    lower_colon : re.RegexObject
        Regular expression to identify colons in keys.
        
    default_tag_type : str
        Default value for tag field 'type'.
        
    Returns
    -------
    dict
        A dictionary with the attributes and tags for a node or way shaped
        appropriately for upload to a SQL database.
    """
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
                if lower_colon.search(key):
                    key_segments = key.split(':')
                    temp_attrib['type'] = key_segments[0]
                    temp_attrib['key'] = ':'.join(key_segments[1:])
                else:
                    temp_attrib['type'] = default_tag_type
                    temp_attrib['key'] = key
                temp_attrib['id'] = node_attribs['id']
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
                if lower_colon.search(key):
                    key_segments = key.split(':')
                    temp_attrib['type'] = key_segments[0]
                    temp_attrib['key'] = ':'.join(key_segments[1:])
                else:
                    temp_attrib['type'] = default_tag_type
                    temp_attrib['key'] = key
                temp_attrib['id'] = way_attribs['id']
                temp_attrib['value'] = child.get('v')
                tags.append(temp_attrib)
            if child.tag == 'nd':
                temp_attrib['id'] = way_attribs['id']
                temp_attrib['node_id'] = child.get('ref')
                temp_attrib['position'] = i
                way_nodes.append(temp_attrib)
                i += 1
	
	# Clean tags   
    tags = clean_tags(tags, problem_chars)  
     
    # Shape the element for integration into the database            
    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}



def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag.
    
    Parameters
    ----------
    osm_file : str
        Path to the OSM file.
        
    tags : tuple
        Tuple of strings that indicate which elements to extract from the OSM
        file.
        
    Yields
    ------
    xml.etree.cElementTree.Element
        An element of the OSM file that belongs to a type identified in the 
        parameter 'tags'.
    """
    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema.
    
    Parameters
    ----------
    element : xml.etree.cElementTree.Element
            An element of the OSM file.
    
    validator : cerberus.validator.Validator
        Validation schema for the records to be uploaded to the database.
        
    schema : dict
        JSON-like dictionary to identify schema for csv files.
        
    Raises
    ------
    ValiidationError
        If the shaped element does not match the schema.
        
    """
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following \
                          errors:\n{1}"
        error_string = pprint.pformat(errors)
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input."""

    def writerow(self, row):
        """Write a row of text to a csv file.
        
        Parameters
        ----------
        row : dict
            Key, value pairs to be written to a csv file.
        """
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) \
            for k, v in row.iteritems()
        })

    def writerows(self, rows):
       """Write values to csv file.
       
       Parameters
       ----------
       rows : dict
           Key, vaue pairs to be written to a csv file.
       """
       for row in rows:
           self.writerow(row)


################################################################################
#                                MAIN FUNCTION                                 #
################################################################################

def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s).
    
    Parameters
    ----------
    file_in : str
        Path to OSM XMl file to be analyzed.
        
    validate : bool
        True if validation to be executed. False if validation omitted.
    """

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