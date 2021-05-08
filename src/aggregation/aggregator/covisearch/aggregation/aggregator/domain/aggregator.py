import json


# ===========Temp Model=========
class Data:
    None


class FilteredData:
    curr_end_page: int
    data: list


# ===========aggregator functions=========
def aggregate_new_resource_for_filter(search_filter: dict, count_of_new_pages_to_fetch: int):
    filtered_data = fetch_data_for_filter(search_filter)
    start_page = 1
    if filtered_data is not None:
        start_page = filtered_data.curr_end_page
    end_page = start_page + count_of_new_pages_to_fetch
    new_resources = aggregate_resource_for_filter(search_filter, range(start_page, end_page))
    filtered_data.data.append(new_resources)
    save_data_for_filter(filtered_data)

# in future this fn may take max-page param if we update each page according to different policy
def aggregate_resource_for_filter_completely(search_filter: dict):
    filtered_data = fetch_data_for_filter(search_filter)
    start_page = 1
    if filtered_data is None:
        raise Exception("No data present for provided filter")
    end_page = filtered_data.curr_end_page
    new_resources = aggregate_resource_for_filter(search_filter, range(start_page, end_page))
    filtered_data.data = new_resources
    save_data_for_filter(filtered_data)


# ===========Temp DB functions=========
def fetch_data_for_filter(search_filter: dict) -> FilteredData:
    None


def save_data_for_filter(search_filter: dict, filter_data: FilteredData):
    None


# ===========Temp Crawler functions=========
def aggregate_resource_for_filter(search_filter: dict, page_range: range) -> list:
    # fetch data using crawler
    new_resources = []
    return new_resources