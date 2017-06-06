#!/usr/bin/env python

import sys
import json
import os
import boto3

try:
    env = sys.argv[1]
except IndexError:
    print("provide env name as a first argument")
    sys.exit(1)

s3 = boto3.client('s3')
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
settings_f = open(os.path.join(root_path, 'zappa_settings.json'))
settings = json.load(settings_f)
(_, _, bucket, path) = settings[env]['remote_env'].split('/')

s3.upload_file(os.path.join(root_path, 'remote_env.json'),
               bucket,
               path)
