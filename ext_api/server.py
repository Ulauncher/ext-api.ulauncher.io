import logging
from json import dumps
from itertools import cycle
from urllib.error import HTTPError
from bottle import default_app, request, response, template, FileUpload

from ext_api.helpers.auth import bottle_auth_plugin, jwt_auth_required, AuthError
from ext_api.db.extensions import (put_extension, update_extension, get_extension, get_extensions,
                                   remove_extension_image, add_extension_images,
                                   ExtensionAlreadyExistsError, ExtensionNotFoundError)
from ext_api.github import (get_project_path, get_manifest, validate_manifest,
                            InvalidGithubUrlError, ManifestValidationError)
from ext_api.s3.ext_images import upload_images, delete_image, FileTooLargeError
from ext_api.helpers.s3 import parse_s3_url
from ext_api.helpers.aws import get_url_prefix
from ext_api.helpers.logging import setup_logging
from ext_api.helpers.response import ErrorResponse


app = default_app()
app.install(bottle_auth_plugin)

setup_logging()
logger = logging.getLogger(__name__)

response.content_type = 'application/json'


@app.route('/api-doc.html', method=['GET'])
def api_doc():
    docs_exclude = ["/api-doc.html"]
    colors = cycle('#fff #e3e4ed'.split())
    routes = [r for r in app.routes if r.rule not in docs_exclude]
    return template("api-doc", colors=colors, routes=routes, url_prefix=get_url_prefix())


@app.route('/extensions', ['GET'])
def get_extensions_route():
    """
    Returns all extensions
    """
    return {'data': get_extensions()}


@app.route('/extensions/<id>', ['GET'])
def get_extension_route(id):
    """
    Returns extension by ID
    """
    try:
        return {'data': get_extension(id)}
    except ExtensionNotFoundError as e:
        return ErrorResponse(e, 404)


@app.route('/extensions', ['POST'])
@jwt_auth_required
def create_extension_route():
    """
    Create an extension

    Request params:
    * GithubUrl: string. Example https://github.com/username/projectname

    Response:
    * Extension object:

    <pre>{data: {Name: 'str', Description: 'str': DeveloperName: 'str'}}</pre>
    """
    user = request.get('REMOTE_USER')

    try:
        github_url = request.json.get('GithubUrl', '')
        project_path = get_project_path(github_url)
        manifest = get_manifest(project_path)
        validate_manifest(manifest)
        put_extension(User=user,
                      GithubUrl=github_url,
                      ProjectPath=project_path)

        return {
            'data': {
                'Name': manifest['name'],
                'Description': manifest['description'],
                'DeveloperName': manifest['developer_name'],
            }
        }
    except (InvalidGithubUrlError, HTTPError, ManifestValidationError, ExtensionAlreadyExistsError) as e:
        return ErrorResponse(e, 400)


@app.route('/extensions/<id>', ['PATCH'])
@jwt_auth_required
def update_extension_route(id):
    """
    Update and publish extension

    Request params:
    * ExtName: (string) extension display name
    * Description: (string)
    * DeveloperName: (string)

    Response:
    * Extension object
    """
    user = request.get('REMOTE_USER')
    data = request.json

    try:
        assert data.get('ExtName'), 'Name cannot be empty'
        assert data.get('Description'), 'Description cannot be empty'
        assert data.get('DeveloperName'), 'DeveloperName cannot be empty'

        data = update_extension(id,
                                ExtName=data['ExtName'],
                                Description=data['Description'],
                                DeveloperName=data['DeveloperName'],
                                Published=True)
        return {'data': data}
    except ExtensionNotFoundError as e:
        return ErrorResponse(e, 404)
    except AssertionError as e:
        return ErrorResponse(e, 400)


@app.route('/extensions/<id>/upload.html', ['GET'])
def image_upload_html_route(id):
    """
    HTML page with an upload form

    Query params:
    * token: (string) authorization token
    """
    return template('image_upload', ext_id=id, token=request.GET['token'], url_prefix=get_url_prefix())


@app.route('/extensions/<id>/images', ['POST'])
@jwt_auth_required
def add_extension_image_route(id):
    """
    Add extension image

    Request params:
    * Files uploaded as "multipart/form-data"

    Field names don't matter. Multiple files are supported
    """
    user = request.get('REMOTE_USER')

    files = [item.file for _, item in request.POST.items() if isinstance(item, FileUpload)]
    try:
        ext = _verify_ext_auth(id)
        assert files, "Files were not provided"
        urls = upload_images(files, id)
        data = add_extension_images(id, urls)
        return {'data': data}
    except ExtensionNotFoundError as e:
        return ErrorResponse(e, 404)
    except AssertionError as e:
        return ErrorResponse(e, 400)
    except FileTooLargeError as e:
        return ErrorResponse(e, 413)
    except AuthError as e:
        return ErrorResponse(e, 401)


@app.route('/extensions/<id>/images/<image_idx>', ['DELETE'])
@jwt_auth_required
def delete_extension_image_route(id, image_idx):
    """
    Delete extension image

    <code>image_idx</code> index of an image starting from 0

    Response:
    * Extension object
    """
    user = request.get('REMOTE_USER')
    image_idx = int(image_idx)

    try:
        ext = _verify_ext_auth(id)
        image_url = ext['Images'][image_idx]
        data = remove_extension_image(id, image_idx)
        delete_image(parse_s3_url(image_url)[1])
        return {'data': data}
    except (ExtensionNotFoundError, IndexError) as e:
        return ErrorResponse(e, 404)
    except AuthError as e:
        return ErrorResponse(e, 401)


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
