import logging
from json import dumps
from itertools import cycle
from urllib.error import HTTPError
from bottle import default_app, request, response, template

from ext_api.auth import bottle_auth_plugin, jwt_auth_required
from ext_api.db.extensions import (put_extension, update_extension,
                                   ExtensionAlreadyExistsError, ExtensionNotFoundError)
from ext_api.github import (get_project_path, get_manifest, validate_manifest,
                            InvalidGithubUrlError, ManifestValidationError)


app = default_app()
app.install(bottle_auth_plugin)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

response.content_type = 'application/json'
docs_exclude = ["/api-doc"]


@app.route('/api-doc', method=['GET'])
def api_doc():
    colors = cycle('#fff #e3e4ed'.split())
    routes = [r for r in app.routes if r.rule not in docs_exclude]
    return template("api-doc", colors=colors, routes=routes)


@app.route('/extensions', ['POST'])
@jwt_auth_required
def create_extension_route():
    """
    Create Extension

    params:
    - GithubUrl: string. Example https://github.com/username/projectname
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
            'Name': manifest['name'],
            'Description': manifest['description'],
            'DeveloperName': manifest['developer_name'],
        }
    except (InvalidGithubUrlError, HTTPError, ManifestValidationError, ExtensionAlreadyExistsError) as e:
        response.status = 400
        return {'message': str(e)}


@app.route('/extensions/<id>', ['PATCH'])
@jwt_auth_required
def update_extension_route(id):
    """
    Update and Publish Extension

    params:
    - ExtName: (string) extension display name
    - Description: (string)
    - DeveloperName: (string)
    """
    user = request.get('REMOTE_USER')
    logger.info('PATCH /extensions : %s : %s' % (user, dumps(request.json)))
    data = request.json

    try:
        assert data.get('ExtName'), 'Name cannot be empty'
        assert data.get('Description'), 'Description cannot be empty'
        assert data.get('DeveloperName'), 'DeveloperName cannot be empty'

        return update_extension(id,
                                ExtName=data['ExtName'],
                                Description=data['Description'],
                                DeveloperName=data['DeveloperName'],
                                Published=True)
    except ExtensionNotFoundError as e:
        response.status = 404
        return {'message': str(e)}
    except AssertionError as e:
        response.status = 400
        return {'message': str(e)}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
