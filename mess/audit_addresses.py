#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
from collections import defaultdict
import re

osm_file = open("Rochester.osm", "r")
aggregation = defaultdict(int)
    
def print_sorted_dict(d):
    keys = d.keys()
    keys = sorted(keys, key=lambda s: s.lower())
    for k in keys:
        v = d[k]
        print "%s: %d" % (k, v) 

def aggregate_types(osm_file, aggregation):
    weird = ('addr:city_1',
             'addr:housenumber_1',
             'addr:housenumber_2',
             'addr:housenumber_3',
             'addr:housenumber_4',
             'addr:housenumber_5',
             'addr:street_1',
             'addr:street_2',
             'addr:street_3',
             'unit',
             'address')
    for event, elem in ET.iterparse(osm_file):
        if elem.tag in ("node", "way", "relation"):
            for child in elem.iter():
                if (child.tag == "tag") and ("addr" in child.attrib['k']):
                    #print 'k: ', child.attrib['k'], ' v: ', child.attrib['v']
                    aggregation[child.attrib['k']] += 1
    print_sorted_dict(aggregation)


if __name__ == '__main__':
    aggregate_types(osm_file, aggregation)
    osm_file.close()