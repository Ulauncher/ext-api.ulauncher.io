import os
import logging

commit = ''
deployed_on = ''
extensions_table_name = os.environ['EXTENSIONS_TABLE_NAME']
ext_images_bucket_name = os.environ['EXT_IMAGES_BUCKET_NAME']

five_mb = 5 * 1024 * 1024
max_image_size = int(os.getenv('MAX_IMAGE_SIZE', five_mb))
max_images_per_uer = int(os.getenv('MAX_IMAGES', 300))

log_level = int(os.getenv('LOG_LEVEL', logging.WARNING))
