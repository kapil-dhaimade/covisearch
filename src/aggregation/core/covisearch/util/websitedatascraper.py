from typing import List, Dict
import json
from abc import ABC
import traceback
import re
import concurrent.futures

import requests
import scrapy
import jsonpath_ng

from covisearch.util.mytypes import URL as URL
from covisearch.util.mytypes import ContentType as ContentType
import covisearch.util.elapsedtime as elapsedtime


def scrape_data_from_websites(
        data_scraping_params: List['DataScrapingParams']) -> List['ScrapedData']:

    operation_ctxs_by_url = ScrapingOperationCtx(data_scraping_params)

    ctx = elapsedtime.start_measuring_operation('scraping data from websites')

    WebsiteDataSpider(operation_ctxs_by_url).scrape()

    elapsedtime.stop_measuring_operation(ctx)
    return operation_ctxs_by_url.get_all_scraped_data()


class DataScrapingParams:
    def __init__(self, url: URL, request_content_type: ContentType, request_body: str,
                 response_content_type: ContentType, table_column_selectors: Dict[str, str],
                 table_row_regex_filters: Dict[str, str],
                 fields_selectors: Dict[str, str]):
        self._url = url
        self._request_content_type: ContentType = request_content_type
        self._request_body: str = request_body
        self._response_content_type = response_content_type
        # NOTE: KAPIL: Selector may be XPath, JSONPath, etc. based on content type
        # Refer 'https://jsonpathfinder.com/' to get JSONPaths from JSON
        # Refer 'http://videlibri.sourceforge.net/cgi-bin/xidelcgi' to get XPath from XML/HTML
        self._table_column_selectors = table_column_selectors
        self._table_row_regex_filters = table_row_regex_filters
        self._fields_selectors = fields_selectors

    @property
    def url(self) -> URL:
        return self._url

    @property
    def request_content_type(self) -> ContentType:
        return self._request_content_type

    @property
    def request_body(self) -> str:
        return self._request_body

    @property
    def response_content_type(self) -> ContentType:
        return self._response_content_type

    @property
    def table_column_selectors(self) -> Dict[str, str]:
        return self._table_column_selectors

    @property
    def table_row_regex_filters(self) -> Dict[str, str]:
        return self._table_row_regex_filters

    @property
    def fields_selectors(self) -> Dict[str, str]:
        return self._fields_selectors


class ScrapedData:
    def __init__(self, url: URL, table_rows: List[Dict[str, str]],
                 fields: Dict[str, str]):
        self._url = url
        self._table_rows = table_rows
        self._fields = fields

    @property
    def url(self) -> URL:
        return self._url

    @property
    def table_rows(self) -> List[Dict[str, str]]:
        return self._table_rows

    @property
    def fields(self) -> Dict[str, str]:
        return self._fields


class WebsiteDataSpider:
    def __init__(self, operation_ctx: 'ScrapingOperationCtx'):
        super().__init__()
        self._operation_ctx: 'ScrapingOperationCtx' = operation_ctx

    def scrape(self):
        # From https://stackoverflow.com/questions/9110593/asynchronous-requests-with-python-requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            response_futures = {
                executor.submit(WebsiteDataSpider._send_request,
                                self._operation_ctx.get_scraping_params_for_url(url)): url
                for url in self._operation_ctx.get_all_urls_for_scraping()
            }
            for response_future in concurrent.futures.as_completed(response_futures):
                try:
                    response = response_future.result()
                    if response.status_code != 200:
                        print('Requests returned HTTP code: \'' + str(response.status_code) + '\' for url: \'' +
                              response.url + '\'')
                        continue

                    try:
                        scraping_params = self._operation_ctx.get_scraping_params_for_url(response.url)
                        scraped_data = scrape_data_from_response(response.text, scraping_params)
                        self._operation_ctx.set_scraped_data_for_url(response.url, scraped_data)

                    except Exception:
                        print('Exception while parsing Grequests response for url: \'' + response.url + '\'. ' +
                              'Ignoring error.')
                        print(traceback.print_exc())

                except Exception:
                    print('Exception while crawling with Requests for url: \'' +
                          response_futures[response_future] + '\'.')
                    print(traceback.print_exc())

    @staticmethod
    def _send_request(scraping_params: DataScrapingParams):

        # NOTE: KAPIL: Using Postman's user-agent string because JustDial returned
        # HTTP 403 Access Denied for python requests lib's user-agent 'python-requests/2.25.1'.
        headers = {
            'User-Agent': 'PostmanRuntime/7.28.0'
        }

        # Example grequests code for GET, POST JSON and Form Data requests. Similar for requests:
        # https://www.programcreek.com/python/example/103991/grequests.post
        if scraping_params.request_content_type is ContentType.JSON:
            request_dict = json.loads(scraping_params.request_body)
            return requests.post(scraping_params.url, json=request_dict, headers=headers)

        if scraping_params.request_content_type is ContentType.FORMDATA:
            form_data_dict = json.loads(scraping_params.request_body)
            return requests.post(scraping_params.url, data=form_data_dict, headers=headers)

        return requests.get(scraping_params.url, headers=headers)


