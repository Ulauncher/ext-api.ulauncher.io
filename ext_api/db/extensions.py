import datetime
from botocore.errorfactory import ClientError
from boto3.dynamodb.conditions import Key, Attr

from ext_api.db.helper import inject_table
from ext_api.config import extensions_table_name

inject_extensions_table = inject_table(extensions_table_name)


@inject_extensions_table
def get_creation_date(table):
    return table.creation_date_time


@inject_extensions_table
def put_extension(table, User, GithubUrl, ProjectPath):
    try:
        return table.put_item(Item={
            'Part': 0,  # we want all the data to be in one partition, so partition key will always be 0
            'ID': 'github-%s' % ProjectPath.replace('/', '-').lower(),
            'User': User,
            'CreatedAt': datetime.datetime.utcnow().isoformat(),
            'GithubUrl': GithubUrl,
            'ProjectPath': ProjectPath,
            'Published': False
        }, ConditionExpression='attribute_not_exists(Part) AND attribute_not_exists(ID)')
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ExtensionAlreadyExistsError('This extension already exists')


@inject_extensions_table
def update_extension(table, id, **data):
    upd_expr = 'set ' + ', '.join(['%s = :%s' % (k, k) for k, _ in data.items()])
    values = dict([(':%s' % k, v) for k, v in data.items()])

    try:
        updated = table.update_item(
            Key={'Part': 0,
                 'ID': id},
            UpdateExpression=upd_expr,
            ExpressionAttributeValues=values,
            ReturnValues='ALL_NEW',
            ConditionExpression='attribute_exists(Part) AND attribute_exists(ID)'
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ExtensionNotFoundError('Extension "%s" not found' % id)

    return _del_unused_item_keys(updated['Attributes'])


@inject_extensions_table
def get_extensions(table, limit=10):
    response = table.query(
        IndexName='CreatedAt-LSI',
        Select='ALL_ATTRIBUTES',
        Limit=limit,
        ConsistentRead=False,
        ScanIndexForward=False,
        KeyConditionExpression=Key('Part').eq(0)
    )
    return [_del_unused_item_keys(i) for i in response['Items']]


@inject_extensions_table
def get_extension(table, ID):
    resp = table.get_item(Key={'Part': 0, 'ID': ID})
    try:
        return _del_unused_item_keys(extresp['Item'])
    except KeyError:
        raise ExtensionNotFoundError('Extension "%s" not found' % ID)


class ExtensionAlreadyExistsError(Exception):
    pass


class ExtensionNotFoundError(Exception):
    pass


def _del_unused_item_keys(item):
    del item['Part']
    return item

if __name__ == '__main__':
    # Print out some data about the table.
    # This will cause a request to be made to DynamoDB and its attribute
    # values will be set based on the response.
    print(get_creation_date())
