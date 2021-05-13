import covisearch.aggregation.datasyncer.domain as domain
import covisearch.aggregation.datasyncer.infra as infra


# NOTE: KAPIL: For testing with Firestore DB:
# Refer 'Deployment.txt' to set up machine before testing locally
# and for deployment.
# -We need to install Google Cloud SDK on local machine before
# we can test Firestore DB on local machine.
# -After install, run 'gcloud auth application-default login' to auth using the
# default app credentials using Google's ADC.
# Sources:
#   -Google Cloud Docs: Firestore: Quickstart using a Server Client Library:
#   https://cloud.google.com/firestore/docs/quickstart-servers#cloud-console
#   -Google Cloud Client Libraries Docs - Python Client for Google Cloud Firestore:
#   https://googleapis.dev/python/firestore/latest/index.html

# NOTE: KAPIL: About Cloud functions:
# Sources:
#   -Google Cloud Docs: Writing Cloud Functions:
#   https://cloud.google.com/functions/docs/writing
#   -Google Cloud Docs: Background Cloud Functions:
#   https://cloud.google.com/functions/docs/writing/background


# Starting point called by Google Cloud Function
# Do init and call corresponding domain function
def resync_aggregated_data(event, context):
    filter_stats_firestore_repo = infra.FilterStatsRepoFirestoreImpl()
    resyncer_config_firestore = infra.get_resyncer_config_from_firestore()

    domain.resync_aggregated_data(filter_stats_firestore_repo,
                                  resyncer_config_firestore)


def main():
    resync_aggregated_data(None, None)


# NOTE: KAPIL: Uncomment when testing on local machine
# if __name__ == '__main__':
#     main()
