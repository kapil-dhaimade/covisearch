from unittest.mock import Mock

import main


def test_success():
    data = {
        "city": "bengaluru",
        "resource-type": "plasma",
        "page_no": 1
    }
    req = Mock(args=data)

    # Call tested function
    print(main.covisearch_api_request_handler(req))
    # assert main.hello_http(req) == 'Hello {}!'.format(name)


test_success()
