from typing import List, Dict
import functools

import covisearch.aggregation.core.domain.entities as entities
from covisearch.aggregation.core.domain.entities import \
    AggregatedResourceInfoRepo, FilteredAggregatedResourceInfo, SearchFilter, CovidResourceInfo, \
    CovidResourceType
import covisearch.aggregation.core.domain.resourcemapping as resourcemapping
import covisearch.util.websitedatascraper as webdatascraper


def aggregate_covid_resources(
        search_filter: SearchFilter, resource_info_repo: AggregatedResourceInfoRepo,
        web_src_repo: resourcemapping.WebSourceRepo):

    aggregated_resources = _aggregate_resources_from_covid_sources(search_filter, web_src_repo)
    filtered_data = FilteredAggregatedResourceInfo(search_filter, aggregated_resources)
    resource_info_repo.set_resources_for_filter(filtered_data)


def _aggregate_resources_from_covid_sources(
        search_filter: SearchFilter, web_src_repo: resourcemapping.WebSourceRepo) -> List[Dict]:

    web_sources = web_src_repo.get_web_sources_for_filter(search_filter)

    if not web_sources:
        raise ValueError('No matching web source found for filter: ' +
                         search_filter.to_url_query_string_fmt())

    scraped_data_list: List[webdatascraper.ScrapedData] = \
        _scrape_data_from_web_sources(web_sources)

    covisearch_resources = _map_scraped_data_to_covisearch_resources(
        scraped_data_list, search_filter, web_sources)

    covisearch_resources = CovidResourceInfo.remove_duplicates(covisearch_resources)
    covisearch_resources = CovidResourceInfo.remove_unavailable_resources(covisearch_resources)
    covisearch_resources = CovidResourceInfo.remove_redundant_fields(covisearch_resources)
    covisearch_resources.sort(key=functools.cmp_to_key(
        entities.get_res_info_comparator(search_filter.resource_type)))

    return covisearch_resources


def _map_scraped_data_to_covisearch_resources(
        scraped_data_list: List[webdatascraper.ScrapedData],
        search_filter: SearchFilter, web_sources: Dict[str, resourcemapping.WebSource]):
    return [
        resourcemapping.map_res_info_to_covisearch(
            web_src_res_info, search_filter, web_sources[scraped_data.url])
        for scraped_data in scraped_data_list if scraped_data is not None
        for web_src_res_info in scraped_data.table_rows
    ]


def _scrape_data_from_web_sources(web_sources: Dict[str, resourcemapping.WebSource]):
    data_scraping_params = [
        webdatascraper.DataScrapingParams(
            web_src.web_resource_url, web_src.response_content_type,
            web_src.data_table_extract_selectors, {})
        for web_src in web_sources.values()
    ]
    return webdatascraper.scrape_data_from_websites(data_scraping_params)


# import covisearch.aggregation.core.infra as infra
# import google.cloud.firestore as firestore
# import sys
# import traceback
#
#
# if __name__ == '__main__':
#     try:
#         db = firestore.Client()
#         aggregated_res_info_repo = infra.AggregatedResourceInfoRepoImpl(db)
#         web_src_repo = infra.WebSourceRepoImpl(db)
#         search_filter = SearchFilter('mumbai', entities.CovidResourceType.OXYGEN, None)
#         aggregate_covid_resources(search_filter, aggregated_res_info_repo, web_src_repo)
#     except Exception as ex:
#         # <class 'IndexError'>
#         print(sys.exc_info()[0])
#
#         # None
#         # Traceback (most recent call last):
#         #   File "D:/Code/covisearch/src/aggregation/core/covisearch/aggregation/core/domain/
#         # __init__.py", line 75, in <module>
#         #     aggregate_covid_resources(search_filter, aggregated_res_info_repo, web_src_repo)
#         #   File "D:/Code/covisearch/src/aggregation/core/covisearch/aggregation/core/domain/
#         # __init__.py", line 17, in aggregate_covid_resources
#         #     i = li[2]
#         # IndexError: list index out of range
#         print(traceback.print_exception(*sys.exc_info()))
#
#         # None
#         #   File "D:/Code/covisearch/src/aggregation/core/covisearch/aggregation/core/domain/
#         # __init__.py", line 75, in <module>
#         #     aggregate_covid_resources(search_filter, aggregated_res_info_repo, web_src_repo)
#         #   File "D:/Code/covisearch/src/aggregation/core/covisearch/aggregation/core/domain/
#         # __init__.py", line 17, in aggregate_covid_resources
#         #     i = li[2]
#         print(traceback.print_tb(ex.__traceback__))
#
#         # list index out of range
#         print(str(ex))
#
#         # None
#         # Traceback (most recent call last):
#         #   File "D:/Code/covisearch/src/aggregation/core/covisearch/aggregation/core/domain/
#         # __init__.py", line 75, in <module>
#         #     aggregate_covid_resources(search_filter, aggregated_res_info_repo, web_src_repo)
#         #   File "D:/Code/covisearch/src/aggregation/core/covisearch/aggregation/core/domain/
#         # __init__.py", line 17, in aggregate_covid_resources
#         #     i = li[2]
#         # IndexError: list index out of range
#         print(traceback.print_exc())
#     print(9)
