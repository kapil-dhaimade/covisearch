from typing import List, Dict
import functools

import covisearch.aggregation.aggregator.domain.entities as entities
from covisearch.aggregation.aggregator.domain.entities import \
    AggregatedResourceInfoRepo, FilteredAggregatedResourceInfo, SearchFilter, CovidResourceInfo
import covisearch.aggregation.aggregator.domain.resourcemapping as resourcemapping
import covisearch.util.websitedatascraper as webdatascraper


def aggregate_completely_and_replace_in_cache(
        search_filter: SearchFilter, resource_info_repo: AggregatedResourceInfoRepo,
        web_src_repo: resourcemapping.WebSourceRepo):
    aggregated_resources = aggregate_resources_from_covid_sources(search_filter, web_src_repo)
    filtered_data = FilteredAggregatedResourceInfo(search_filter, aggregated_resources)
    resource_info_repo.set_resources_for_filter(filtered_data)


def aggregate_resources_from_covid_sources(
        search_filter: SearchFilter, web_src_repo: resourcemapping.WebSourceRepo) -> List[Dict]:

    web_sources = web_src_repo.get_web_sources_for_filter(search_filter)

    scraped_data_list: List[webdatascraper.ScrapedData] = \
        _scrape_data_from_web_sources(web_sources)

    covisearch_resources = _map_scraped_data_to_covisearch_resources(
        scraped_data_list, search_filter, web_sources)

    covisearch_resources = CovidResourceInfo.remove_duplicates(covisearch_resources)
    covisearch_resources = CovidResourceInfo.remove_unavailable_resources(covisearch_resources)
    covisearch_resources.sort(key=functools.cmp_to_key(entities.compare_res_info))

    return covisearch_resources


def _map_scraped_data_to_covisearch_resources(scraped_data_list, search_filter, web_sources):
    return [
        resourcemapping.map_res_info_to_covisearch(
            web_src_res_info, search_filter, web_sources[scraped_data.url].resource_mapping_desc)
        for scraped_data in scraped_data_list for web_src_res_info in scraped_data.table_rows
    ]


def _scrape_data_from_web_sources(web_sources: Dict[str, resourcemapping.WebSource]):
    data_scraping_params = [
        webdatascraper.DataScrapingParams(
            web_src.web_resource_url, web_src.response_content_type,
            web_src.data_table_extract_selectors, [])
        for web_src in web_sources.values()
    ]
    return webdatascraper.scrape_data_from_websites(data_scraping_params)
