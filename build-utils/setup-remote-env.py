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


remote_env = {
    "AWS_DEFAULT_REGION": os.environ["AWS_DEFAULT_REGION"],

    "AUTH0_DOMAIN": os.environ["AUTH0_DOMAIN"],
    "AUTH0_CLIENT_ID": os.environ["AUTH0_CLIENT_ID"],
    "AUTH0_CLIENT_SECRET": os.environ["AUTH0_CLIENT_SECRET"],

    "EXTENSIONS_TABLE_NAME": os.environ["EXTENSIONS_TABLE_NAME"],
    "EXT_IMAGES_BUCKET_NAME": os.environ["EXT_IMAGES_BUCKET_NAME"],

    "LOG_LEVEL": os.environ.get("LOG_LEVEL", 20)
}

s3.put_object(
    Body=json.dumps(remote_env, indent=2),
    Bucket=bucket,
    Key=path,
    ContentEncoding='utf-8'
)
