import boto3
from functools import wraps


def inject_table(table_name):

    def fn_wrapper(fn):
        """
        Decorates fn and injects table as a first argument
        """

        @wraps(fn)
        def wrapper(*args, **kw):
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table(table_name)

            return fn(table, *args, **kw)

        setattr(wrapper, 'original', fn)

        return wrapper

    return fn_wrapper
