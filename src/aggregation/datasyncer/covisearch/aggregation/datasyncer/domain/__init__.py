import traceback
from typing import List, Callable

import covisearch.aggregation.datasyncer.domain.entities as entities


def resync_aggregated_data(filter_stats_repo: entities.FilterStatsRepo,
                           resyncer_config: entities.ResyncerConfig,
                           resource_info_repo: entities.AggregatedResourceInfoRepo,
                           aggregate_covid_resources_for_filters: Callable[[List[str]], None]) -> None:

    filter_stats = filter_stats_repo.get_all()

    filters_to_resync = _get_filters_to_resync(filter_stats, resyncer_config)
    _resync_resources_for_filter(filters_to_resync, aggregate_covid_resources_for_filters)

    filters_to_remove = _get_filters_to_remove(filter_stats, resyncer_config)
    _remove_resources_for_filter(filters_to_remove, resource_info_repo, filter_stats_repo)


def _remove_resources_for_filter(filter_to_remove: List[entities.FilterStats],
                                 resource_info_repo: entities.AggregatedResourceInfoRepo,
                                 filter_stats_repo: entities.FilterStatsRepo):

    for filter_stats_item in filter_to_remove:
        try:
            print('Removing resources for filter \'' + filter_stats_item.search_filter + '\'...')

            resource_info_repo.remove_resources_for_filter(filter_stats_item.search_filter)
            filter_stats_repo.remove_for_filter(filter_stats_item.search_filter)

            print('Removal success for filter \'' + filter_stats_item.search_filter + '\'.')
        except Exception:
            print(traceback.print_exc())
            print('Exception while removing resources for search filter: \'' +
                  filter_stats_item.search_filter + '\'. ' +
                  'Ignoring error and continuing removal of other filters.')


def _resync_resources_for_filter(filter_stats_to_resync: List[entities.FilterStats],
                                 aggregate_covid_resources_for_filters: Callable[[List[str]], None]):
    filters_to_resync_str = [filter_stats.search_filter for filter_stats in filter_stats_to_resync]
    chunk_size = 100
    filter_chunks_to_resync = [filters_to_resync_str[i: i + chunk_size]
                                     for i in range(0, len(filters_to_resync_str), chunk_size)]

    chunk_idx = 1
    for filters_chunk in filter_chunks_to_resync:
        try:
            print('Resyncing resources for filter chunk \'' + str(chunk_idx) + '\'...')

            aggregate_covid_resources_for_filters(filters_chunk)

            print('Resync success for filter chunk \'' + str(chunk_idx) + '\'.')
        except Exception:
            print(traceback.print_exc())
            print('Exception while resyncing for filters chunk: \'' +
                  str(chunk_idx) + '\'. ' +
                  'Ignoring error and continuing resyncing of other filters.')
        finally:
            chunk_idx = chunk_idx + 1


def _get_filters_to_resync(filter_stats: List[entities.FilterStats],
                           resyncer_config: entities.ResyncerConfig) -> List[entities.FilterStats]:
    return [filter_stats_item for filter_stats_item in filter_stats
            if _should_resync(filter_stats_item, resyncer_config)]


def _get_filters_to_remove(filter_stats: List[entities.FilterStats],
                           resyncer_config: entities.ResyncerConfig) -> List[entities.FilterStats]:
    return [filter_stats_item for filter_stats_item in filter_stats
            if not _should_resync(filter_stats_item, resyncer_config)]


def _should_resync(filter_stats_item: entities.FilterStats,
                   resyncer_config: entities.ResyncerConfig) -> bool:
    should_resync = \
        entities.get_resync_policy_for_filter(filter_stats_item)
    return should_resync(filter_stats_item, resyncer_config)
