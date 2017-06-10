import io
import datetime
import boto3
from ext_api.config import ext_images_bucket_name, max_image_size

s3 = boto3.resource('s3')
image_bucket = s3.Bucket(ext_images_bucket_name)


def upload_images(file_objects, ext_id):
    """
    Returns a list of S3 URLs
    Raises AssertionError, FileTooLargeError
    """
    images = [validate_image(fileobj) for fileobj in file_objects]
    urls = []
    for image in images:
        urls.append(_upload_image(image, ext_id))

    return urls


def _upload_image(fileobj, ext_id):
    filename = '%s.png' % datetime.datetime.utcnow().isoformat()
    key = '%s/%s' % (ext_id, filename)
    image_bucket.upload_fileobj(fileobj,
                                key,
                                ExtraArgs={'ACL': 'public-read'})

    return 'https://%s.s3.amazonaws.com/%s' % (bucket_name, key)


def delete_image(key):
    image_bucket.delete_objects(Delete={'Objects': [{'Key': key}]})


def delete_images(ext_id):
    objects = []
    for obj in image_bucket.objects.filter(Prefix='%s/' % ext_id):
        objects.append({'Key': obj.key})

    if not objects:
        return

    image_bucket.delete_objects(Delete={'Objects': objects})


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


class FileTooLargeError(Exception):
    pass
