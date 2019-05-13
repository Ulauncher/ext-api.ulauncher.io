#!/usr/bin/env python
import logging
import json
from itertools import cycle
from urllib.error import HTTPError
from bson.json_util import dumps
from bottle import Bottle, request, response, template, FileUpload, JSONPlugin

from ext_api.helpers.auth import bottle_auth_plugin, jwt_auth_required, AuthError
from ext_api.models.extensions import (put_extension, update_extension, get_extension, get_extensions,
                                       get_user_extensions, delete_extension, ExtensionDoesntBelongToUserError,
                                       ExtensionAlreadyExistsError, ExtensionNotFoundError)
from ext_api.github import (get_project_path, InvalidGithubUrlError,
                            get_json, get_latest_version_commit,
                            validate_manifest, ProjectValidationError)
from ext_api.s3.ext_images import (upload_images, validate_image_url, get_user_images, delete_images,
                                   ImageUrlValidationError, FileTooLargeError)
from ext_api.helpers.aws import get_url_prefix
from ext_api.helpers.http_client import http
from ext_api.db import check_migration_consistency
from ext_api.helpers.response import ErrorResponse
from ext_api.helpers.cors import allow_options_requests, add_options_route
from ext_api.config import max_images_per_uer, commit, deployed_on


app = Bottle(autojson=False)
app.install(JSONPlugin(json_dumps=dumps))
app.install(allow_options_requests)
app.install(bottle_auth_plugin)
add_options_route(app)

logger = logging.getLogger(__name__)

response.content_type = 'application/json'

# pylint: disable=no-member,unsubscriptable-object


@app.route('/api-doc.html', method=['GET'])
def api_doc():
    docs_exclude = ["/api-doc.html", "/<url:re:.*>"]
    colors = cycle('#fff #e3e4ed'.split())
    routes = [r for r in app.routes if r.rule not in docs_exclude]
    return template("api-doc", colors=colors, routes=routes, url_prefix=get_url_prefix(),
                    commit=commit, deployed_on=deployed_on)


@app.route('/extensions', ['GET'])
def get_extensions_route():
    """
    Returns all extensions
    """
    return {'data': get_extensions()}


@app.route('/my/extensions', ['GET'])
@jwt_auth_required
def get_my_extensions_route():
    """
    Returns user's extensions
    """
    user = request.get('REMOTE_USER')
    return {'data': get_user_extensions(user)}


@app.route('/extensions/<id>', ['GET'])
def get_extension_route(id):
    """
    Returns extension by ID
    """
    try:
        return {'data': get_extension(id)}
    except ExtensionNotFoundError as e:
        return ErrorResponse(e, 404)


@app.route('/validate-project', ['GET'])
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
        url = request.GET.get('url')
        assert url, 'query argument "url" cannot be empty'
        project_path = get_project_path(url)
        versions = get_json(project_path, 'master', 'versions')
        commit_or_branch = get_latest_version_commit(versions)
        manifest = get_json(project_path, commit_or_branch, 'manifest')
        validate_manifest(manifest)

        return {
            'data': {
                'GithubUrl': url,
                'Name': manifest['name'],
                'Description': manifest['description'],
                'DeveloperName': manifest['developer_name'],
            }
        }
    except (InvalidGithubUrlError, HTTPError, ProjectValidationError, AssertionError) as e:
        return ErrorResponse(e, 400)


@app.route('/extensions', ['POST'])
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
    user = request.get('REMOTE_USER')
    data = request.json

    try:
        assert data.get('Name'), 'Name cannot be empty'
        assert data.get('Description'), 'Description cannot be empty'
        assert data.get('DeveloperName'), 'DeveloperName cannot be empty'
        assert data.get('GithubUrl'), 'GithubUrl cannot be empty'
        assert isinstance(data.get('Images'), list), 'Images must be a list of URLs'
        # pylint: disable=len-as-condition
        assert 0 < len(data['Images']) < 6, 'You must upload at least 1 (max 5) screenshot of your extension'

        project_path = get_project_path(data['GithubUrl'])
        versions = get_json(project_path, 'master', 'versions')
        versions_only = [v['required_api_version'] for v in versions]
        commit_or_branch = get_latest_version_commit(versions)
        manifest = get_json(project_path, commit_or_branch, 'manifest')
        validate_manifest(manifest)

        for image_url in data['Images']:
            validate_image_url(image_url)

        data = put_extension(User=user,
                             GithubUrl=data['GithubUrl'],
                             ProjectPath=project_path,
                             Name=data['Name'],
                             Description=data['Description'],
                             DeveloperName=data['DeveloperName'],
                             Images=data['Images'],
                             SupportedVersions=versions_only,
                             Published=True)
        return {'data': data}
    except (AssertionError, ImageUrlValidationError, InvalidGithubUrlError, HTTPError,
            ProjectValidationError, ExtensionAlreadyExistsError) as e:
        return ErrorResponse(e, 400)


