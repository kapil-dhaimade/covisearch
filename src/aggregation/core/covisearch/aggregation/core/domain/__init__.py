from typing import List, Dict
import functools

import covisearch.aggregation.core.domain.entities as entities
from covisearch.aggregation.core.domain.entities import \
    AggregatedResourceInfoRepo, FilteredAggregatedResourceInfo, SearchFilter, CovidResourceInfo, \
    CovidResourceType
import covisearch.aggregation.core.domain.relevence as relevance
import covisearch.aggregation.core.domain.resourcemapping as resourcemapping
import covisearch.util.websitedatascraper as webdatascraper
import covisearch.util.elapsedtime as elapsedtime
import covisearch.util.mytypes as mytypes
import covisearch.util.geoutil as geoutil


MAX_RESOURCES_STORAGE_LIMIT = 300


def aggregate_covid_resources(
        search_filter: SearchFilter, resource_info_repo: AggregatedResourceInfoRepo,
        web_src_repo: resourcemapping.WebSourceRepo):

    aggregated_resources = _collect_resources_from_covid_sources(search_filter, web_src_repo)

    ctx_3 = elapsedtime.start_measuring_operation('merging duplicates')
    resource_info_class = entities.get_resource_info_class(search_filter.resource_type)
    covisearch_resources = resource_info_class.merge_duplicates(aggregated_resources)
    elapsedtime.stop_measuring_operation(ctx_3)

    ctx_6 = elapsedtime.start_measuring_operation('sorting covid resources')
    covisearch_resources.sort(key=functools.cmp_to_key(
        relevance.get_res_info_comparator(search_filter)))
    elapsedtime.stop_measuring_operation(ctx_6)

    ctx_5 = elapsedtime.start_measuring_operation('removing redundant fields')
    covisearch_resources = CovidResourceInfo.remove_redundant_fields(covisearch_resources)
    elapsedtime.stop_measuring_operation(ctx_5)

    if len(covisearch_resources) > MAX_RESOURCES_STORAGE_LIMIT:
        covisearch_resources = covisearch_resources[: MAX_RESOURCES_STORAGE_LIMIT]

    filtered_data = FilteredAggregatedResourceInfo(search_filter, covisearch_resources)

    ctx = elapsedtime.start_measuring_operation('writing resources to repo')
    resource_info_repo.set_resources_for_filter(filtered_data)
    elapsedtime.stop_measuring_operation(ctx)


def _collect_resources_from_covid_sources(
        search_filter: SearchFilter, web_src_repo: resourcemapping.WebSourceRepo) -> List[Dict]:

    resource_info_mapper = resourcemapping.ResourceInfoMapper()

    ctx = elapsedtime.start_measuring_operation('websources fetch')
    web_sources: Dict[mytypes.URL, resourcemapping.WebSource] = \
        web_src_repo.get_web_sources_for_filter(search_filter)
    elapsedtime.stop_measuring_operation(ctx)

    if not web_sources:
        raise ValueError('No matching web source found for filter: ' +
                         search_filter.to_url_query_string_fmt())

    covisearch_resources = _collect_resources_from_primary_city(
        resource_info_mapper, search_filter, web_sources)

    if len(covisearch_resources) < 20:
        collect_resources_from_synonym_cities(
            covisearch_resources, resource_info_mapper, search_filter, web_sources)

    return covisearch_resources


def collect_resources_from_synonym_cities(covisearch_resources, resource_info_mapper, search_filter, web_sources):
    synonym_cities = geoutil.get_synonym_cities(search_filter.city)

    for synonym_city in synonym_cities:
        search_filter_for_synonym = SearchFilter(synonym_city,
                                                 search_filter.resource_type, None)
        synonym_city_web_sources = _get_web_srcs_for_synonym_city(search_filter_for_synonym, web_sources)

        covisearch_resources.extend(_collect_resources_for_city(
            resource_info_mapper, search_filter_for_synonym, synonym_city_web_sources))

        if len(covisearch_resources) >= 20:
            break


