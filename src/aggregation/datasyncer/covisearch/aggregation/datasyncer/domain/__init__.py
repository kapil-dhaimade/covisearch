import covisearch.aggregation.datasyncer.domain.entities as entities


def resync_aggregated_data(filter_stats_repo: entities.FilterStatsRepo,
                           config: entities.ResyncerConfig) -> None:
    # TODO: DEEPALI
    # NOTE: KAPIL: Decision on calling aggregate complete fn via Cloud Functions
    # or directly ia Python package is pending.
    pass
