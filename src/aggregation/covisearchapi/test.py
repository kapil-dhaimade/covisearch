from unittest.mock import Mock

import main


def test_print_name():
    data = {
      "search_filter": {
        "city": "bengaluru",
        "resource-type": "plasma"
      },
      "page_no": 1
    }
    req = Mock(get_json=Mock(return_value=data), args=data, headers={"content-type": "application/json"})

    # Call tested function
    print(main.covisearch_api_request_handler(req))
    # assert main.hello_http(req) == 'Hello {}!'.format(name)


test_print_name()