def _collect_resources_from_primary_city(
        resource_info_mapper, primary_city_search_filter, web_sources) -> List[Dict]:
    return _collect_resources_for_city(resource_info_mapper, primary_city_search_filter, web_sources)


def _collect_resources_for_city(resource_info_mapper, search_filter, web_sources) -> List[Dict]:
    scraped_data_list: List[webdatascraper.ScrapedData] = \
        _scrape_data_from_web_sources(web_sources)
    ctx_2 = elapsedtime.start_measuring_operation('mapping data to covisearch')
    covisearch_resources = _map_scraped_data_to_covisearch_resources(
        scraped_data_list, search_filter, web_sources, resource_info_mapper)
    elapsedtime.stop_measuring_operation(ctx_2)
    return covisearch_resources


def _get_web_srcs_for_synonym_city(
        search_filter_for_synonym: SearchFilter,
        web_sources: Dict[mytypes.URL, resourcemapping.WebSource]) -> \
        Dict[mytypes.URL, resourcemapping.WebSource]:

    synonym_city_web_sources = {}

    for web_src in web_sources.values():
        synonym_city_web_src = web_src.clone_for_filter(search_filter_for_synonym)
        synonym_city_web_sources[synonym_city_web_src.web_resource_url] = synonym_city_web_src

    return synonym_city_web_sources


def _map_scraped_data_to_covisearch_resources(
        scraped_data_list: List[webdatascraper.ScrapedData], search_filter: SearchFilter,
        web_sources: Dict[str, resourcemapping.WebSource],
        resource_info_mapper: resourcemapping.ResourceInfoMapper) -> List[Dict]:

    return [
        resource_info_mapper.map_res_info_to_covisearch(
            web_src_res_info, search_filter, web_sources[scraped_data.url])
        for scraped_data in scraped_data_list if scraped_data is not None
        for web_src_res_info in scraped_data.table_rows
    ]


def _scrape_data_from_web_sources(web_sources: Dict[str, resourcemapping.WebSource]) -> \
        List[webdatascraper.ScrapedData]:

    data_scraping_params = [
        webdatascraper.DataScrapingParams(
            web_src.web_resource_url, web_src.request_content_type, web_src.request_body,
            web_src.additional_http_headers,
            web_src.response_content_type, web_src.data_table_extract_selectors,
            web_src.data_table_filters, {})
        for web_src in web_sources.values()
    ]

    ctx = elapsedtime.start_measuring_operation('data scraping')
    scraped_data_list = webdatascraper.scrape_data_from_websites(data_scraping_params)
    elapsedtime.stop_measuring_operation(ctx)
    return scraped_data_list


# import covisearch.aggregation.core.infra as infra
# import google.cloud.firestore as firestore
# import sys
# import traceback
# import covisearch.aggregation.core.domain.resourcemapping as resourcemapping
# import covisearch.util.datetimeutil as datetimeutil
# import datetime
#
#
# if __name__ == '__main__':
#     try:
#         # isofmt1 = datetimeutil.map_short_datetime_dd_mm_to_utc_datetime(
#         # '05-06-2021 10:19:49', datetime.timezone.utc)
#
#         # dt = resourcemapping._map_short_datetime_dd_mm_time_to_covisearch('05-06-2021 10:19:49pm').isoformat()
#         # dt_mapper = resourcemapping.get_datetime_format_mapper(datetimeutil.DatetimeFormat.UNIX_TIMESTAMP_MILLISEC)
#         # dt2 = dt_mapper('1621189375010').isoformat()
#
#         elapsedtime.start_measuring_total()
#
#         ctx = elapsedtime.start_measuring_operation('firestore DB init')
#         db = firestore.Client()
#         elapsedtime.stop_measuring_operation(ctx)
#
#         aggregated_res_info_repo = infra.AggregatedResourceInfoRepoImpl(db)
#         web_src_repo = infra.WebSourceRepoImpl(db)
#         search_filter = SearchFilter('bengaluru', entities.CovidResourceType.MED_FABIFLU, None)
#         aggregate_covid_resources(search_filter, aggregated_res_info_repo, web_src_repo)
#
#         elapsedtime.stop_measuring_total()
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
