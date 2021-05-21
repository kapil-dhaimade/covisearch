from abc import ABC, abstractmethod
from json import JSONEncoder
import google.cloud.firestore as firestore
import json
from google.api_core.datetime_helpers import DatetimeWithNanoseconds
from flask import Request
from flask import abort
import base64
import json
import os
from google.cloud import pubsub_v1


def fetch_resource_for_filter(request: Request):
    city = request.args["city"]
    resource_type = request.args["resource-type"]
    page_no = request.args["page_no"]

    if resource_type is None or city is None:
        raise abort(400)

    if page_no is None:
        page_no = 1
    else:
        page_no = int(page_no)

    # This is auto-initialized when main program loads
    db = firestore.Client()

    # ======================updating stats======================
    res_info_filter_id = "city=" + city + "&resource-type=" + resource_type
    filter_stat_doc = db.collection('filter-stats'). \
        document(res_info_filter_id).get()

    query_time = {"last-query-time-utc": DatetimeWithNanoseconds.today()}
    if not filter_stat_doc.exists:
        db.collection('filter-stats').add(query_time, "res_info_filter_id")
        raise abort(202)
    else:
        db.collection('filter-stats'). \
            document(res_info_filter_id).set(query_time)

    # ======================fetching resource======================
    res_info_doc = db.collection('filtered-aggregated-resource-info'). \
        document(res_info_filter_id).get()

    if not res_info_doc.exists:
        resync_invoke_schedule(res_info_filter_id)
        raise abort(202)

    resources = res_info_doc.get(db.field_path('res-info-data'))
    page_size = 10
    if len(resources) < page_no * page_size:
        if len(resources) < (page_no - 1) * page_size:
            raise abort(400)
        else:
            more_data_available = False
            res_info_data = resources[(page_no - 1) * page_size:len(resources) - 1]
    else:
        more_data_available = True
        res_info_data = resources[(page_no - 1) * page_size:page_no * page_size]

    response_dict = {
        "meta-info": {
            "more-data-available": more_data_available,
        },
        "res-info-data": res_info_data
    }
    return json.dumps(response_dict, cls=DateTimeEncoder)


# Publishes a message to a Cloud Pub/Sub topic.
def resync_invoke_schedule(res_info_filter_id: str):
    # Instantiates a Pub/Sub client
    publisher = pubsub_v1.PublisherClient()
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')

    # References an existing topic
    topic_path = publisher.topic_path(PROJECT_ID, "resync-schedule-topic")

    message_bytes = res_info_filter_id.encode('utf-8')

    # Publishes a message
    try:
        publish_future = publisher.publish(topic_path, data=message_bytes)
        publish_future.result()  # Verify the publish succeeded
    except Exception as e:
        print(e)


class DateTimeEncoder(JSONEncoder):
    # Override the default method
    def default(self, obj):
        if isinstance(obj, DatetimeWithNanoseconds):
            return obj.isoformat()
