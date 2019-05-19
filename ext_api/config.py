import os
import logging

commit = os.getenv('COMMIT_SHA1', '')
deployed_on = os.getenv('BUILD_DATE', '')
extensions_table_name = os.environ['EXTENSIONS_TABLE_NAME']
ext_images_bucket_name = os.environ['EXT_IMAGES_BUCKET_NAME']

github_api_user = os.getenv('GITHUB_API_USER')
github_api_token = os.getenv('GITHUB_API_TOKEN')

mongodb_connection = os.environ['MONGODB_CONNECTION']
db_name = os.environ['DB_NAME']

five_mb = 5 * 1024 * 1024
max_image_size = int(os.getenv('MAX_IMAGE_SIZE', str(five_mb)))
max_images_per_uer = int(os.getenv('MAX_IMAGES', '300'))

log_level = int(os.getenv('LOG_LEVEL', str(logging.WARNING)))
