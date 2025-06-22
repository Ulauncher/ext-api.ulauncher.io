#!/usr/bin/env python
import json
import logging
import os
from itertools import cycle
from urllib.error import HTTPError

from bottle import Bottle, FileUpload, JSONPlugin, request, response, template
from bson.json_util import dumps
from nodesemver import satisfies

from ext_api.config import commit, deployed_on, github_api_token, github_api_user, max_images_per_uer
from ext_api.db import check_migration_consistency
from ext_api.github import (
    InvalidGithubUrlError,
    JsonFileNotFoundError,
    ProjectValidationError,
    get_json,
    get_latest_version_commit,
    get_project_path,
    get_repo_info,
    validate_manifest,
)
from ext_api.helpers.auth import AuthError, bottle_auth_plugin, jwt_auth_required
from ext_api.helpers.aws import get_url_prefix
from ext_api.helpers.cors import add_options_route, allow_options_requests
from ext_api.helpers.http_client import http
from ext_api.helpers.logging_utils import bottle_request_logger
from ext_api.helpers.response import ErrorResponse
from ext_api.models.extensions import (
    ExtensionAlreadyExistsError,
    ExtensionDoesntBelongToUserError,
    ExtensionNotFoundError,
    delete_extension,
    get_extension,
    get_extensions,
    get_user_extensions,
    put_extension,
    update_extension,
)
from ext_api.s3.ext_images import (
    FileTooLargeError,
    ImageUrlValidationError,
    delete_images,
    get_user_images,
    upload_images,
    validate_image_url,
)

app = Bottle(autojson=False)
app.install(JSONPlugin(json_dumps=dumps))
app.install(allow_options_requests)
app.install(bottle_auth_plugin)
app.install(bottle_request_logger)
add_options_route(app)

logger = logging.getLogger(__name__)

response.content_type = "application/json"

allowed_sort_by = ["GithubStars", "CreatedAt"]
allowed_sort_order = ["-1", "1"]
HTTP_STATUS_OK = 200


@app.route("/api-doc.html", method=["GET"])
def api_doc():
    docs_exclude = ["/api-doc.html", "/<url:re:.*>"]
    colors = cycle(["#fff", "#e3e4ed"])
    routes = [r for r in app.routes if r.rule not in docs_exclude]
    return template(
        "api-doc", colors=colors, routes=routes, url_prefix=get_url_prefix(), commit=commit, deployed_on=deployed_on
    )


@app.route("/extensions", ["GET"])
def get_extensions_route():
    """
    Returns all extensions

    Query params:
    * api_version: string. Version of Ulauncher Extension API. Returns all extensions by default

    """
    result = []

    # filter by required API version
    api_version = request.GET.get("api_version")
    try:
        sort_by = request.GET.get("sort_by") or allowed_sort_by[0]
        sort_order = request.GET.get("sort_order") or allowed_sort_order[0]
        assert sort_by in allowed_sort_by, "allowed sorty_by: " + ", ".join(allowed_sort_by)
        assert sort_order in allowed_sort_order, "allowed sort_order: " + ", ".join(map(str, allowed_sort_order))
    except AssertionError as e:
        return ErrorResponse(e, 400)

    for ext in get_extensions(sort_by=sort_by, sort_order=int(sort_order)):
        if not api_version:
            result.append(ext)
        for req_version in ext.get("SupportedVersions", []):
            if satisfies(api_version, req_version):
                result.append(ext)  # noqa: PERF401

    return {"data": result}


@app.route("/my/extensions", ["GET"])
@jwt_auth_required
def get_my_extensions_route():
    """
    Returns user's extensions
    """
    user = request.get("REMOTE_USER")
    return {"data": get_user_extensions(user)}


@app.route("/extensions/<id>", ["GET"])
def get_extension_route(id):
    """
    Returns extension by ID
    """
    try:
        return {"data": get_extension(id)}
    except ExtensionNotFoundError as e:
        return ErrorResponse(e, 404)


