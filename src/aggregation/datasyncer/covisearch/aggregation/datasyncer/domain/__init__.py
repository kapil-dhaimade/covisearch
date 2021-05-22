import traceback

import covisearch.aggregation.datasyncer.domain.entities as entities
import covisearch.aggregation.core.domain.entities as coreentities
import covisearch.aggregation.core.domain.resourcemapping as resourcemapping
import covisearch.aggregation.core.domain as coredomain


def resync_aggregated_data(filter_stats_repo: entities.FilterStatsRepo,
                           resyncer_config: entities.ResyncerConfig,
                           resource_info_repo: coreentities.AggregatedResourceInfoRepo,
                           web_src_repo: resourcemapping.WebSourceRepo) -> None:
    for filter_stats_item in filter_stats_repo.get_all():
        should_resync = \
            entities.get_resync_policy_for_filter(filter_stats_item)
        if should_resync(filter_stats_item, resyncer_config):
            try:
                coredomain.aggregate_covid_resources(
                    coreentities.SearchFilter.create_from_url_query_string_fmt(
                        filter_stats_item.search_filter),
                    resource_info_repo, web_src_repo)
            except Exception:
                print(traceback.print_exc())
                print('Exception while resyncing for search filter: \'' +
                      filter_stats_item.search_filter + '\'. ' +
                      'Ignoring error and continuing resyncing of other filters.')
