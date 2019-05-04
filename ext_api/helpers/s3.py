from urllib.parse import urlparse


def parse_s3_url(url):
    """
    >>> parse_s3_url('https://my-bucket.s3.amazonaws.com/my/path.png')
    <<< ('my-bucket', 'my/path.png')
    """

    components = urlparse(url)
    bucket = components.netloc.split('.')[0]
    key = components.path.strip('/')

    return (bucket, key)
