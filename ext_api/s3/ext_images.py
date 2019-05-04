import io
import datetime
from urllib.parse import urlparse

import boto3
from ext_api.config import ext_images_bucket_name, max_image_size

s3 = boto3.resource('s3')
image_bucket = s3.Bucket(ext_images_bucket_name)


def get_user_images(user_id):
    return image_bucket.objects.filter(Prefix='%s/' % user_id)


def upload_images(user_id, file_objects):
    """
    Returns a list of S3 URLs
    Raises AssertionError, FileTooLargeError
    """
    images = [validate_image(fileobj) for fileobj in file_objects]
    urls = []
    for image in images:
        urls.append(_upload_image(user_id, image))

    return urls


def _upload_image(user_id, fileobj):
    filename = '%s.png' % datetime.datetime.utcnow().isoformat()
    key = '%s/%s' % (user_id, filename)
    image_bucket.upload_fileobj(fileobj,
                                key,
                                ExtraArgs={'ACL': 'public-read'})

    return 'https://%s.s3.amazonaws.com/%s' % (ext_images_bucket_name, key)


def delete_image(key):
    image_bucket.delete_objects(Delete={'Objects': [{'Key': key}]})


def delete_images(urls, user_id):
    objects = []
    for url in urls:
        (_, _, filename) = parse_image_url(url)
        objects.append({'Key': '%s/%s' % (user_id, filename)})

    if not objects:
        return

    image_bucket.delete_objects(Delete={'Objects': objects})


def delete_user_images(user_id):
    objects = []
    for obj in image_bucket.objects.filter(Prefix='%s/' % user_id):
        objects.append({'Key': obj.key})

    if not objects:
        return

    image_bucket.delete_objects(Delete={'Objects': objects})


def parse_image_url(url):
    """
    Returns tuple (bucket_name, user_id, image_name)
    >>> "https://dev-ulauncher-ext-image.s3.amazonaws.com/github|1202543/2017-06-23T19:09:44.447649.png"
    <<< ('dev-ulauncher-ext-image', 'github|1202543', '2017-06-23T19:09:44.447649.png')
    """
    res = urlparse(url)
    bucket_name = res.hostname.split('.')[0]
    user_id = res.path.split('/')[1]
    filename = res.path.split('/')[2]
    return (bucket_name, user_id, filename)


def validate_image(fileobj):
    """
    Check file size and type
    Returns new file-like object
    """
    buf_size = 8192
    data = b''

    while True:
        buf = fileobj.read(buf_size)
        if not buf:
            break

        data += buf

        if len(data) > max_image_size:
            fileobj.close()
            raise FileTooLargeError('File too large (max: %d megabytes)' % (max_image_size / (1024 * 1024)))

    return io.BytesIO(data)


def validate_image_url(url):
    url = str(url)
    if not url:
        raise ImageUrlValidationError('Image URL cannot be empty')
    if not url.startswith('https://%s.s3.amazonaws.com/' % ext_images_bucket_name):
        raise ImageUrlValidationError('You cannot use external image URLs')


class FileTooLargeError(Exception):
    pass


class ImageUrlValidationError(Exception):
    pass
