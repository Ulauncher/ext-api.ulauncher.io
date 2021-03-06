import datetime
from pymongo.errors import DuplicateKeyError

from ext_api.db import db
from ext_api.helpers.logging_utils import timeit


@timeit
def put_extension(**item):
    """
    :returns dict: Extension
    """
    if not item.get('ID'):
        id = 'github-%s' % item['ProjectPath'].replace('/', '-').lower()
        item.update({'ID': id})

    if not item.get('CreatedAt'):
        item.update({'CreatedAt': datetime.datetime.utcnow()})

    try:
        db.Extensions.insert_one(item)
    except DuplicateKeyError:
        raise ExtensionAlreadyExistsError('This extension already exists')

    return item


@timeit
def update_extension(id, **data):
    data['UpdatedAt'] = datetime.datetime.utcnow()
    result = db.Extensions.update_one({'ID': id}, {'$set': data})

    if result.modified_count == 0:
        raise ExtensionNotFoundError('Extension "%s" not found' % id)

    return get_extension(id)


@timeit
def delete_extension(id, user=None):
    """
    If user is passed it will also check extension owner
    :raises ExtensionDoesntBelongToUserError:
    """

    if user:
        ext = get_extension(id)
        if ext['User'] != user:
            raise ExtensionDoesntBelongToUserError("Extension '%s' doesn't belong to user" % id)

    result = db.Extensions.delete_one({'ID': id})
    if result.deleted_count == 0:
        raise ExtensionNotFoundError('Extension "%s" not found' % id)


@timeit
def add_extension_images(id, image_urls):
    result = db.Extensions.update_one({'ID': id}, {'$addToSet': {'Images': image_urls}})
    if result.modified_count == 0:
        raise ExtensionNotFoundError('Extension "%s" not found' % id)

    return get_extension(id)


@timeit
def remove_extension_image(id, image_idx):
    result = db.Extensions.update_one({'ID': id}, {'$unset': {"Images.%s" % image_idx: 1}})
    if result.modified_count == 0:
        raise ExtensionNotFoundError('Extension "%s" not found' % id)
    db.Extensions.update_one({'ID': id}, {'$pull': {"Images": None}})

    return get_extension(id)


@timeit
def get_extensions(limit=1000, sort_by='GithubStars', sort_order=-1):
    return db.Extensions.find({'Published': True}).sort(sort_by, sort_order).limit(limit)


@timeit
def get_user_extensions(user, limit=1000):
    return db.Extensions.find({'User': user}).sort('CreatedAt', -1).limit(limit)


@timeit
def get_extension(id):
    result = db.Extensions.find_one({'ID': id})
    if not result:
        raise ExtensionNotFoundError('Extension "%s" not found' % id)

    return result


class ExtensionAlreadyExistsError(Exception):
    pass


class ExtensionNotFoundError(Exception):
    pass


class ExtensionDoesntBelongToUserError(Exception):
    pass
