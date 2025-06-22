import logging
import os

import dotenv

dotenv.load_dotenv()

commit = os.getenv("COMMIT_SHA1", "")
deployed_on = os.getenv("BUILD_DATE", "")
ext_images_bucket_name = os.environ["EXT_IMAGES_BUCKET_NAME"]
aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
aws_default_region = os.environ["AWS_DEFAULT_REGION"]
s3_use_digitalocean = os.environ.get("S3_USE_DIGITALOCEAN", "false").lower() == "true"
boto3_resource_cfg = dict()
if s3_use_digitalocean:
    object_store_base_url = f"https://{aws_default_region}.digitaloceanspaces.com"
    boto3_resource_cfg = {
        "region_name": aws_default_region,
        "endpoint_url": object_store_base_url,
        "aws_access_key_id": aws_access_key_id,
        "aws_secret_access_key": aws_secret_access_key,
    }

github_api_user = os.getenv("GITHUB_API_USER")
github_api_token = os.getenv("GITHUB_API_TOKEN")

mongodb_connection = os.environ["MONGODB_CONNECTION"]
db_name = os.environ["DB_NAME"]

five_mb = 5 * 1024 * 1024
max_image_size = int(os.getenv("MAX_IMAGE_SIZE", str(five_mb)))
max_images_per_uer = int(os.getenv("MAX_IMAGES", "300"))

log_level = int(os.getenv("LOG_LEVEL", str(logging.INFO)))