@app.route("/validate-project", ["GET"])
@jwt_auth_required
def validate_project():
    """
    Checks that versions.json file is valid

    Query params:
    * url: string. Example https://github.com/user/project

    Response:
    * {Name: (str), Description: (str), DeveloperName: (str)}
    """

    try:
        url = request.GET.get("url")
        assert url, 'query argument "url" cannot be empty'
        project_path = get_project_path(url)
        get_repo_info(project_path)
        try:
            versions = get_json(project_path, "master", "versions")
            commit_or_branch = get_latest_version_commit(versions)
        except JsonFileNotFoundError:
            commit_or_branch = "master"
        except json.JSONDecodeError as e:
            return ErrorResponse(ProjectValidationError(f"Error in versions.json: {e!s}"), 400)

        manifest = get_json(project_path, commit_or_branch, "manifest")
        validate_manifest(manifest)

        return {
            "data": {
                "GithubUrl": url,
                "Name": manifest["name"],
                "Description": manifest["description"],
                "DeveloperName": manifest["developer_name"],
            }
        }
    except json.JSONDecodeError as e:
        return ErrorResponse(ProjectValidationError(f"Error in manifest.json: {e!s}"), 400)
    except (InvalidGithubUrlError, HTTPError, ProjectValidationError, AssertionError) as e:
        return ErrorResponse(e, 400)


@app.route("/extensions", ["POST"])
@jwt_auth_required
def create_extension_route():
    """
    Create extension

    Request params:
    * GithubUrl: (string)
    * Name: (string) extension display name
    * Description: (string)
    * DeveloperName: (string)
    * Images: (list) list of image URLs

    Response:
    * Extension object
    """
    user = request.get("REMOTE_USER")
    data = request.json

    try:
        assert data.get("Name"), "Name cannot be empty"
        assert data.get("Description"), "Description cannot be empty"
        assert data.get("DeveloperName"), "DeveloperName cannot be empty"
        assert data.get("GithubUrl"), "GithubUrl cannot be empty"
        assert isinstance(data.get("Images"), list), "Images must be a list of URLs"
        max_screenshots = 5
        assert (
            0 < len(data["Images"]) <= max_screenshots
        ), "You must upload at least 1 (max 5) screenshot of your extension"

        project_path = get_project_path(data["GithubUrl"])
        info = get_repo_info(project_path)
        try:
            versions = get_json(project_path, "master", "versions")
            versions_only = [v["required_api_version"] for v in versions]
            commit_or_branch = get_latest_version_commit(versions)
        except JsonFileNotFoundError:
            commit_or_branch = "master"
            versions_only = ["^1.0.0"]

        manifest = get_json(project_path, commit_or_branch, "manifest")
        validate_manifest(manifest)

        for image_url in data["Images"]:
            validate_image_url(image_url)

        data = put_extension(
            User=user,
            GithubUrl=data["GithubUrl"],
            ProjectPath=project_path,
            Name=data["Name"],
            Description=data["Description"],
            DeveloperName=data["DeveloperName"],
            Images=data["Images"],
            SupportedVersions=versions_only,
            GithubStars=info["stargazers_count"],
            Published=True,
        )
    except (
        AssertionError,
        ImageUrlValidationError,
        InvalidGithubUrlError,
        HTTPError,
        ProjectValidationError,
        ExtensionAlreadyExistsError,
    ) as e:
        return ErrorResponse(e, 400)
    else:
        return {"data": data}


@app.route("/extensions/<id>", ["PATCH"])
@jwt_auth_required
def update_extension_route(id):
    """
    Update extension

    Request params:
    * Name: (string) extension display name
    * Description: (string)
    * DeveloperName: (string)
    * Images: (list) list of image URLs

    Response:
    * Extension object
    """
    user = request.get("REMOTE_USER")
    data = request.json

    try:
        ext = _verify_ext_auth(id)

        assert data.get("Name"), "Name cannot be empty"
        assert data.get("Description"), "Description cannot be empty"
        assert data.get("DeveloperName"), "DeveloperName cannot be empty"
        assert isinstance(data.get("Images"), list), "Images must be a list of URLs"
        max_screenshots = 5
        assert (
            0 < len(data["Images"]) <= max_screenshots
        ), "You must upload at least 1 (max 5) screenshot of your extension"

        for image_url in data["Images"]:
            validate_image_url(image_url)

        to_delete = set(ext["Images"]) - set(data["Images"])
        delete_images(to_delete, user)

        data = update_extension(
            id,
            Name=data["Name"],
            Description=data["Description"],
            DeveloperName=data["DeveloperName"],
            Images=data["Images"],
        )
    except ExtensionNotFoundError as e:
        return ErrorResponse(e, 404)
    except (AssertionError, ImageUrlValidationError) as e:
        return ErrorResponse(e, 400)
    except AuthError as e:
        return ErrorResponse(e, 401)
    else:
        return {"data": data}


