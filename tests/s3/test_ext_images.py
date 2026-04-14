from ext_api.config import ext_images_bucket_name, ext_images_public_base_url
from ext_api.s3.ext_images import parse_image_url


def test_parse_image_url():
    url = f"{ext_images_public_base_url.rstrip('/')}/github|1202543/2017-06-23T19:09:44.447649.png"
    assert parse_image_url(url) == (ext_images_bucket_name, "github|1202543", "2017-06-23T19:09:44.447649.png")
