#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
from collections import defaultdict
import re

osm_file = open("webster_full.osm", "r")
aggregation = defaultdict(int)

def is_way(elem):
	return(elem.tag == "way")

def is_tag(elem):
    return (elem.tag == "tag")
    
def print_sorted_dict(d):
    keys = d.keys()
    keys = sorted(keys, key=lambda s: s.lower())
    for k in keys:
        v = d[k]
        print "%s: %d" % (k, v) 

def aggregate_types(osm_file, aggregation):
    for event, elem in ET.iterparse(osm_file):
        if is_way(elem):
            for sub_tag in elem.iter():
                if is_tag(sub_tag):
                    aggregation[sub_tag.attrib['k']] += 1
    print_sorted_dict(aggregation)


if __name__ == '__main__':
    aggregate_types(osm_file, aggregation)
    osm_file.close()