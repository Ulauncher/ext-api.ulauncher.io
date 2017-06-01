import os

extensions_table_name = os.environ['EXTENSIONS_TABLE_NAME']
ext_images_bucket_name = os.environ['EXT_IMAGES_BUCKET_NAME']

max_upload_size = 5 * 1024 * 1024  # 5MB
