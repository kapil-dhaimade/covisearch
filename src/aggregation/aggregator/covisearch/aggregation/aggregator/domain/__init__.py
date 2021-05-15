import json
from typing import List, Dict

import covisearch.aggregation.aggregator.domain.entities
from covisearch.aggregation.aggregator.domain.entities import \
    AggregatedResourceInfoRepo, FilteredAggregatedResourceInfo
import covisearch.util.websitedatascraper as webdatascraper


def aggregate_new_resources_and_append_to_cache(search_filter: Dict,
                                                count_of_new_pages_to_fetch: int,
                                                resource_info_repo: AggregatedResourceInfoRepo):
    filtered_data = resource_info_repo.get_filtered_resources(search_filter)
    if filtered_data is None:
        filtered_data = FilteredAggregatedResourceInfo(search_filter, 0, [])
    start_page = filtered_data.curr_end_page
    end_page = start_page + count_of_new_pages_to_fetch
    new_resources = aggregate_resources_from_covid_sources(search_filter)
    # Todo - Removing duplicates optimally.
    # 1. Use OrderedSet
    # 2. while removing duplicate check which post is latest give preference to that post
    # 3. remove duplicates within new data as well(in aggregate_completely_and_replace_in_cache method pending).
    for resource in new_resources:
        if resource not in filtered_data.data:
            filtered_data.data.append(resource)

    filtered_data.curr_end_page = end_page
    resource_info_repo.set_filtered_resources(filtered_data)


# in future this fn may take max-page param if we update each page according to different policy
def aggregate_completely_and_replace_in_cache(search_filter: Dict,
                                              resource_info_repo: AggregatedResourceInfoRepo):
    filtered_data = resource_info_repo.get_filtered_resources(search_filter)
    if filtered_data is None:
        raise Exception("No data present for provided filter")
    new_resources = aggregate_resources_from_covid_sources(search_filter)
    filtered_data.data = new_resources
    resource_info_repo.set_filtered_resources(filtered_data)


def aggregate_resources_from_covid_sources(search_filter: Dict) -> List:
    # webdatascraper.scrape_data_from_websites()
    covid_resources = []
    covid_resources.sort(reverse=True)
    return covid_resources
