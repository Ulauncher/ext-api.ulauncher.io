from bottle import request


def is_lambda():
    return bool(request.get("HTTP_X_AMZN_TRACE_ID"))


def get_url_prefix():
    return request.get("SCRIPT_NAME", "")  # is set to /<dev|prod> for lambdas
