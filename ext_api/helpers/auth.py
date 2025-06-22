import os
from functools import lru_cache

import jwt
from bottle import request
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate

from ext_api.helpers.http_client import http
from ext_api.helpers.response import ErrorResponse

AUTH0_DOMAIN = os.environ["AUTH0_DOMAIN"]
AUTH0_CLIENT_ID = os.environ["AUTH0_CLIENT_ID"]

HTTP_OK = 200


@lru_cache(maxsize=1)
def get_signing_key():
    """
    get key and cache forever in memory
    """
    resp = http.request("GET", f"https://{AUTH0_DOMAIN}/pem")
    if resp.status != HTTP_OK:
        raise Exception(f"Could not download auth0 cert. {resp.data}")
    cert_obj = load_pem_x509_certificate(resp.data, default_backend())
    return cert_obj.public_key()


def parse_token(token):
    try:
        assert token, "Token is empty"
        if " " in token:
            # this is an Authorization header. Take string after space
            token = token.split(" ")[1]

        return jwt.decode(token, get_signing_key(), audience=AUTH0_CLIENT_ID, algorithms=["RS256"])
    except Exception as e:
        raise AuthError(f"Unauthorized. {e}") from e


class AuthError(Exception):
    pass


def bottle_auth_plugin(callback):

    def wrapper(*args, **kwargs):
        if hasattr(callback, "auth_required") and not request.get("REMOTE_USER"):
            try:
                decoded = parse_token(request.get_header("Authorization"))
                assert decoded["sub"]
            except AuthError as e:
                return ErrorResponse(e, 401)

            request["REMOTE_USER"] = decoded["sub"]

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
    callable_obj.auth_required = True

    return callable_obj
