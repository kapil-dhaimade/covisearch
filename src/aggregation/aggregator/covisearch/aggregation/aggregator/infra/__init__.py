from abc import ABC
from typing import List
import datetime
import google.cloud.firestore as firestore
import covisearch.aggregation.aggregator.domain.entities as entities

db = firestore.Client()


class AggregatedResourceInfoRepoImpl(entities.AggregatedResourceInfoRepo):
    def get_filtered_resources(self, search_filter: dict) -> entities.FilteredAggregatedResourceInfo:
        resource_info_db_coll = db.collection('filtered-aggregated-resource-info').stream()
        return firestore_to_resource_info(resource_info_db_coll, search_filter)

    def set_filtered_resources(self, search_filter: dict,
                               filtered_aggregated_resource_info: entities.FilteredAggregatedResourceInfo):
        resource_info_db_coll = db.collection('filtered-aggregated-resource-info').stream()
        resource_info_to_firestore(resource_info_db_coll, search_filter,filtered_aggregated_resource_info)

# ===== DTO mapper =====
# Todo : remove duplicates
# Todo : handle concurrent requests


def firestore_to_resource_info(
        firestore_resource_info: firestore.DocumentSnapshot,
        search_filter: dict) -> entities.FilteredAggregatedResourceInfo:
    resource_info_root_dict = firestore_resource_info.to_dict()
    if search_filter not in resource_info_root_dict:
        return None
    resource_info_dict = resource_info_root_dict[search_filter]
    resource_info = entities.FilteredAggregatedResourceInfo.to_object(resource_info_dict)
    return resource_info


def resource_info_to_firestore(
        firestore_resource_info: firestore.DocumentSnapshot,
        search_filter: dict,
        resource_info: entities.FilteredAggregatedResourceInfo):
    resource_info_root_dict = firestore_resource_info.to_dict()
    if search_filter not in resource_info_root_dict:
        return None
    resource_info_root_dict[search_filter] = \
        entities.FilteredAggregatedResourceInfo.to_data(resource_info)
