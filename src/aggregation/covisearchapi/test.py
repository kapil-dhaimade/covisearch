from unittest.mock import Mock

import main


def test_size_and_offset():
    data = {
        "city": "bengaluru",
        "resource_type": "plasma",
        "record_offset": "0",
        "record_count":"3"
    }
    req = Mock(args=data)

    # Call tested function
    print(main.covisearch_api_request_handler(req))
    # assert main.hello_http(req) == 'Hello {}!'.format(name)


def test_success():
    data = {
        "city": "bengaluru",
        "resource_type": "plasma",
        "page_no": 1
    }
    req = Mock(args=data)

    # Call tested function
    print(main.covisearch_api_request_handler(req))
    # assert main.hello_http(req) == 'Hello {}!'.format(name)


# test_success()
test_size_and_offset()