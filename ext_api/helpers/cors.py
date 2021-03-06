from bottle import request, response
from functools import wraps


def allow_options_requests(callback):
    @wraps(callback)
    def wrapper(*args, **kwargs):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'PATCH, GET, POST, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = \
            'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token, Authorization'

        if request.method.lower() == 'options':
            return
        else:
            return callback(*args, **kwargs)

    return wrapper


def add_options_route(app):

    @app.route("/<url:re:.*>", method=['OPTIONS'])
    def options(url):
        return
