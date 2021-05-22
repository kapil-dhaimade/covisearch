from typing import List
import itertools

import google.cloud.firestore as firestore

import covisearch.aggregation.datasyncer.domain.entities as entities


class FilterStatsRepoFirestoreImpl(entities.FilterStatsRepo):
    def __init__(self, db: firestore.Client):
        self._db = db

    def get_all(self) -> List[entities.FilterStats]:
        filter_stats_db_coll = self._db.collection('filter_stats').stream()
        return [firestore_to_filter_stats(x) for x in filter_stats_db_coll]


def get_resyncer_config_from_firestore(db: firestore.Client) -> entities.ResyncerConfig:
    resyncer_config_iter = itertools.islice(db.collection('resyncer_config').stream(), 0, None)
    resyncer_config_doc = next(resyncer_config_iter)
    resyncer_config_dict = resyncer_config_doc.to_dict()
    return entities.ResyncerConfig(resyncer_config_dict['idle_resync_threshold_in_days'])


# DTO mapper
def firestore_to_filter_stats(
        firestore_filter_stats: firestore.DocumentSnapshot) -> entities.FilterStats:
    filter_stats_dict = firestore_filter_stats.to_dict()
    last_query_datetime = filter_stats_dict['last_query_time_utc']
    return entities.FilterStats(firestore_filter_stats.id,
                                last_query_datetime)
