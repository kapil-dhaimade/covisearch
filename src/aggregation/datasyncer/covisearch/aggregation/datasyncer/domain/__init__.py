import time

import covisearch.aggregation.datasyncer.domain.entities as entities


def resync_aggregated_data(filter_stats_repo: entities.FilterStatsRepo,
                           resyncer_config: entities.ResyncerConfig) -> None:
    for filter_stats_list_item in filter_stats_repo.get_all():
        should_resync = \
            entities.get_resync_policy_for_filter(filter_stats_list_item)
        if should_resync(filter_stats_list_item, resyncer_config):
            # TODO: Placeholder function. Change when actual one is ready
            aggregate_resource_for_filter_completely()


def aggregate_resource_for_filter_completely():
    time.sleep(0.01)
