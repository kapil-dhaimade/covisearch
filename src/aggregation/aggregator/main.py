import base64

import google.cloud.firestore as firestore

import covisearch.aggregation.core.infra as infra
from covisearch.aggregation.core.domain import entities
import covisearch.aggregation.core.domain as domain


# Starting point called by Google Cloud Function
# Do init and call corresponding domain function
def aggregate_new_resources_and_append_to_cache(event, context):
    db = firestore.Client()
    aggregated_res_info_repo = infra.AggregatedResourceInfoRepoImpl(db)
    web_src_repo = infra.WebSourceRepoImpl(db)
    search_filter_str = base64.b64decode(event['data']).decode('utf-8')
    search_filter = entities.SearchFilter.create_from_url_query_string_fmt(search_filter_str)
    domain.aggregate_covid_resources(search_filter, aggregated_res_info_repo, web_src_repo)


# if __name__=='__main__':
#     aggregate_new_resources_and_append_to_cache({'data': 'Y2l0eT1jaGVubmFpJnJlc291cmNlLXR5cGU9b3h5Z2Vu'}, None)
