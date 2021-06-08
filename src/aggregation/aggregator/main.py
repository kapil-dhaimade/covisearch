import base64

import google.cloud.firestore as firestore

import covisearch.aggregation.core.infra as infra
from covisearch.aggregation.core.domain import entities
import covisearch.aggregation.core.domain as domain


# Keep this global as global vars are not reinitialized if same Cloud Function instance
# is re-used. And we need DB init only once. Plus it is time intensive.
db = firestore.Client()

# NOTE: KAPIL: Parsing this dummy ISO format datetime during init improves performance of
# subsequent datetime parsing operations and makes mapping websrc resources to covisearch faster!!
dummy_datetime_for_performance = \
    domain.resourcemapping._map_isoformat_timestamp_to_covisearch('2021-05-10T13:22:16.075259')


# Starting point called by Google Cloud Function
# Do init and call corresponding domain function
def aggregate_covid_resources(event, context):
    aggregated_res_info_repo = infra.AggregatedResourceInfoRepoImpl(db)
    web_src_repo = infra.WebSourceRepoImpl(db)

    search_filter_str = base64.b64decode(event['data']).decode('utf-8')

    try:
        print('Aggregating covid resources for filter \'' + search_filter_str + '\'...')

        search_filter = entities.SearchFilter.create_from_url_query_string_fmt(search_filter_str)
        domain.aggregate_covid_resources(search_filter, aggregated_res_info_repo, web_src_repo)

        print('Aggregated covid resources successfully for filter \'' + search_filter_str + '\'')
    except Exception:
        print('Exception while aggregating covid resources for filter \'' + search_filter_str + '\'')
        raise


# if __name__=='__main__':
#     # city=mumbai&resource_type=ambulance
#     aggregate_covid_resources({'data': 'Y2l0eT1tdW1iYWkmcmVzb3VyY2VfdHlwZT1hbWJ1bGFuY2U='}, None)
#     # city=chennai&resource_type=plasma
#     aggregate_covid_resources({'data': 'Y2l0eT1jaGVubmFpJnJlc291cmNlX3R5cGU9cGxhc21h'}, None)
#     # # city=mumbai&resource_type=oxygen
#     # aggregate_covid_resources({'data': 'Y2l0eT1tdW1iYWkmcmVzb3VyY2VfdHlwZT1veHlnZW4='}, None)
#
#     print(9)
