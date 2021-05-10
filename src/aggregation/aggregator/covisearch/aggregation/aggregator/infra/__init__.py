from abc import ABC
from typing import List
import datetime
import google.cloud.firestore as firestore
import covisearch.aggregation.aggregator.domain.entities as entities


db = firestore.Client()


class AggregatedResourceInfoRepoImpl(entities.AggregatedResourceInfoRepo):
    def get_filtered_resources(self, search_filter: dict) -> entities.FilteredAggregatedResourceInfo:
        resource_info_db_coll = db.collection('filtered-aggregated-resource-info').stream()
        return firestore_to_resource_info_stats(resource_info_db_coll, search_filter)

    def set_filtered_resources(self, search_filter: dict,
                               filtered_aggregated_resource_info: entities.FilteredAggregatedResourceInfo):
        None


# ===== DTO mapper =====
class FirestoreFilteredAggregatedResourceInfoMapper:
    def to_DTO

def firestore_to_resource_info_stats(
        firestore_resource_info: firestore.DocumentSnapshot,
        search_filter: dict) -> entities.FilteredAggregatedResourceInfo:
    resource_info_root_dict = firestore_resource_info.to_dict()
    resource_info = entities.FilteredAggregatedResourceInfo()
    resource_info_dict = resource_info_root_dict[search_filter]
    resource_info.curr_end_page = resource_info_dict["curr_end_page"]
    resource_info.filter = search_filter
    resource_info.filter = search_filter

    return resource_info