class ScrapingOperationCtx:
    def __init__(self, data_scraping_params: List['DataScrapingParams']):
        self._operation_ctx_for_url = \
            {scraping_params.url: {'scraping_params': scraping_params, 'scraped_data': None}
             for scraping_params in data_scraping_params}

    def get_scraping_params_for_url(self, url: URL) -> DataScrapingParams:
        return self._operation_ctx_for_url[url]['scraping_params']

    def set_scraped_data_for_url(
            self, url: URL, scraped_data: ScrapedData) -> None:
        self._operation_ctx_for_url[url]['scraped_data'] = scraped_data

    def get_all_urls_for_scraping(self) -> List[URL]:
        return list(self._operation_ctx_for_url.keys())

    def get_all_scraped_data(self) -> List['ScrapedData']:
        return [x['scraped_data'] for x in list(self._operation_ctx_for_url.values())]


# Factory for content type selector parser
def create_selector_parser_for_content_type(
        content_type: ContentType, content: str) -> 'ContentTypeSelectorParser':
    selector_parser = {
        ContentType.HTML: HTMLSelectorParser,
        ContentType.JSON: JSONSelectorParser
    }
    return selector_parser[content_type](content)


def scrape_data_from_response(response_content: str,
                              scraping_params: DataScrapingParams) -> ScrapedData:
    selector_parser = create_selector_parser_for_content_type(
        scraping_params.response_content_type, response_content)
    table_rows = scrape_table_from_response(scraping_params, selector_parser)
    fields = scrape_fields_from_response(scraping_params, selector_parser)
    return ScrapedData(scraping_params.url, table_rows, fields)


def scrape_fields_from_response(scraping_params: DataScrapingParams,
                                selector_parser: 'ContentTypeSelectorParser') -> Dict[str, str]:
    field_selector_pairs = [selector_pair for selector_pair in
                            scraping_params.fields_selectors.items()]
    field_selector_vals = [field_selector_pair[1] for field_selector_pair in field_selector_pairs]
    field_vals: List[str] = \
        [selector_parser.get_all_vals_matching_selector(field_selector)
         for field_selector in field_selector_vals]
    field_names = [field_selector_pair[0] for field_selector_pair in field_selector_pairs]
    fields = {key: val for key, val in zip(field_names, field_vals)}
    return fields


def scrape_table_from_response(
        scraping_params: DataScrapingParams,
        selector_parser: 'ContentTypeSelectorParser') -> List[Dict[str, str]]:
    table_column_selectors = [col_selector_pair for col_selector_pair in
                              scraping_params.table_column_selectors.items()]
    column_selector_values = [col_selector_pair[1] for col_selector_pair in table_column_selectors]
    table_vals_by_column: List[List[str]] = \
        [selector_parser.get_all_vals_matching_selector(col_selector)
         for col_selector in column_selector_values]
    column_names = [col_selector_pair[0] for col_selector_pair in table_column_selectors]
    table_rows = [{col: row_col_val for col, row_col_val in zip(column_names, row_vals)}
                  for row_vals in zip(*table_vals_by_column)]
    table_rows = _filter_table_rows(table_rows, scraping_params.table_row_regex_filters)
    return table_rows


def _filter_table_rows(table_rows: List[Dict[str, str]], row_regex_filters: Dict[str, str]) -> \
        List[Dict[str, str]]:
    return [row for row in table_rows if _row_matches_filters(row, row_regex_filters)]


def _row_matches_filters(table_row: Dict[str, str], row_regex_filters: Dict[str, str]) -> bool:
    for col_name, regex_filter in row_regex_filters.items():
        if not re.search(regex_filter, table_row[col_name], re.IGNORECASE):
            return False
    return True


class ContentTypeSelectorParser(ABC):
    def get_all_vals_matching_selector(self, selector: str) -> List[str]:
        raise NotImplementedError('ContentTypeSelectorParser is an interface')


class JSONSelectorParser(ContentTypeSelectorParser):
    def __init__(self, content: str):
        self._json_content = json.loads(self._extract_json_from_content(content))
        self._cached_parent_nodes = {}

    def get_all_vals_matching_selector(self, selector: str) -> List[str]:
        selector_tokens = selector.rsplit('.', 1)
        selector_till_parent = selector_tokens[0]

        if selector_till_parent in self._cached_parent_nodes:
            parent_nodes = self._cached_parent_nodes[selector_till_parent]
        else:
            parent_nodes = [match.value for match in
                            jsonpath_ng.parse(selector_till_parent).find(self._json_content)]
            self._cached_parent_nodes[selector_till_parent] = parent_nodes

        field_selector = selector_tokens[1]
        return [self._get_str_val_of_field(field_selector, parent_node) for parent_node in parent_nodes]

    def _get_str_val_of_field(self, field_selector, parent_node):
        # NOTE: KAPIL: In some cases parent node of JSON is 'null'. In such cases,
        # node returned by JSONPath for that parent node is None.
        if parent_node is None:
            return ''

        # NOTE: KAPIL: JSONPath node can be dict as well list. If JSON has list node
        # inside list node, then it will be list.
        if type(parent_node) is list:
            field_selector_idx = int(field_selector)
            field_val = parent_node[field_selector_idx] if len(parent_node) > field_selector_idx else ''
        else:
            field_val = parent_node.get(field_selector, '')

        if field_val is None:
            return ''
        return str(field_val)

    # NOTE: KAPIL: Preprocessing for resources which return JSON in a JS variable.
    # Eg: var data = { "abc": 2, "def": [ 2, 3 ] };
    @classmethod
    def _extract_json_from_content(cls, content: str) -> str:
        json_dict_start_pos = content.find('{')
        json_content = '{}'
        if json_dict_start_pos is not -1:
            json_content = content[json_dict_start_pos:content.rfind('}') + 1]
        else:
            json_array_start_pos = content.find('[')
            if json_array_start_pos is not -1:
                json_content = content[json_array_start_pos:content.rfind(']') + 1]
        return json_content


