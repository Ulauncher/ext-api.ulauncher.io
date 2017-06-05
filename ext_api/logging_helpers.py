import os
import sys
import logging
import time
from random import randint
from functools import wraps

from ext_api.config import log_level

logger = logging.getLogger(__name__)


def setup_logging():
    root = logging.getLogger()
    formatter = logging.Formatter("%(levelname)s | %(name)s: %(funcName)s() | %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root.addHandler(handler)
    root.setLevel(log_level)


def timeit(fn):

    @wraps(fn)
    def timed(*args, **kw):

        ts = time.time()
        result = fn(*args, **kw)
        te = time.time()

        logger.info('func:%r args:[%r, %r] took: %2.4f sec' % (fn.__name__, args, kw, te - ts))

        return result

    return timed
