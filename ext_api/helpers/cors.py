from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from bottle import Bottle, request, response

Param = ParamSpec("Param")
RetType = TypeVar("RetType")


def allow_options_requests[**Param, RetType](callback: Callable[Param, RetType]) -> Callable[Param, RetType | None]:
    @wraps(callback)
    def wrapper(*args: Param.args, **kwargs: Param.kwargs) -> RetType | None:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "PATCH, GET, POST, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = (
            "Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token, Authorization"
        )

        if request.method.lower() == "options":
            return None

        return callback(*args, **kwargs)

    return wrapper


def add_options_route(app: Bottle) -> None:
    @app.route("/<url:re:.*>", method=["OPTIONS"])  # type: ignore
    def options(_):  # type: ignore
        return
