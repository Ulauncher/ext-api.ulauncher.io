import logging
from json import dumps
from urllib.error import HTTPError
from bottle import default_app, request, response

from ext_api.auth import bottle_auth_plugin, jwt_auth_required
from ext_api.db.extensions import put_extension
from ext_api.github import (get_project_path, get_manifest, validate_manifest,
                            InvalidGithubUrlError, ManifestValidationError)


app = default_app()
app.install(bottle_auth_plugin)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

response.content_type = 'application/json'


@app.route('/extensions', ['POST'])
@jwt_auth_required
def create_extension():
    user = request.get('REMOTE_USER')
    logger.info('POST /extensions : %s : %s' % (user, dumps(request.json)))

    try:
        github_url = request.json.get('github_url', '')
        project_path = get_project_path(github_url)
        manifest = get_manifest(project_path)
        validate_manifest(manifest)
        put_extension(User=user,
                      GithubUrl=github_url,
                      ProjectPath=project_path)

        return manifest
    except InvalidGithubUrlError:
        response.status = 400
        return {'message': 'Invalid Github URL'}
    except (HTTPError, ManifestValidationError) as e:
        response.status = 400
        return {'message': str(e)}


@app.route('/hello', ['GET'])
def hello(*args, **kw):
    logger.info('remote user: %s' % request.get('REMOTE_USER'))
    return request.get('REMOTE_USER')


@app.route('/name/<name>/<test>', ['GET', 'POST'])
@app.route('/hello-protected/<name>', ['GET', 'POST'])
@jwt_auth_required
def helloProtected(name, test=None):
    logger.info('remote user: %s' % request['REMOTE_USER'])
    return {'name': name}


@app.route('/items', ['GET', 'OPTIONS'])
def hello():
    return {'items': []}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
