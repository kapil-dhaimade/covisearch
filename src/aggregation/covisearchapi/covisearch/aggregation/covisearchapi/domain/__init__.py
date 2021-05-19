from abc import ABC, abstractmethod
from json import JSONEncoder
import google.cloud.firestore as firestore
import json
from google.api_core.datetime_helpers import DatetimeWithNanoseconds


def fetch_resource_for_filter(request_json):
    search_filter = request_json["search_filter"]
    page_no = request_json["page_no"]

    if search_filter is None:
        raise ValueError("Invalid Input")

    if page_no is None:
        page_no = 1
    elif not isinstance(page_no, int):
        raise ValueError("Invalid Input")

    # This is auto-initialized when main program loads
    db = firestore.Client()

    res_info_filter_id = "city="+search_filter["city"]+"&resource-type="+search_filter["resource-type"]
    res_info_doc = db.collection('filtered-aggregated-resource-info'). \
        document(res_info_filter_id).get()

    if not res_info_doc.exists:
        return None

    resources = res_info_doc.get(db.field_path('res-info-data'))
    page_size = 10
    if len(resources) < page_no * page_size:
        raise LookupError("Data not aggregated yet")
    else:
        return json.dumps({"res-info-data":resources[(page_no-1)*page_size:page_no*page_size]}, cls=DateTimeEncoder)


class DateTimeEncoder(JSONEncoder):
    # Override the default method
    def default(self, obj):
        if isinstance(obj, DatetimeWithNanoseconds):
            return obj.isoformat()