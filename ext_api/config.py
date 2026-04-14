import logging
import os
from typing import Any

import dotenv
from botocore.config import Config

dotenv.load_dotenv()

commit = os.getenv("COMMIT_SHA1", "")
ext_images_bucket_name = os.environ["EXT_IMAGES_BUCKET_NAME"]
aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
aws_default_region = os.environ["AWS_DEFAULT_REGION"]
s3_use_digitalocean = os.environ.get("S3_USE_DIGITALOCEAN", "false").lower() == "true"
s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL")
s3_public_base_url = os.environ.get("S3_PUBLIC_BASE_URL")
s3_addressing_style = os.environ.get("S3_ADDRESSING_STYLE")

s3_https_domain = ".s3.amazonaws.com"
if s3_use_digitalocean:
    s3_https_domain = ".nyc3.digitaloceanspaces.com"
if os.environ.get("S3_HTTPS_DOMAIN"):
    s3_https_domain = os.environ["S3_HTTPS_DOMAIN"]

boto3_resource_cfg: dict[str, Any] = {}
if s3_endpoint_url:
    boto3_resource_cfg = {
        "region_name": aws_default_region,
        "endpoint_url": s3_endpoint_url,
        "aws_access_key_id": aws_access_key_id,
        "aws_secret_access_key": aws_secret_access_key,
    }
elif s3_use_digitalocean:
    object_store_base_url = f"https://{aws_default_region}.digitaloceanspaces.com"
    boto3_resource_cfg = {
        "region_name": aws_default_region,
        "endpoint_url": object_store_base_url,
        "aws_access_key_id": aws_access_key_id,
        "aws_secret_access_key": aws_secret_access_key,
    }

if s3_addressing_style:
    boto3_resource_cfg["config"] = Config(s3={"addressing_style": s3_addressing_style})  # type: ignore[arg-type]

ext_images_public_base_url = s3_public_base_url or f"https://{ext_images_bucket_name}{s3_https_domain}"

github_api_user = os.getenv("GITHUB_API_USER")
github_api_token = os.getenv("GITHUB_API_TOKEN")
github_api_base_url = os.getenv("GITHUB_API_BASE_URL", "https://api.github.com")
github_raw_base_url = os.getenv("GITHUB_RAW_BASE_URL", "https://raw.githubusercontent.com")

mongodb_connection = os.environ["MONGODB_CONNECTION"]
db_name = os.environ["DB_NAME"]

five_mb = 5 * 1024 * 1024
max_image_size = int(os.getenv("MAX_IMAGE_SIZE", str(five_mb)))
max_images_per_uer = int(os.getenv("MAX_IMAGES", "300"))

log_level = int(os.getenv("LOG_LEVEL", str(logging.INFO)))
