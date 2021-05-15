import json
import entities
from entities import AggregatedResourceInfoRepo, FilteredAggregatedResourceInfo


def aggregate_new_resources_and_append_to_cache(search_filter: dict,
                                                count_of_new_pages_to_fetch: int,
                                                resource_info_repo: AggregatedResourceInfoRepo):
    filtered_data = resource_info_repo.get_filtered_resources(search_filter)
    if filtered_data is None:
        filtered_data = FilteredAggregatedResourceInfo(search_filter, 0, [])
    start_page = filtered_data.curr_end_page
    end_page = start_page + count_of_new_pages_to_fetch
    new_resources = aggregate_resources(search_filter, range(start_page, end_page))
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
    # Todo - fetch data using crawler
    new_resources = []
    new_resources.sort(reverse=True)
    return new_resources
