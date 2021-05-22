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

    # For more information about CORS and CORS preflight requests, see
    # https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request
    # for more information.

    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    # Note: We cant make user wait till we process backend task, and we cant
    # return with HTTP Response without completing the task. So will be calling
    # cloud function from here
    # https://cloud.google.com/functions/docs/writing/http
    # If a function creates background tasks (such as threads, futures, Node.js Promise objects,
    # callbacks, or system processes), you must terminate or otherwise resolve these tasks
    # before returning an HTTP response. Any tasks not terminated prior to an HTTP response
    # may not be completed, and may also cause undefined behavior.
    return fetch_resource_for_filter(request)
