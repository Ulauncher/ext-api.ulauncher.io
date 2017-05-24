import os
import jwt
import json
from bottle import request, response


AUTH0_CLIENT_ID = os.environ['AUTH0_CLIENT_ID']
AUTH0_CLIENT_SECRET = os.environ['AUTH0_CLIENT_SECRET']


def parse_token(token):
    try:
        assert token, "Token is empty"
        if ' ' in token:
            # this is an Authorization header. Take string after space
            token = token.split(' ')[1]

        return jwt.decode(token, AUTH0_CLIENT_SECRET, audience=AUTH0_CLIENT_ID)
    except Exception as e:
        raise AuthError(e)


class AuthError(Exception):
    pass


def bottle_auth_plugin(callback):

    def wrapper(*args, **kwargs):
        if hasattr(callback, 'auth_required') and not request.get('REMOTE_USER'):
            try:
                decoded = parse_token(request.get_header('Authorization'))
                assert decoded['sub']
            except AuthError as e:
                response.content_type = 'application/json'
                response.status = 401
                return {'message': 'Unauthorized. %s' % e}

            request['REMOTE_USER'] = decoded['sub']

        return callback(*args, **kwargs)

    return wrapper


def jwt_auth_required(callable_obj):
    """A decorator that signs a callable object with an 'auth_required'
    attribute (True). We use this attribute to find which handler callbacks
    require an authorized for protected access.
    Args:
        callable_obj (instance): A handler callable object.
    Returns:
        The callable object.
    """
    setattr(callable_obj, 'auth_required', True)

    return callable_obj
