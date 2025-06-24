import logging
import time
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import ParamSpec, TypeVar

from bottle import request, response

from ext_api.config import log_level

logger = logging.getLogger(__name__)


Param = ParamSpec("Param")
RetType = TypeVar("RetType")


def setup_logging():
    root = logging.getLogger()
    formatter = logging.Formatter("%(levelname)s | %(name)s: %(funcName)s() | %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root.addHandler(handler)
    root.setLevel(log_level)


def timeit[**Param, RetType](fn: Callable[Param, RetType]) -> Callable[Param, RetType]:
    @wraps(fn)
    def timed(*args: Param.args, **kw: Param.kwargs) -> RetType:
        ts = time.time()
        result = fn(*args, **kw)
        te = time.time()

        logger.debug("func:%r args:[%r, %r] took: %2.4f sec", fn.__name__, args, kw, te - ts)

        return result

    return timed


def bottle_request_logger[**Param, RetType](fn: Callable[Param, RetType]) -> Callable[Param, RetType]:
    """
    Wrap a Bottle request so that a log line is emitted after it's handled.
    (This decorator can be extended to take the desired logger as a param.)
    """
    bottle_logger = logging.getLogger("request")

    @wraps(fn)
    def log(*args: Param.args, **kwargs: Param.kwargs) -> RetType:
        request_time = datetime.now()
        actual_response = fn(*args, **kwargs)
        # modify this to log exactly what you need:
        bottle_logger.info(
            "%s %s %s %s %s", request.remote_addr, request_time, request.method, request.url, response.status
        )
        return actual_response

    return log
