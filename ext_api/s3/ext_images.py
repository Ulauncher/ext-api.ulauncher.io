import datetime
import io
from urllib.parse import urlparse

import boto3

from ext_api.config import boto3_resource_cfg, ext_images_bucket_name, max_image_size, s3_use_digitalocean

s3 = boto3.resource("s3", **boto3_resource_cfg)
image_bucket = s3.Bucket(ext_images_bucket_name)


def get_user_images(user_id):
    return image_bucket.objects.filter(Prefix=f"{user_id}/")


def upload_images(user_id, file_objects):
    """
    Returns a list of S3 URLs
    Raises AssertionError, FileTooLargeError
    """
    images = [validate_image(fileobj) for fileobj in file_objects]
    return [_upload_image(user_id, image) for image in images]


def _upload_image(user_id, fileobj):
    filename = f"{datetime.datetime.utcnow().isoformat()}.png"
    key = f"{user_id}/{filename}"
    image_bucket.upload_fileobj(fileobj, key, ExtraArgs={"ACL": "public-read"})
    if s3_use_digitalocean:
        return f"https://{ext_images_bucket_name}.nyc3.digitaloceanspaces.com/{key}"
    return f"https://{ext_images_bucket_name}.s3.amazonaws.com/{key}"


def delete_image(key):
    image_bucket.delete_objects(Delete={"Objects": [{"Key": key}]})


def delete_images(urls, user_id):
    objects = []
    for url in urls:
        (_, _, filename) = parse_image_url(url)
        objects.append({"Key": f"{user_id}/{filename}"})

    if not objects:
        return

    image_bucket.delete_objects(Delete={"Objects": objects})


def delete_user_images(user_id):
    objects = [{"Key": obj.key} for obj in image_bucket.objects.filter(Prefix=f"{user_id}/")]

    if not objects:
        return

    image_bucket.delete_objects(Delete={"Objects": objects})


def parse_image_url(url):
    """
    Returns tuple (bucket_name, user_id, image_name)
    >>> "https://dev-ulauncher-ext-image.s3.amazonaws.com/github|1202543/2017-06-23T19:09:44.447649.png"
    <<< ('dev-ulauncher-ext-image', 'github|1202543', '2017-06-23T19:09:44.447649.png')
    """
    res = urlparse(url)
    bucket_name = res.hostname.split(".")[0]
    user_id = res.path.split("/")[1]
    filename = res.path.split("/")[2]
    return (bucket_name, user_id, filename)


def validate_image(fileobj):
    """
    Check file size and type
    Returns new file-like object
    """
    buf_size = 8192
    data = b""

    while True:
        buf = fileobj.read(buf_size)
        if not buf:
            break

        data += buf

        if len(data) > max_image_size:
            fileobj.close()
            max_size = max_image_size / (1024 * 1024)
            raise FileTooLargeError(f"File too large (max: {max_size} megabytes)")

    return io.BytesIO(data)


def validate_image_url(url):
    url = str(url)
    if not url:
        msg = "Image URL cannot be empty"
        raise ImageUrlValidationError(msg)

    if not url.startswith(f"https://{ext_images_bucket_name}.s3.amazonaws.com/") and not url.startswith(
        f"https://{ext_images_bucket_name}.nyc3.digitaloceanspaces.com/"
    ):
        msg = "You cannot use external image URLs"
        raise ImageUrlValidationError(msg)


class FileTooLargeError(Exception):
    pass


class ImageUrlValidationError(Exception):
    pass
