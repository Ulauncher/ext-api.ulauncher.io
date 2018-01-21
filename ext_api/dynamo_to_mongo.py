from pprint import pprint
from dateutil import parser
from ext_api.models.extensions import put_extension
from ext_api.dynamodb.extensions import get_extensions


def migrate():
    for ext in get_extensions():
        ext['CreatedAt'] = parser.parse(ext['CreatedAt'])
        pprint(ext)
        put_extension(**ext)
