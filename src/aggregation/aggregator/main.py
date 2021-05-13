import covisearch.aggregation.aggregator.domain as domain
import covisearch.aggregation.aggregator.infra as infra


# Starting point called by Google Cloud Function
# Do init and call corresponding domain function
def aggregate_new_resources_and_append_to_cache(event, context):
    aggregated_resource_info_repo = infra.AggregatedResourceInfoRepoImpl()
    # TODO : Pass parameter
    domain.aggregate_new_resources_and_append_to_cache(None, None, aggregated_resource_info_repo)


def main():
    aggregate_new_resources_and_append_to_cache(None, None)


# NOTE: KAPIL: Uncomment when testing on local machine
# if __name__ == '__main__':
#     main()
