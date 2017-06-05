from json import dumps
from bottle import HTTPResponse


class ErrorResponse(HTTPResponse):

    def __init__(self, e, status):
        """
        :param Exception e:
        :param int status: HTTP status code
        """
        body = {
            'error': {
                'status': status,
                'error': type(e).__name__,
                'description': str(e)
            }
        }

        json_body = dumps(body)

        super(HTTPResponse, self).__init__(json_body, status, {'Content-Type': 'application/json'})