@app.route("/extensions/<id>", ["DELETE"])
@jwt_auth_required
def delete_extension_route(id):
    """
    Deletes extension by ID
    """
    user = request.get("REMOTE_USER")
    try:
        ext = _verify_ext_auth(id)
        delete_images(ext["Images"], user)
        delete_extension(id, user=user)
        response.status = 204
    except (ExtensionDoesntBelongToUserError, AuthError) as e:
        return ErrorResponse(e, 401)


@app.route("/upload-images.html", ["GET"])
def upload_images_html_route():
    """
    HTML page with an upload form for testing

    Query params:
    * token: (string) authorization token
    """
    return template("image_upload", token=request.GET["token"], url_prefix=get_url_prefix())


@app.route("/upload-images", ["POST"])
@jwt_auth_required
def upload_images_route():
    """
    Upload images

    Request params:
    * Files uploaded as "multipart/form-data"

    Field names don't matter. Multiple files are supported
    """
    user = request.get("REMOTE_USER")

    files = [item.file for _, item in request.POST.items() if isinstance(item, FileUpload)]
    try:
        assert files, "Files were not provided"
        if len(list(get_user_images(user))) + len(files) > max_images_per_uer:
            raise MaxImageLimitError(f"You cannot upload more than {max_images_per_uer} images")  # noqa: TRY301

        urls = upload_images(user, files)
    except (AssertionError, MaxImageLimitError) as e:
        return ErrorResponse(e, 400)
    except FileTooLargeError as e:
        return ErrorResponse(e, 413)
    else:
        return {"data": urls}


@app.route("/misc/ulauncher-releases/<version>", ["GET"])
def get_ulauncher_release(version):
    """
    Fetches Ulauncher release from Github by given git tag (version)

    Note: This is necessary because Github API limits number of unauthenticated requests and it often blocks
    IPs that Travis CI uses, so Ulauncher releases could fail
    """
    headers = {"User-Agent": "curl/7.47.0"}
    resp = http.request("GET", "https://api.github.com/repos/ulauncher/ulauncher/releases", headers=headers)
    if resp.status != HTTP_STATUS_OK:
        return ErrorResponse(Exception(f"Could not get releases from Github. {resp.data}"), 400)
    releases = json.loads(resp.data)
    try:
        return next(r for r in releases if r["tag_name"] == version)
    except StopIteration:
        return ErrorResponse(Exception(f"Release version {version} not found"), 404)


def _verify_ext_auth(id):
    """
    Verifies if current user can change/delete extension by given ID

    :param str id:
    :raises AuthError:
    :raises ExtensionNotFoundError:

    :returns: dict - extension
    """
    ext = get_extension(id)
    user = request.get("REMOTE_USER")

    if ext["User"] != user:
        msg = "You are not allowed to change extensions of other users"
        raise AuthError(msg)

    return ext


class MaxImageLimitError(Exception):
    pass


def run_server():
    check_migration_consistency()
    port = os.getenv("PORT") or 8080
    if not github_api_token or not github_api_user:
        logger.warning(
            "GITHUB_API_USER and GITHUB_API_TOKEN env vars are not set. "
            "For unauthenticated requests, the rate limit allows for up to 60 requests per hour "
            "(see https://developer.github.com/v3/#rate-limiting)"
        )
    threads = os.getenv("GUNICORN_THREADS")
    if threads:
        app.run(server="gunicorn", host="0.0.0.0", port=port, threads=int(threads), debug=False)
    else:
        app.run(host="0.0.0.0", port=port, debug=True)