# NOTE: KAPIL: Format of selector: <parent_node_selector>||<child_val_selector>
# Eg: descendant-or-self::div[@class and contains(concat(' ', normalize-space(@class), ' '),
# ' detail-row ') and (@class and contains(concat(' ', normalize-space(@class), ' '), ' phone '))]/
# descendant-or-self::*/a[@class and contains(concat(' ', normalize-space(@class), ' '), ' action-btn ')
#  and (@class and contains(concat(' ', normalize-space(@class), ' '), ' gtm-phone-call '))]
# ||substring-after(@href, 'tel:')
# REASONING:
# 1. This is being done because we need to get empty string in case parent node is present and
# actual target node is not present. However, the built-in Scrapy XPath parser does not support this.
# It simply does not return that entry, hence will be a problem when we want to extract tables as
# columns having missing values will have lesser entries than other columns.
# 2. Another reason is that we need pre-processing on some values, like returning string after a
# prefix. Full featured XPath parsers can do this in one selector. However, Scrapy's HTML parser
# needs to perform this in 2 steps, first to get parent nodes, and second step to actually fetch
# substring after the given prefix.
# Sources:
#   -SO: Returning a string per element using substring-after:
#   https://stackoverflow.com/questions/42506393/returning-a-string-per-element-using-substring-after/42516851
#   -SO: XPath get default value when node is empty or not present (note: This does not work in Scrapy):
#   https://stackoverflow.com/questions/38178578/xpath-get-default-value-when-node-is-empty-or-not-present
class HTMLSelectorParser(ContentTypeSelectorParser):
    def __init__(self, content: str):
        self._selector = scrapy.selector.Selector(text=content)

    def get_all_vals_matching_selector(self, selector: str) -> List[str]:
        html_selector_list = selector.split('||')
        parent_node_selector = html_selector_list[0]
        child_val_selector = html_selector_list[1]
        parent_node_results = self._selector.xpath(parent_node_selector)
        matching_vals = [parent_node_result.xpath(child_val_selector).get(default='')
                         for parent_node_result in parent_node_results]
        return matching_vals


# NOTE: KAPIL: Uncomment while testing
# if __name__ == '__main__':
#     json_selector = JSONSelectorParser('var global = { \"abc\": 1, \"def\": { \"x\": 2, \"y\": 3} };')
#     vals = json_selector.get_all_vals_matching_selector('def[*].x')
#
#     try:
#         di = json.loads('{"variables": {},"query": "{\\n  workspace {\\n    tickets(city: \\"Mumbai\\") {\\n      edges {\\n        node {\\n          updatedAt\\n          resourceType\\n          subResourceType\\n          contactName\\n          contactNumber\\n          upvoteCount\\n          downvoteCount\\n          description\\n          city\\n          state\\n          pincode\\n          address\\n          leadId\\n          updateUrl\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n"}')
#     except:
#         print(traceback.print_exc())
#
#     data_scraping_params2 = [
#
#         DataScrapingParams('https://api.covidcitizens.org/api/v1/leadbyquery?location=delhi&'
#                            'category=plasma', None, None,
#                            ContentType.JSON,
#                            {'name': 'data[*].name', 'city': 'data[*].location',
#                             'phone': 'data[*].phone',
#                             'last_verified': 'data[*].lastverified'},
#                            {}),
#         DataScrapingParams('https://e1xevguqtj.execute-api.ap-south-1.amazonaws.com/metabase/graphql',
#                            ContentType.JSON, '{"variables": {},"query": "{\\n  workspace {\\n    tickets(city: \\"Mumbai\\", resourceType: \\"Blood\\") {\\n      edges {\\n        node {\\n          updatedAt\\n          resourceType\\n          subResourceType\\n          contactName\\n          contactNumber\\n          upvoteCount\\n          downvoteCount\\n          description\\n          city\\n          state\\n          pincode\\n          address\\n          leadId\\n          updateUrl\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n"}',
#                            ContentType.JSON,
#                            {},
#                            {})
#     ]
#     scraped_data = scrape_data_from_websites(data_scraping_params2)
#     print(9)
