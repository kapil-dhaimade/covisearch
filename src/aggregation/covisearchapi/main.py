from flask import escape
from flask import Request

from covisearch.aggregation.covisearchapi.domain import fetch_resource_for_filter


def covisearch_api_request_handler(request: Request):
    """Responds to any HTTP request.
    =========Request=========
    {
      "search_filter": {
        "city": "mumbai",
        "resource": "oxygen"
      },
      "page_no": 2
    }

    =========Response========
    {
      "res-info-data": [
        {
            "contact_name":"Test"
            ....
        },
        {
            "contact_name":"Test2"
            ....
        }
      ]
    }
    """
    # Note: We cant make user wait till we process backend task, and we cant
    # return with HTTP Response without completing the task. So will be calling
    # cloud function from here
    # https://cloud.google.com/functions/docs/writing/http
    # If a function creates background tasks (such as threads, futures, Node.js Promise objects,
    # callbacks, or system processes), you must terminate or otherwise resolve these tasks
    # before returning an HTTP response. Any tasks not terminated prior to an HTTP response
    # may not be completed, and may also cause undefined behavior.
    content_type = request.headers['content-type']
    if content_type == 'application/json':
        request_json = request.get_json(silent=True)
        if request_json:
            return fetch_resource_for_filter(request_json)
        else:
            raise ValueError("JSON is invalid")
    else:
        raise ValueError("invalid content type")
