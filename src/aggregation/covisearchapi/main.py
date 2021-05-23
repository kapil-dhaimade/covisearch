from flask import escape
from flask import Request

from covisearch.aggregation.covisearchapi.domain import fetch_resource_for_filter


def covisearch_api_request_handler(request: Request):
    """
    =========Response========
    {
      "meta_info":{
        "more_data_available":true|false
      }
      "resource-info-data": [
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
    return fetch_resource_for_filter(request)
