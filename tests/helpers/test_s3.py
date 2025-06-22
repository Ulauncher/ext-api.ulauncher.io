from ext_api.helpers.s3 import parse_s3_url


def test_parse_s3_url():
    assert parse_s3_url("https://my-bucket.s3.amazonaws.com/my/path.png") == ("my-bucket", "my/path.png")
