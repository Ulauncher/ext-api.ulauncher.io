import datetime
from typing import Any, TypedDict

from pymongo.errors import DuplicateKeyError

from ext_api.db import extension_collection
from ext_api.entities import Extension
from ext_api.helpers.logging_utils import timeit


@timeit
def put_extension(item: Extension) -> Extension:
    """
    :returns dict: Extension
    """
    if not item.get("ID"):
        id = "github-{}".format(item["ProjectPath"].replace("/", "-").lower())
        item.update({"ID": id})

    if not item.get("CreatedAt"):
        item.update({"CreatedAt": datetime.datetime.now(datetime.UTC)})

    try:
        extension_collection.insert_one(item)
    except DuplicateKeyError as e:
        msg = "This extension already exists"
        raise ExtensionAlreadyExistsError(msg) from e

    return item


@timeit
def update_extension(id: str, data: dict[str, Any]) -> Extension:
    data["UpdatedAt"] = datetime.datetime.now(datetime.UTC)
    result = extension_collection.update_one({"ID": id}, {"$set": data})

    if result.modified_count == 0:
        raise ExtensionNotFoundError(f'Extension "{id}" not found')

    return get_extension(id)


@timeit
def delete_extension(id: str, user: str | None = None):
    """
    If user is passed it will also check extension owner
    :raises ExtensionDoesntBelongToUserError:
    """

    if user:
        ext = get_extension(id)
        if ext["User"] != user:
            raise ExtensionDoesntBelongToUserError(f"Extension '{id}' doesn't belong to user")

    result = extension_collection.delete_one({"ID": id})
    if result.deleted_count == 0:
        raise ExtensionNotFoundError(f'Extension "{id}" not found')


@timeit
def add_extension_images(id: str, image_urls: list[str]):
    result = extension_collection.update_one({"ID": id}, {"$addToSet": {"Images": image_urls}})
    if result.modified_count == 0:
        raise ExtensionNotFoundError(f'Extension "{id}" not found')

    return get_extension(id)


@timeit
def remove_extension_image(id: str, image_idx: list[str]):
    result = extension_collection.update_one({"ID": id}, {"$unset": {f"Images.{image_idx}": 1}})
    if result.modified_count == 0:
        raise ExtensionNotFoundError(f'Extension "{id}" not found')
    extension_collection.update_one({"ID": id}, {"$pull": {"Images": None}})

    return get_extension(id)


class GetExtensionsResult(TypedDict):
    data: list[Extension]
    has_more: bool


@timeit
def get_extensions(
    limit: None | int = 1000,
    offset: int = 0,
    sort_by: str = "GithubStars",
    sort_order: int = -1,
    versions: list[str] | None = None,
) -> GetExtensionsResult:
    query: dict[str, Any] = {"Published": True}

    if versions:
        query["SupportedVersions"] = {"$in": versions}

    cursor = extension_collection.find(query).sort(sort_by, sort_order).skip(offset)

    if limit:
        cursor = cursor.limit(limit + 1)

    found = list(cursor)

    return GetExtensionsResult(
        data=found[:limit] if limit else found,
        has_more=len(found) > limit if limit else False,
    )


@timeit
def get_user_extensions(user: str, limit: int = 1000):
    return extension_collection.find({"User": user}).sort("CreatedAt", -1).limit(limit)


@timeit
def get_extension(id: str):
    result = extension_collection.find_one({"ID": id})
    if not result:
        raise ExtensionNotFoundError(f'Extension "{id}" not found')

    return result


class ExtensionAlreadyExistsError(Exception):
    pass


class ExtensionNotFoundError(Exception):
    pass


class ExtensionDoesntBelongToUserError(Exception):
    pass
