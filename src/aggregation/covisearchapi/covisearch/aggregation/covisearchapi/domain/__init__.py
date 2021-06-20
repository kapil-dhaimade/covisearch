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
import urllib.parse


# This is auto-initialized when main program loads
db = firestore.Client()


def fetch_resource_for_filter(request: Request):
    # For more information about CORS and CORS preflight requests, see
    # https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request
    # for more information.

    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        return '', 204, headers

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    page_no = None
    record_offset = None
    record_count = None

    city = request.args["city"]
    resource_type = request.args["resource_type"]
    if "page_no" in request.args:
        page_no = int(request.args["page_no"])
    if "record_offset" in request.args:
        record_offset = int(request.args["record_offset"])
    if "record_count" in request.args:
        record_count = int(request.args["record_count"])
    supported_resource_type = ["oxygen", "ambulance", "hospital_bed", "hospital_bed_icu", "plasma", "ecmo", "food", "testing",
                                 "medicine", "ventilator", "helpline", "blood", "med_amphotericin", "med_cresemba", "med_tocilizumab",
                                 "med_oseltamivir", "med_ampholyn", "med_posaconazole", "med_fabiflu", "oxy_concentrator", "oxy_cylinder", "oxy_refill", "oxy_regulator"]

    if resource_type is None or city is None or resource_type.lower() not in supported_resource_type:
        return "Invalid Input!!!", 400, headers
    else:
        city = urllib.parse.quote(city).lower()
        resource_type = urllib.parse.quote(resource_type).lower()

    page_size = 12
    if page_no is not None:
        record_slice = slice((page_no - 1) * page_size, page_no * page_size)
    elif record_offset is not None and record_count is not None:
        record_slice = slice(record_offset, record_offset + record_count)
    else:
        record_slice = slice(page_size)

    res_info_filter_id = "city=" + city + "&resource_type=" + resource_type
    update_stats(res_info_filter_id, db)

    # ======================fetching resource======================
    res_info_doc = db.collection('filtered_aggregated_resource_info'). \
        document(res_info_filter_id).get()

    if not res_info_doc.exists:
        resync_invoke_schedule(res_info_filter_id)
        return "Collecting data... Try again after few seconds", 202, headers

    resources = res_info_doc.get(db.field_path('resource_info_data'))
    res_info_data = resources[record_slice]
    more_data_available = len(resources) > record_slice.stop

    response_dict = {
        "meta_info": {
            "more_data_available": more_data_available,
            "total_records": len(resources)
        },
        "resource_info_data": res_info_data
    }
    return json.dumps(response_dict, cls=DateTimeEncoder), 200, headers


def update_stats(res_info_filter_id: str, db):
    filter_stat_doc = db.collection('filter_stats'). \
        document(res_info_filter_id).get()

    query_time = {"last_query_time_utc": DatetimeWithNanoseconds.today()}
    if not filter_stat_doc.exists:
        db.collection('filter_stats').add(query_time, res_info_filter_id)
    else:
        db.collection('filter_stats'). \
            document(res_info_filter_id).set(query_time)


# Publishes a message to a Cloud Pub/Sub topic.
def resync_invoke_schedule(res_info_filter_id: str):
    # Instantiates a Pub/Sub client
    publisher = pubsub_v1.PublisherClient()
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')

    # References an existing topic
    topic_path = publisher.topic_path(PROJECT_ID, "aggregate-topic")

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
