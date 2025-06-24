from json import dumps

from bottle import HTTPResponse, response


class ErrorResponse(HTTPResponse):
    def __init__(self, e: Exception, status: int) -> None:
        """
        :param Exception e:
        :param int status: HTTP status code
        """
        body: dict[str, dict[str, str | int]] = {
            "error": {"status": status, "error": type(e).__name__, "description": str(e)}
        }

        json_body: str = dumps(body)

        headers: dict[str, str] = {}
        headers.update(response.headers)
        headers["Content-Type"] = "application/json"

        super(HTTPResponse, self).__init__(json_body, status, headers)  # type: ignore
