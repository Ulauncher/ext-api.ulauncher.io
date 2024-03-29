import os
import re
from datetime import datetime
from ext_api.db import db


__version__ = 3
ext_images_bucket_name = os.environ['EXT_IMAGES_BUCKET_NAME']
aws_default_region = os.environ['AWS_DEFAULT_REGION']
object_store_base_url = f'https://{ext_images_bucket_name}.{aws_default_region}.digitaloceanspaces.com'


def run_migration():
    extensions = db.Extensions.find()
    for ext in extensions:
        images = [aws_s3_to_digitalocean_spaces(i) for i in ext.get('Images', [])]
        db.Extensions.update_one({'ID': ext['ID']}, {'$set': {
            'Images': images
        }})
    db.Migrations.insert({'Version': __version__, 'CreatedAt': datetime.utcnow()})


def aws_s3_to_digitalocean_spaces(image_url):
    """
    Converts url like https://stg-ulauncher-ext-images.s3.amazonaws.com/github|1202543/2019-02-23T11:45:41.600354.png
    to https://ulauncher-ext-images-dev.nyc3.digitaloceanspaces.com/github|1202543/2019-02-23T11:45:41.600354.png
    """
    return re.sub(r'^https://[^/]+/(.*)$', fr'{object_store_base_url}/\g<1>', image_url)
