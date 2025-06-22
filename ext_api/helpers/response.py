from json import dumps

from bottle import HTTPResponse, response


class ErrorResponse(HTTPResponse):

    def __init__(self, e, status) -> None:
        """
        :param Exception e:
        :param int status: HTTP status code
        """
        body = {"error": {"status": status, "error": type(e).__name__, "description": str(e)}}

        json_body = dumps(body)

        headers = {}
        headers.update(response.headers)
        headers["Content-Type"] = "application/json"

        super(HTTPResponse, self).__init__(json_body, status, headers)
