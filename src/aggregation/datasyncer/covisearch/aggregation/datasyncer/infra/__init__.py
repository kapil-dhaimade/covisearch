from typing import List
import itertools
import os

import google.cloud.firestore as firestore
from google.cloud import pubsub_v1

import covisearch.aggregation.datasyncer.domain.entities as entities


class FilterStatsRepoFirestoreImpl(entities.FilterStatsRepo):
    def __init__(self, db: firestore.Client):
        self._db = db

    def get_all(self) -> List[entities.FilterStats]:
        filter_stats_db_coll = self._db.collection('filter_stats').stream()
        return [_firestore_to_filter_stats(x) for x in filter_stats_db_coll]

    def remove_for_filter(self, search_filter: str):
        self._db.collection('filter_stats').document(search_filter).delete()


class AggregatedResourceInfoRepoImpl(entities.AggregatedResourceInfoRepo):
    def __init__(self, db: firestore.Client):
        self._db = db

    def remove_resources_for_filter(self, search_filter: str):
        self._db.collection('filtered_aggregated_resource_info').\
            document(search_filter).delete()


def aggregate_covid_resources_for_filters(search_filters: List[str]):
    # Instantiates a Pub/Sub client
    publisher = pubsub_v1.PublisherClient()
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')

    # References an existing topic
    topic_path = publisher.topic_path(PROJECT_ID, "aggregate-topic")

    search_filters_csv = ''
    for search_filter in search_filters:
        search_filters_csv = search_filters_csv + search_filter + ','
    search_filters_csv = search_filters_csv[:-1]

    message_bytes = search_filters_csv.encode('utf-8')

    # Publishes a message
    try:
        publish_future = publisher.publish(topic_path, data=message_bytes)
        publish_future.result()  # Verify the publish succeeded
    except Exception as e:
        print(e)


def get_resyncer_config_from_firestore(db: firestore.Client) -> entities.ResyncerConfig:
    resyncer_config_iter = itertools.islice(db.collection('resyncer_config').stream(), 0, None)
    resyncer_config_doc = next(resyncer_config_iter)
    resyncer_config_dict = resyncer_config_doc.to_dict()
    return entities.ResyncerConfig(resyncer_config_dict['idle_resync_threshold_in_days'])


# DTO mapper
def _firestore_to_filter_stats(
        firestore_filter_stats: firestore.DocumentSnapshot) -> entities.FilterStats:
    filter_stats_dict = firestore_filter_stats.to_dict()
    last_query_datetime = filter_stats_dict['last_query_time_utc']
    return entities.FilterStats(firestore_filter_stats.id,
                                last_query_datetime)
