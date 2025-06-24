import os
from collections.abc import Callable
from functools import lru_cache
from typing import ParamSpec, TypeVar

import jwt
from bottle import request
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import load_pem_x509_certificate

from ext_api.helpers.http_client import http
from ext_api.helpers.response import ErrorResponse

AUTH0_DOMAIN = os.environ["AUTH0_DOMAIN"]
AUTH0_CLIENT_ID = os.environ["AUTH0_CLIENT_ID"]

HTTP_OK = 200


@lru_cache(maxsize=1)
def get_signing_key() -> rsa.RSAPublicKey:
    """
    get key and cache forever in memory
    """
    resp = http.request("GET", f"https://{AUTH0_DOMAIN}/pem")
    if resp.status != HTTP_OK:
        raise Exception(f"Could not download auth0 cert. {resp.data}")
    cert_obj = load_pem_x509_certificate(resp.data, default_backend())
    pkey = cert_obj.public_key()

    if not isinstance(pkey, rsa.RSAPublicKey):
        msg = "Auth0 public key is not an RSA key"
        raise TypeError(msg)

    return pkey


def parse_token(token: str) -> dict[str, str]:
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


Param = ParamSpec("Param")
RetType = TypeVar("RetType")


def bottle_auth_plugin[**Param, RetType](
    callback: Callable[Param, RetType],
) -> Callable[Param, RetType | ErrorResponse]:
    def wrapper(*args: Param.args, **kwargs: Param.kwargs) -> RetType | ErrorResponse:
        remote_user = request.get("REMOTE_USER")
        auth_header = request.get_header("Authorization")
        if hasattr(callback, "auth_required") and not remote_user:
            try:
                decoded = parse_token(auth_header)
                assert decoded["sub"]
            except AuthError as e:
                return ErrorResponse(e, 401)

            request["REMOTE_USER"] = decoded["sub"]

        return callback(*args, **kwargs)

    return wrapper


def jwt_auth_required[**Param, RetType](callable_obj: Callable[Param, RetType]) -> Callable[Param, RetType]:
    """A decorator that signs a callable object with an 'auth_required'
    attribute (True). We use this attribute to find which handler callbacks
    require an authorized user for protected access.
    Args:
        callable_obj (instance): A handler callable object.
    Returns:
        The callable object.
    """
    callable_obj.auth_required = True  # type: ignore

    return callable_obj
