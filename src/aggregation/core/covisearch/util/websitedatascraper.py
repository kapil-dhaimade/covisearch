from typing import List, Dict
import json
from abc import ABC
import traceback

import scrapy
from scrapy import crawler
import jsonpath_ng

from covisearch.util.types import URL as URL
from covisearch.util.types import ContentType as ContentType


def scrape_data_from_websites(
        data_scraping_params: List['DataScrapingParams']) -> List['ScrapedData']:
    operation_ctxs_by_url = ScrapingOperationCtx(data_scraping_params)
    process = crawler.CrawlerProcess()
    process.crawl(WebsiteDataSpider, operation_ctxs_by_url)
    process.start()
    return operation_ctxs_by_url.get_all_scraped_data()


class DataScrapingParams:
    def __init__(self, url: URL, response_content_type: ContentType,
                 table_column_selectors: Dict[str, str],
                 fields_selectors: Dict[str, str]):
        self._url = url
        self._response_content_type = response_content_type
        # NOTE: KAPIL: Selector may be XPath, JSONPath, etc. based on content type
        # Refer 'https://jsonpathfinder.com/' to get JSONPaths from JSON
        # Refer 'http://videlibri.sourceforge.net/cgi-bin/xidelcgi' to get XPath from XML/HTML
        self._table_column_selectors = table_column_selectors
        self._fields_selectors = fields_selectors

    @property
    def url(self) -> URL:
        return self._url

    @property
    def response_content_type(self) -> ContentType:
        return self._response_content_type

    @property
    def table_column_selectors(self) -> Dict[str, str]:
        return self._table_column_selectors

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


class WebsiteDataSpider(scrapy.Spider):
    name = 'websitedataspider'

    def __init__(self, operation_ctx: 'ScrapingOperationCtx'):
        super().__init__()
        self._operation_ctx: 'ScrapingOperationCtx' = operation_ctx
        self.start_urls = self._operation_ctx.get_all_urls_for_scraping()

    def parse(self, response: scrapy.http.Response, **kwargs):
        if response.status != 200:
            print('Scrapy returned HTTP code: \'' + str(response.status) + '\' for url: \'' +
                  response.url + '\'')
            return

        try:
            scraping_params = self._operation_ctx.get_scraping_params_for_url(response.url)
            scraped_data = scrape_data_from_response(response.body, scraping_params)
            self._operation_ctx.set_scraped_data_for_url(response.url, scraped_data)
        except Exception:
            print('Exception while parsing Scrapy response for url: \'' + response.url + '\'. ' +
                  'Ignoring error.')
            print(traceback.print_exc())


class ScrapingOperationCtx:
    def __init__(self, data_scraping_params: List['DataScrapingParams']):
        self._operation_ctx_for_url = \
            {scraping_params.url: {'scraping-params': scraping_params, 'scraped-data': None}
             for scraping_params in data_scraping_params}

    def get_scraping_params_for_url(self, url: URL) -> DataScrapingParams:
        return self._operation_ctx_for_url[url]['scraping-params']

    def set_scraped_data_for_url(
            self, url: URL, scraped_data: ScrapedData) -> None:
        self._operation_ctx_for_url[url]['scraped-data'] = scraped_data

    def get_all_urls_for_scraping(self) -> List[URL]:
        return list(self._operation_ctx_for_url.keys())

    def get_all_scraped_data(self) -> List['ScrapedData']:
        return [x['scraped-data'] for x in list(self._operation_ctx_for_url.values())]


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
    return table_rows


class ContentTypeSelectorParser(ABC):
    def get_all_vals_matching_selector(self, selector: str) -> List[str]:
        raise NotImplementedError('ContentTypeSelectorParser is an interface')


class JSONSelectorParser(ContentTypeSelectorParser):
    def __init__(self, content: str):
        self._json_content = json.loads(content)
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
        return [parent_node.get(field_selector, '') for parent_node in parent_nodes]


class HTMLSelectorParser(ContentTypeSelectorParser):
    def __init__(self, content: str):
        self._selector = scrapy.selector.Selector(content)

    def get_all_vals_matching_selector(self, selector: str) -> List[str]:
        return [value for value in self._selector.xpath(selector).getall()]


# NOTE: KAPIL: Uncomment while testing
# if __name__ == '__main__':
#     data_scraping_params2 = [
#         DataScrapingParams('https://1platefood.com/portal/resources?page=2&type=oxygen&'
#                            'city=Mumbai&sort=last_verified_at&availability=Available',
#                            ContentType.JSON,
#                            [('name', 'data[*].name'), ('city', 'data[*].city'),
#                             ('phone', 'data[*].phone'),
#                             ('last_verified_at', 'data[*].last_verified_at')],
#                            [('page_num', 'page'), ('total_pages', 'num_pages'),
#                             ('page_size', 'page_size'), ('total_entries', 'total')]),
#
#         DataScrapingParams('https://api.covidcitizens.org/api/v1/leadbyquery?location=delhi&'
#                            'category=plasma',
#                            ContentType.JSON,
#                            [('name', 'data[*].name'), ('city', 'data[*].location'),
#                             ('phone', 'data[*].phone'),
#                             ('last_verified', 'data[*].lastverified')],
#                            [('total_entries', 'noOfLeads')])
#     ]
#     scraped_data = scrape_data_from_websites(data_scraping_params2)
#     print(9)
