import traceback
from typing import List

import covisearch.aggregation.datasyncer.domain.entities as entities
import covisearch.aggregation.core.domain.entities as coreentities
import covisearch.aggregation.core.domain.resourcemapping as resourcemapping
import covisearch.aggregation.core.domain as coredomain
import covisearch.util.websitedatascraper as websitedatascraper


def resync_aggregated_data(filter_stats_repo: entities.FilterStatsRepo,
                           resyncer_config: entities.ResyncerConfig,
                           resource_info_repo: coreentities.AggregatedResourceInfoRepo,
                           web_src_repo: resourcemapping.WebSourceRepo) -> None:

    filter_stats = filter_stats_repo.get_all()

    filters_to_resync = _get_filters_to_resync(filter_stats, resyncer_config)
    _resync_resources_for_filter(filters_to_resync, resource_info_repo, web_src_repo)

    filters_to_remove = _get_filters_to_remove(filter_stats, resyncer_config)
    _remove_resources_for_filter(filters_to_remove, resource_info_repo, filter_stats_repo)


def _remove_resources_for_filter(filter_to_remove: List[entities.FilterStats],
                                 resource_info_repo: coreentities.AggregatedResourceInfoRepo,
                                 filter_stats_repo: entities.FilterStatsRepo):

    for filter_stats_item in filter_to_remove:
        try:
            print('Removing resources for filter \'' + filter_stats_item.search_filter + '\'...')

            resource_info_repo.remove_resources_for_filter(
                coreentities.SearchFilter.create_from_url_query_string_fmt(filter_stats_item.search_filter))
            filter_stats_repo.remove_for_filter(filter_stats_item.search_filter)

            print('Removal success for filter \'' + filter_stats_item.search_filter + '\'.')
        except Exception:
            print(traceback.print_exc())
            print('Exception while removing resources for search filter: \'' +
                  filter_stats_item.search_filter + '\'. ' +
                  'Ignoring error and continuing removal of other filters.')


def _resync_resources_for_filter(filter_stats_to_resync: List[entities.FilterStats],
                                 resource_info_repo: coreentities.AggregatedResourceInfoRepo,
                                 web_src_repo: resourcemapping.WebSourceRepo):

    for filter_stats_item in filter_stats_to_resync:
        try:
            print('Resyncing resources for filter \'' + filter_stats_item.search_filter + '\'...')

            # NOTE: KAPIL: For performance reasons, spawn scrapy child process instantly on init.
            websitedatascraper.start_scrapy_process_in_advance()

            coredomain.aggregate_covid_resources(
                coreentities.SearchFilter.create_from_url_query_string_fmt(
                    filter_stats_item.search_filter),
                resource_info_repo, web_src_repo)

            print('Resync success for filter \'' + filter_stats_item.search_filter + '\'.')
        except Exception:
            print(traceback.print_exc())
            print('Exception while resyncing for search filter: \'' +
                  filter_stats_item.search_filter + '\'. ' +
                  'Ignoring error and continuing resyncing of other filters.')


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
