import json
import entities
from entities import AggregatedResourceInfoRepo, FilteredAggregatedResourceInfo


def aggregate_new_resources_and_append_to_cache(search_filter: dict,
                                                count_of_new_pages_to_fetch: int,
                                                resource_info_repo: AggregatedResourceInfoRepo):
    filtered_data = resource_info_repo.get_filtered_resources(search_filter)
    start_page = 1
    if filtered_data is not None:
        start_page = filtered_data.curr_end_page
    end_page = start_page + count_of_new_pages_to_fetch
    new_resources = aggregate_resources(search_filter, range(start_page, end_page))
    filtered_data.data.append(new_resources)
    filtered_data.curr_end_page = end_page
    resource_info_repo.set_filtered_resources(filtered_data)


# in future this fn may take max-page param if we update each page according to different policy
def aggregate_completely_and_replace_in_cache(search_filter: dict,
                                              resource_info_repo: AggregatedResourceInfoRepo):
    filtered_data = resource_info_repo.get_filtered_resources(search_filter)
    start_page = 1
    if filtered_data is None:
        raise Exception("No data present for provided filter")
    end_page = filtered_data.curr_end_page
    new_resources = aggregate_resources(search_filter, range(start_page, end_page))
    filtered_data.data = new_resources
    resource_info_repo.set_filtered_resources(filtered_data)


def aggregate_resources(search_filter: dict, page_range: range) -> list:
    # fetch data using crawler
    new_resources = []
    return new_resources