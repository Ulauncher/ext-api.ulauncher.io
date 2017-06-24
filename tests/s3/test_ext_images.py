from ext_api.s3.ext_images import parse_image_url


def test_parse_image_url():
    url = "https://dev-ulauncher-ext-image.s3.amazonaws.com/github|1202543/2017-06-23T19:09:44.447649.png"
    assert parse_image_url(url) == ('dev-ulauncher-ext-image', 'github|1202543', '2017-06-23T19:09:44.447649.png')
