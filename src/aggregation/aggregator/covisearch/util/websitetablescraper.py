from enum import Enum
from typing import Tuple, List, Dict

import scrapy


def scrape_tables_from_websites(
        table_scraping_params: List['TableScrapingParams']) -> List['ScrapedTable']:
    operation_ctxs_by_url = {x.url: TableScrapingOperationCtx(x)
                             for x in table_scraping_params}

    process = scrapy.crawler.CrawlerProcess()
    process.crawl(WebsiteTableSpider, operation_ctxs_by_url)
    process.start()
    return None


class ContentType(Enum):
    HTML = 1
    JSON = 2


URL = str


class TableScrapingParams:
    def __init__(self, url: URL, response_content_type: ContentType,
                 column_vs_xpath_list: List[Tuple[str, str]]):
        self._url = url
        self._response_content_type = response_content_type
        self._column_vs_xpath_list = column_vs_xpath_list

    @property
    def url(self) -> URL:
        return self._url

    @property
    def response_content_type(self) -> ContentType:
        return self._response_content_type

    @property
    def column_vs_xpath_list(self) -> List[Tuple[str, str]]:
        return self._column_vs_xpath_list


class ScrapedTable:
    def __init__(self, url: URL, table_rows: List[Dict[str, str]]):
        self._url = url
        self._table_rows = table_rows

    @property
    def url(self) -> URL:
        return self._url

    @property
    def table_rows(self) -> List[Dict[str, str]]:
        return self._table_rows


class WebsiteTableSpider(scrapy.Spider):
    name = 'websitetablespider'

    def __init__(self, operation_ctxs_by_url: Dict[URL, 'TableScrapingOperationCtx']):
        super().__init__()
        self._operation_ctxs_by_url = operation_ctxs_by_url
        self.start_urls = [*self._operation_ctxs_by_url]

    def parse(self, response: scrapy.http.Response, **kwargs):
        operation_ctx_for_url: 'TableScrapingOperationCtx' = \
            self._operation_ctxs_by_url[response.url]
        scrape_table_for_content_type = \
            get_table_scraper_for_content_type(operation_ctx_for_url.response_content_type)


class TableScrapingOperationCtx:
    def __init__(self, table_scraping_param: TableScrapingParams):
        self._table_scraping_param = table_scraping_param

    @property
    def response_content_type(self):
        return self._table_scraping_param.response_content_type


# Factory for content type table scraper
def get_table_scraper_for_content_type(content_type: ContentType):
    table_scraper_fns = {
        ContentType.HTML: scrape_table_from_html,
        ContentType.JSON: scrape_table_from_json
    }
    return table_scraper_fns[content_type]


def scrape_table_from_html():
    pass


def scrape_table_from_json():
    pass
