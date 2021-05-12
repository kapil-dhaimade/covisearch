from typing import List
import datetime
import itertools

import google.cloud.firestore as firestore

import covisearch.aggregation.datasyncer.domain.entities as entities


# This is auto-initialized when main program loads
db = firestore.Client()


class FilterStatsRepoFirestoreImpl(entities.FilterStatsRepo):
    def get_all(self) -> List[entities.FilterStats]:
        filter_stats_db_coll = db.collection('filter-stats').stream()
        return [firestore_to_filter_stats(x) for x in filter_stats_db_coll]


def get_resyncer_config_from_firestore() -> entities.ResyncerConfig:
    resyncer_config_iter = itertools.islice(db.collection('resyncer-config').stream(), 0, None)
    resyncer_config_doc = next(resyncer_config_iter)
    resyncer_config_dict = resyncer_config_doc.to_dict()
    return entities.ResyncerConfig(resyncer_config_dict['idle-resync-threshold-in-days'])


# DTO mapper
def firestore_to_filter_stats(
        firestore_filter_stats: firestore.DocumentSnapshot) -> entities.FilterStats:
    filter_stats_dict = firestore_filter_stats.to_dict()
    last_query_datetime = datetime.datetime.fromisoformat(
        filter_stats_dict['last-query-time-utc'])
    return entities.FilterStats(firestore_filter_stats.id,
                                last_query_datetime)
