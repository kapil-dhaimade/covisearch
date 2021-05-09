import covisearch.aggregation.datasyncer.domain as domain
import covisearch.aggregation.datasyncer.infra as infra


# Starting point called by Google Cloud Function
# Do init and call corresponding domain function
def resync_aggregated_data(event, context):
    filter_stats_firestore_repo = infra.FilterStatsRepoFirestoreImpl()
    resyncer_config_firestore = infra.get_resyncer_config_from_firestore()

    domain.resync_aggregated_data(filter_stats_firestore_repo,
                                  resyncer_config_firestore)
