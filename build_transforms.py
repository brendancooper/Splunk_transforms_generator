import argparse
import configparser
import csv
import os
import sys

from pathlib import Path

"""
Is there transforms that already does that functionality?
    If it exists:
        create a new props that points to that transforms
    else:
        create a new transforms based on the 'action' value:
            reroute = DEST_KEY = index, name = reroute_to_{{name}}
            drop = drop the event
            mask = DEST_KEY = _raw, name = mask_{{sourcetype}}_{{name}}
        create a new props that points to the new transform


"""


def handle_row(row):
    if row['action'] == "drop":
        transform_name = "drop_events"
    elif row['action'] == "reroute":
        transform_name = "reroute_to_{}".format(row['name'])
    elif row['action'] == "mask":
        transform_name = "mask_{}_{}".format(row['sourcetype'], row['name'])

    if transform_name not in transforms:
        if row['action'] == "drop":
            transforms[transform_name] = create_drop_config(row)
        elif row['action'] == "reroute":
            transforms[transform_name] = create_reroute_config(row)
        elif row['action'] == "mask":
            transforms[transform_name] = create_mask_config(row)

    create_props(row['sourcetype'], transform_name)


def create_reroute_config(row):
    config = {}
    config['DEST_KEY'] = "_MetaData:Index"
    config['REGEX'] = "^.*"
    config['FORMAT'] = row['name']
    return config


def create_mask_config(row):
    config = {}
    config['DEST_KEY'] = "_raw"
    config['REGEX'] = row['regex']
    config['FORMAT'] = row['format']
    return config


def create_drop_config(row):
    config = {}
    config['DEST_KEY'] = "queue"
    config['REGEX'] = "^.*"
    config['FORMAT'] = "nullQueue"
    return config


def create_props(sourcetype, transform_name):
    attr_name = "TRANSFORMS-" + transform_name
    if sourcetype not in props:
        props[sourcetype] = {}

    props[sourcetype][attr_name] = transform_name


parser = argparse.ArgumentParser(
    description='Bulk create Splunk Props/Transforms for routing,masking and dropping events using a simple csv format')
parser.add_argument('--input', required=True,
                    help='CSV File with following columns "sourcetype,action,name,format,regex"')

props = configparser.ConfigParser()
props.optionxform = str
transforms = configparser.ConfigParser()
transforms.optionxform = str

args = vars(parser.parse_args())
p = Path(args['input'])


with p.open() as file:
    lookup = csv.DictReader(file)
    for row in lookup:
        handle_row(row)

with open('props.conf', 'w') as configfile:
    props.write(configfile)

with open('transforms.conf', 'w') as configfile:
    transforms.write(configfile)
