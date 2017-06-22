import logging
from json import dumps
from itertools import cycle
from urllib.error import HTTPError
from bottle import default_app, hook, request, response, template, FileUpload

from ext_api.helpers.auth import bottle_auth_plugin, jwt_auth_required, AuthError
from ext_api.db.extensions import (put_extension, update_extension, get_extension, get_extensions,
                                   get_user_extensions, delete_extension, ExtensionDoesntBelongToUserError,
                                   ExtensionAlreadyExistsError, ExtensionNotFoundError)
from ext_api.github import (get_project_path, get_manifest, validate_manifest,
                            InvalidGithubUrlError, ManifestValidationError)
from ext_api.s3.ext_images import (upload_images, validate_image_url, get_user_images,
                                   ImageUrlValidationError, FileTooLargeError)
from ext_api.helpers.aws import get_url_prefix
from ext_api.helpers.logging import setup_logging
from ext_api.helpers.response import ErrorResponse
from ext_api.helpers.cors import allow_options_requests, add_options_route
from ext_api.config import max_images_per_uer, commit, deployed_on


app = default_app()
app.install(allow_options_requests)
app.install(bottle_auth_plugin)
add_options_route(app)

setup_logging()
logger = logging.getLogger(__name__)

response.content_type = 'application/json'


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


@app.route('/check-manifest', ['GET'])
@jwt_auth_required
def check_ext_manifest_route():
    """
    Check extension manifest

    Query params:
    * url: string. Example https://github.com/user/project

    Response:
    * {Name: (str), Description: (str), DeveloperName: (str)}
    """

    try:
        url = request.GET.get('url')
        assert url, 'query argument "url" cannot be empty'
        project_path = get_project_path(url)
        manifest = get_manifest(project_path)
        validate_manifest(manifest)

        return {
            'data': {
                'GithubUrl': url,
                'Name': manifest['name'],
                'Description': manifest['description'],
                'DeveloperName': manifest['developer_name'],
            }
        }
    except (InvalidGithubUrlError, HTTPError, ManifestValidationError, AssertionError) as e:
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
        assert type(data.get('Images')) is list, 'Images must be a list of URLs'
        assert 0 < len(data['Images']) < 6, 'You must upload at least 1 (max 5) screenshot of your extension'

        project_path = get_project_path(data['GithubUrl'])
        manifest = get_manifest(project_path)
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
                             Published=True)
        return {'data': data}
    except (AssertionError, ImageUrlValidationError, InvalidGithubUrlError, HTTPError, ManifestValidationError,
            ExtensionAlreadyExistsError) as e:
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
        _verify_ext_auth(id)

        assert data.get('Name'), 'Name cannot be empty'
        assert data.get('Description'), 'Description cannot be empty'
        assert data.get('DeveloperName'), 'DeveloperName cannot be empty'
        assert type(data.get('Images')) is list, 'Images must be a list of URLs'
        assert 0 < len(data['Images']) < 6, 'You must upload at least 1 (max 5) screenshot of your extension'

        for image_url in data['Images']:
            validate_image_url(image_url)

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


@app.route('/extensions/<id>', ['DELETE'])
@jwt_auth_required
def delete_extension_route(id):
    """
    Deletes extension by ID
    """
    user = request.get('REMOTE_USER')
    try:
        ext = delete_extension(id, user=user)
    except ExtensionDoesntBelongToUserError as e:
        return ErrorResponse(e, 401)


@app.route('/upload-image.html', ['GET'])
def upload_image_html_route():
    """
    HTML page with an upload form for testing

    Query params:
    * token: (string) authorization token
    """
    return template('image_upload', token=request.GET['token'], url_prefix=get_url_prefix())


@app.route('/upload-image', ['POST'])
@jwt_auth_required
def upload_image_route():
    """
    Upload an image

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


# @app.route('/environ', ['GET'])
# @jwt_auth_required
# def print_environ_route():

#     def serializable(d):
#         res = {}
#         for k, v in d.items():
#             if isinstance(v, (str, float, int, tuple, list)):
#                 res[k] = v
#             elif isinstance(v, dict):
#                 res[k] = serializable(v)
#             else:
#                 res[k] = 'type(%s)' % type(v).__name__
#         return res

#     return serializable(request.environ)


class MaxImageLimitError(Exception):
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
