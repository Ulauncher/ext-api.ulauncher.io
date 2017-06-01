import logging
from json import dumps
from itertools import cycle
from urllib.error import HTTPError
from bottle import default_app, request, response, template, FileUpload

from ext_api.auth import bottle_auth_plugin, jwt_auth_required
from ext_api.db.extensions import (put_extension, update_extension,
                                   ExtensionAlreadyExistsError, ExtensionNotFoundError)
from ext_api.github import (get_project_path, get_manifest, validate_manifest,
                            InvalidGithubUrlError, ManifestValidationError)
from ext_api.ext_images import upload_images, FileTooLargeError


app = default_app()
app.install(bottle_auth_plugin)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

response.content_type = 'application/json'
docs_exclude = ["/api-doc.html"]


@app.route('/api-doc.html', method=['GET'])
def api_doc():
    colors = cycle('#fff #e3e4ed'.split())
    routes = [r for r in app.routes if r.rule not in docs_exclude]
    return template("api-doc", colors=colors, routes=routes)


@app.route('/extensions', ['POST'])
@jwt_auth_required
def create_extension_route():
    """
    Create an extension

    Request params:
    * GithubUrl: string. Example https://github.com/username/projectname

    Response:
    <pre>{data: {Name: 'str', Description: 'str': DeveloperName: 'str'}}</pre>
    """
    user = request.get('REMOTE_USER')
    logger.info('POST /extensions : %s : %s' % (user, dumps(request.json)))

    try:
        github_url = request.json.get('GithubUrl', '')
        project_path = get_project_path(github_url)
        manifest = get_manifest(project_path)
        validate_manifest(manifest)
        put_extension(User=user,
                      GithubUrl=github_url,
                      ProjectPath=project_path)

        return {
            data: {
                'Name': manifest['name'],
                'Description': manifest['description'],
                'DeveloperName': manifest['developer_name'],
            }
        }
    except (InvalidGithubUrlError, HTTPError, ManifestValidationError, ExtensionAlreadyExistsError) as e:
        response.status = 400
        return {'error': str(e)}


@app.route('/extensions/<id>', ['PATCH'])
@jwt_auth_required
def update_extension_route(id):
    """
    Update and publish extension

    Request params:
    * ExtName: (string) extension display name
    * Description: (string)
    * DeveloperName: (string)
    """
    user = request.get('REMOTE_USER')
    logger.info('PATCH /extensions : %s : %s' % (user, dumps(request.json)))
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
        response.status = 404
        return {'error': str(e)}
    except AssertionError as e:
        response.status = 400
        return {'error': str(e)}


@app.route('/extensions/<id>/upload.html', ['GET'])
def image_upload_html_route(id):
    """
    HTML page with an upload form

    Query params:
    * token: (string) authorization token
    """
    return template('image_upload', ext_id=id, token=request.GET['token'])


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
    logger.info('POST /extensions/<id>/images : %s : %s' % (user, dumps(request.json)))

    files = [item.file for _, item in request.POST.items() if isinstance(item, FileUpload)]
    try:
        # TODO: check if extension belongs to the user
        assert files, "Files were not provided"
        urls = upload_images(files, id)
        return {'data': urls}
    except AssertionError as e:
        response.status = 400
        return {'error': str(e)}
    except FileTooLargeError as e:
        response.status = 413
        return {'error': str(e)}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
