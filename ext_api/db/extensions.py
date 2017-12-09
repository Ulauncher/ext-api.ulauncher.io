import datetime
import boto3
from botocore.errorfactory import ClientError
from boto3.dynamodb.conditions import Key, Attr

from ext_api.helpers.db import inject_table, generate_attrs
from ext_api.helpers.logging import timeit
from ext_api.config import extensions_table_name

inject_extensions_table = inject_table(extensions_table_name)


@timeit
@inject_extensions_table
def get_creation_date(table):
    return table.creation_date_time


@timeit
@inject_extensions_table
def put_extension(table, **item):
    """
    :returns dict: Extension
    """
    id = 'github-%s' % item['ProjectPath'].replace('/', '-').lower()
    try:
        item.update({
            'Part': 0,  # we want all the data to be in one partition, so partition key will always be 0
            'ID': id,
            'CreatedAt': datetime.datetime.utcnow().isoformat(),
        })
        table.put_item(Item=item,
                       ConditionExpression='attribute_not_exists(Part) AND attribute_not_exists(ID)')
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ExtensionAlreadyExistsError('This extension already exists')
        raise

    return _del_unused_item_keys(item)


@timeit
@inject_extensions_table
def update_extension(table, id, **data):
    attrs = generate_attrs(data)

    try:
        updated = table.update_item(
            Key={'Part': 0,
                 'ID': id},
            ExpressionAttributeNames=attrs['ExpressionAttributeNames'],
            ExpressionAttributeValues=attrs['ExpressionAttributeValues'],
            UpdateExpression=attrs['UpdateExpression'],
            ReturnValues='ALL_NEW',
            ConditionExpression='attribute_exists(Part) AND attribute_exists(ID)'
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ExtensionNotFoundError('Extension "%s" not found' % id)
        raise

    return _del_unused_item_keys(updated['Attributes'])


@timeit
@inject_extensions_table
def delete_extension(table, id, user=None):
    """
    If user is passed it will also check belonging it to user

    :raises ExtensionDoesntBelongToUserError:
    """
    kwargs = {
        'Key': {'Part': 0, 'ID': id},
        'ReturnValues': 'ALL_OLD'
    }

    if user:
        kwargs['ConditionExpression'] = Attr('User').eq(user)

    try:
        ext = table.delete_item(**kwargs)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ExtensionDoesntBelongToUserError("Extension '%s' doesn't belong to user" % id)
        raise

    return _del_unused_item_keys(ext['Attributes'])


@timeit
@inject_extensions_table
def add_extension_images(table, id, image_urls):
    updated = table.update_item(
        Key={'Part': 0,
             'ID': id},
        UpdateExpression='SET Images = list_append(Images, :images)',
        ExpressionAttributeValues={':images': image_urls},
        ReturnValues='ALL_NEW'
    )

    return _del_unused_item_keys(updated['Attributes'])


@timeit
@inject_extensions_table
def remove_extension_image(table, id, image_idx):
    updated = table.update_item(
        Key={'Part': 0,
             'ID': id},
        UpdateExpression='REMOVE Images[%s]' % image_idx,
        ReturnValues='ALL_NEW'
    )

    return _del_unused_item_keys(updated['Attributes'])


@timeit
@inject_extensions_table
def get_extensions(table, limit=100):
    response = table.query(
        IndexName='CreatedAt-LSI',
        Select='ALL_ATTRIBUTES',
        Limit=limit,
        ConsistentRead=False,
        ScanIndexForward=False,
        KeyConditionExpression=Key('Part').eq(0)
    )
    return [_del_unused_item_keys(i) for i in response['Items']]


@timeit
@inject_extensions_table
def get_user_extensions(table, user, limit=100):
    response = table.query(
        IndexName='User-LSI',
        Select='ALL_ATTRIBUTES',
        Limit=limit,
        ConsistentRead=False,
        KeyConditionExpression=Key('Part').eq(0) & Key('User').eq(user)
    )
    return [_del_unused_item_keys(i) for i in response['Items']]


@timeit
@inject_extensions_table
def get_extension(table, ID):
    resp = table.get_item(Key={'Part': 0, 'ID': ID})
    try:
        return _del_unused_item_keys(resp['Item'])
    except KeyError:
        raise ExtensionNotFoundError('Extension "%s" not found' % ID)


def create_table():
    dynamodb = boto3.resource('dynamodb')

    table = dynamodb.create_table(
        TableName=extensions_table_name,
        KeySchema=[
            {
                'AttributeName': 'Part',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'ID',
                'KeyType': 'RANGE'  # Sort key
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'Part',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'ID',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'CreatedAt',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'User',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'Rating',
                'AttributeType': 'N'
            },

        ],
        LocalSecondaryIndexes=[
            {
                'IndexName': 'CreatedAt-LSI',
                'KeySchema': [
                    {
                        'AttributeName': 'Part',
                        'KeyType': 'HASH'  # Partition key
                    },
                    {
                        'AttributeName': 'CreatedAt',
                        'KeyType': 'RANGE'  # Sort key
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            },
            {
                'IndexName': 'User-LSI',
                'KeySchema': [
                    {
                        'AttributeName': 'Part',
                        'KeyType': 'HASH'  # Partition key
                    },
                    {
                        'AttributeName': 'User',
                        'KeyType': 'RANGE'  # Sort key
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            },
            {
                'IndexName': 'Rating-LSI',
                'KeySchema': [
                    {
                        'AttributeName': 'Part',
                        'KeyType': 'HASH'  # Partition key
                    },
                    {
                        'AttributeName': 'Rating',
                        'KeyType': 'RANGE'  # Sort key
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5,
        }
    )

    print("Table status:", table.table_status)


class ExtensionAlreadyExistsError(Exception):
    pass


class ExtensionNotFoundError(Exception):
    pass


class ExtensionDoesntBelongToUserError(Exception):
    pass


def _del_unused_item_keys(item):
    del item['Part']
    return item


if __name__ == '__main__':
    try:
        get_creation_date()
    except Exception as e:
        create_table()