@app.route('/extensions/<id>', ['PATCH'])
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
    user = request.get('REMOTE_USER')
    data = request.json

    try:
        ext = _verify_ext_auth(id)

        assert data.get('Name'), 'Name cannot be empty'
        assert data.get('Description'), 'Description cannot be empty'
        assert data.get('DeveloperName'), 'DeveloperName cannot be empty'
        assert isinstance(data.get('Images'), list), 'Images must be a list of URLs'
        # pylint: disable=len-as-condition
        assert 0 < len(data['Images']) < 6, 'You must upload at least 1 (max 5) screenshot of your extension'

        for image_url in data['Images']:
            validate_image_url(image_url)

        to_delete = set(ext['Images']) - set(data['Images'])
        delete_images(to_delete, user)

        data = update_extension(id,
                                Name=data['Name'],
                                Description=data['Description'],
                                DeveloperName=data['DeveloperName'],
                                Images=data['Images'])
        return {'data': data}
    except ExtensionNotFoundError as e:
        return ErrorResponse(e, 404)
    except (AssertionError, ImageUrlValidationError) as e:
        return ErrorResponse(e, 400)
    except AuthError as e:
        return ErrorResponse(e, 401)


# pylint: disable=inconsistent-return-statements
@app.route('/extensions/<id>', ['DELETE'])
@jwt_auth_required
def delete_extension_route(id):
    """
    Deletes extension by ID
    """
    user = request.get('REMOTE_USER')
    try:
        ext = _verify_ext_auth(id)
        delete_images(ext['Images'], user)
        delete_extension(id, user=user)
        response.status = 204
    except (ExtensionDoesntBelongToUserError, AuthError) as e:
        return ErrorResponse(e, 401)


@app.route('/upload-images.html', ['GET'])
def upload_images_html_route():
    """
    HTML page with an upload form for testing

    Query params:
    * token: (string) authorization token
    """
    return template('image_upload', token=request.GET['token'], url_prefix=get_url_prefix())


@app.route('/upload-images', ['POST'])
@jwt_auth_required
def upload_images_route():
    """
    Upload images

    Request params:
    * Files uploaded as "multipart/form-data"

    Field names don't matter. Multiple files are supported
    """
    user = request.get('REMOTE_USER')

    files = [item.file for _, item in request.POST.items() if isinstance(item, FileUpload)]
    try:
        assert files, "Files were not provided"
        if len(list(get_user_images(user))) + len(files) > max_images_per_uer:
            raise MaxImageLimitError('You cannot upload more than %s images' % max_images_per_uer)
        urls = upload_images(user, files)
        return {'data': urls}
    except (AssertionError, MaxImageLimitError) as e:
        return ErrorResponse(e, 400)
    except FileTooLargeError as e:
        return ErrorResponse(e, 413)


@app.route('/misc/ulauncher-releases/<version>', ['GET'])
def get_ulauncher_release(version):
    """
    Fetches Ulauncher release from Github by given git tag (version)

    Note: This is necessary because Github API limits number of unauthenticated requests and it often blocks
    IPs that Travis CI uses, so Ulauncher releases could fail
    """
    headers = {'User-Agent': 'curl/7.47.0'}
    resp = http.request('GET', 'https://api.github.com/repos/ulauncher/ulauncher/releases', headers=headers)
    if resp.status != 200:
        return ErrorResponse(Exception('Could not get releases from Github. %s' % resp.data), 400)
    releases = json.loads(resp.data)
    try:
        return next((r for r in releases if r['tag_name'] == version))
    except StopIteration:
        return ErrorResponse(Exception('Release version %s not found' % version), 404)


def _verify_ext_auth(id):
    """
    Verifies if current user can change/delete extension by given ID

    :param str id:
    :raises AuthError:
    :raises ExtensionNotFoundError:

    :returns: dict - extension
    """
    ext = get_extension(id)
    user = request.get('REMOTE_USER')

    if ext['User'] != user:
        raise AuthError('You are not allowed to change extensions of other users')

    return ext


class MaxImageLimitError(Exception):
    pass


def run_server():
    check_migration_consistency()
    app.run(host='0.0.0.0', port=8080, debug=True)
