import os
import logging
from bottle import default_app, request
from ext_api.auth import bottle_auth_plugin, jwt_auth_required

app = default_app()
app.install(bottle_auth_plugin)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@app.route('/hello', ['GET'])
def hello(*args, **kw):
    logger.info('remote user: %s' % request.get('REMOTE_USER'))
    return serializable_dict(dict(request))


@app.route('/name/<name>/<test>', ['GET', 'POST'])
@app.route('/hello-protected/<name>', ['GET', 'POST'])
@jwt_auth_required
def helloProtected(name, test=None):
    logger.info('remote user: %s' % request['REMOTE_USER'])
    return {'name': name}


@app.route('/items', ['GET', 'OPTIONS'])
def hello():
    return {'items': []}


def serializable_dict(d):
    ret = {}
    for k, v in d.items():
        if isinstance(v, (str, int, float, bool, tuple)):
            ret[k] = v
        elif isinstance(v, dict):
            ret[k] = serializable_dict(v)
        else:
            ret[k] = 'type(%s)' % type(v).__name__

    return ret


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
