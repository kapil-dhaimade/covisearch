from enum import Enum
from typing import List, Dict, Tuple
import re
from datetime import datetime, timezone
from dateutil import tz

from covisearch.util.types import *
import covisearch.aggregation.aggregator.domain.entities as entities
from covisearch.aggregation.aggregator.domain.entities import CovidResourceInfo, CovidResourceType
import covisearch.util.datetimeutil


# NOTE: KAPIL: Python Dict convertible to JSON provided data types are
# serializable. None gets converted to null in JSON. Dict has objects
# like datetime, etc. as values, but JSON needs it to be serializable.


# Classes related to Covid resource websites and resource mapping
class WebSourceType(Enum):
    PAN_INDIA = 1,
    CITY_SPECIFIC = 2,
    RESOURCE_SPECIFIC = 3


class WebSource:
    def __init__(self, url: URL, source_type: WebSourceType,
                 response_content_type: ContentType,
                 data_table_extract_selectors: List[Tuple[str, str]],
                 res_mapping_desc: List[Tuple[str, str]]):
        self._url: URL = url
        self._source_type: WebSourceType = source_type
        self._response_content_type: ContentType = response_content_type
        self._data_table_extract_selectors: List[Tuple[str, str]] = \
            data_table_extract_selectors
        self._res_mapping_desc: List[Tuple[str, str]] = res_mapping_desc


# maps covid resource from third-party source format to Covisearch format
def map_to_covisearch(web_src_res_info: Dict, res_type: CovidResourceType,
                      res_mapping_desc: List[Tuple[str, str]]) -> CovidResourceInfo:
    _map_res_to_covisearch_res = {
        entities.CovidResourceType.PLASMA: _map_plasma,
        entities.CovidResourceType.OXYGEN: _map_oxygen,
        entities.CovidResourceType.HOSPITAL_BED: _map_hospital_bed,
        entities.CovidResourceType.HOSPITAL_BED_ICU: _map_hospital_bed_icu,
    }
    covisearch_res: Dict = {}
    _map_common_res_info(web_src_res_info, res_mapping_desc, covisearch_res)
    _map_res_to_covisearch_res[res_type](web_src_res_info, res_mapping_desc, covisearch_res)
    return None


def _map_plasma(web_src_res_info: Dict, res_mapping_desc: List[Tuple[str, str]],
                covisearch_res: Dict):
    pass


def _map_oxygen(web_src_res_info: Dict, res_mapping_desc: List[Tuple[str, str]],
                covisearch_res: Dict):
    pass


def _map_hospital_bed(web_src_res_info: Dict, res_mapping_desc: List[Tuple[str, str]],
                      covisearch_res: Dict):
    pass


def _map_hospital_bed_icu(web_src_res_info: Dict, res_mapping_desc: List[Tuple[str, str]],
                          covisearch_res: Dict):
    pass


def _map_common_res_info(web_src_res_info: Dict, res_mapping_desc: List[Tuple[str, str]],
                         covisearch_res: Dict):
    for field_mapping in res_mapping_desc:
        pass


# NOTE: KAPIL: Desc format:
# -Tuple['covisearch_res_field_name',
#        'mandatory,remove-chars(chars),split-on(delim),datetimeformat(ago/none),<web_src_field_name>']
# Eg: Mandatory field, remove '+' and 'space' chars, split multiple numbers on '\n'
#       -('phone_no', 'mandatory,remove-chars(+ ),split-on(\n),mobile-nos')
# Eg: Optional last verified, web src res format is 'hours/days ago', convert to UTC
#       -('last_verified_utc', 'datetimeformat(ago),lastVerified')
# TODO: KAPIL: Implement mandatory, remove_chars(), split_on() later.
class FieldMappingDesc:
    DATETIMEFORMAT_TOKEN = 'datetimeformat'

    def __init__(self, field_mapping_desc: Tuple[str, str]):
        self._covisearch_field_name = field_mapping_desc[0]
        mapping_desc_tokens = self._split_mapping_desc_csv(field_mapping_desc[1])
        self._web_src_field_name = mapping_desc_tokens.pop()
        self._datetime_fmt_mapping = self._get_datetime_fmt_mapping_if_present(mapping_desc_tokens)

    @staticmethod
    def _get_datetime_fmt_mapping_if_present(mapping_desc_tokens):
        datetimeformat_mapping_token = [fmt for fmt in mapping_desc_tokens if
                                         FieldMappingDesc.DATETIMEFORMAT_TOKEN in fmt]
        if datetimeformat_mapping_token is not []:
            datetimefmt_mapping = datetimeformat_mapping_token[0]
            datetime_fmt_str = re.search('\((.*)\)', datetimefmt_mapping).group(1)
            return datetime_format_from_str(datetime_fmt_str)
        else:
            return None

    @staticmethod
    def _split_mapping_desc_csv(desc: str) -> List[str]:
        return desc.split(',')


def datetime_format_to_str(datetime_format: covisearch.util.datetimeutil.DatetimeFormat) -> str:
    datetime_format_strings = {
        covisearch.util.datetimeutil.DatetimeFormat.AGO: 'ago',
        covisearch.util.datetimeutil.DatetimeFormat.ISOFORMAT: 'isoformat',
        covisearch.util.datetimeutil.DatetimeFormat.SHORT_DATETIME: 'short-datetime'
    }
    return datetime_format_strings[datetime_format]


def datetime_format_from_str(datetime_format_str: str) -> \
        covisearch.util.datetimeutil.DatetimeFormat:
    datetime_formats = {
        'ago': covisearch.util.datetimeutil.DatetimeFormat.AGO,
        'isoformat': covisearch.util.datetimeutil.DatetimeFormat.ISOFORMAT,
        'short-datetime': covisearch.util.datetimeutil.DatetimeFormat.SHORT_DATETIME
    }
    return datetime_formats[datetime_format_str]


# NOTE: KAPIL: Refer 'https://regexr.com/' to test out regex
def map_ago_format_timestamp_to_covisearch(ago_format_datetime: str) -> datetime:
    return covisearch.util.datetimeutil.\
        map_ago_format_timestamp_to_isoformat(ago_format_datetime)


def map_isoformat_timestamp_to_covisearch(isoformat_datetime_str: str) -> datetime:
    covisearch_datetime = datetime.fromisoformat(isoformat_datetime_str)
    # NOTE: KAPIL: Since we operate in IST, setting default to IST.
    # Need to change if region changes or becomes multi-region.
    covisearch_datetime = set_timezone_ist_if_not_present(covisearch_datetime)
    covisearch_datetime = covisearch_datetime.astimezone(tz=timezone.utc)
    return covisearch_datetime


def map_short_datetime_timestamp_to_covisearch(short_datetime_str) -> datetime:
    covisearch.util.datetimeutil.map_short_datetime_dd_mm_to_isoformat(short_datetime_str)


def set_timezone_ist_if_not_present(timestamp: datetime) -> datetime:
    if not covisearch.util.datetimeutil.is_timezone_aware(timestamp):
        timestamp = timestamp.replace(tzinfo=tz.gettz('Asia/Kolkata'))
    return timestamp
# verified/updated time, phone number separation, mandatory, remove chars
# ----Covid Resource Web Source - ENDS ----


if __name__ == '__main__':

    dt = datetime.fromisoformat('2021-05-16T21:06:17.000000')
    dt = dt.replace(tzinfo=tz.gettz('America/New_York'))
    dt = dt.astimezone(tz=timezone.utc)
    st = dt.isoformat()
    # print('a minute ago = ' + str(map_ago_format_timestamp_to_covisearch('a minute ago')))
    # print('an hour ago = ' + str(map_ago_format_timestamp_to_covisearch('an hour ago')))
    # print('a day ago = ' + str(map_ago_format_timestamp_to_covisearch('a day ago')))
    # print('a week ago = ' + str(map_ago_format_timestamp_to_covisearch('a week ago')))
    # print('a month ago = ' + str(map_ago_format_timestamp_to_covisearch('a month ago')))
    # print('a year ago = ' + str(map_ago_format_timestamp_to_covisearch('a year ago')))
    #
    # print('1 minute ago = ' + str(map_ago_format_timestamp_to_covisearch('1 minute ago')))
    # print('1 hour ago = ' + str(map_ago_format_timestamp_to_covisearch('1 hour ago')))
    # print('1 day ago = ' + str(map_ago_format_timestamp_to_covisearch('1 day ago')))
    # print('1 week ago = ' + str(map_ago_format_timestamp_to_covisearch('1 week ago')))
    # print('1 month ago = ' + str(map_ago_format_timestamp_to_covisearch('1 month ago')))
    # print('1 year ago = ' + str(map_ago_format_timestamp_to_covisearch('1 year ago')))
    #
    # print('5 minutes ago = ' + str(map_ago_format_timestamp_to_covisearch('5 minutes ago')))
    # print('5 hours ago = ' + str(map_ago_format_timestamp_to_covisearch('5 hours ago')))
    # print('5 days ago = ' + str(map_ago_format_timestamp_to_covisearch('5 days ago')))
    # print('5 weeks ago = ' + str(map_ago_format_timestamp_to_covisearch('5 weeks ago')))
    # print('5 months ago = ' + str(map_ago_format_timestamp_to_covisearch('5 months ago')))
    # print('5 years ago = ' + str(map_ago_format_timestamp_to_covisearch('5 years ago')))
    #
    # print('15 minutes ago = ' + str(map_ago_format_timestamp_to_covisearch('15 minutes ago')))
    # print('15 days ago = ' + str(map_ago_format_timestamp_to_covisearch('15 days ago')))
    # print('15 weeks ago = ' + str(map_ago_format_timestamp_to_covisearch('15 weeks ago')))
    # print('15 hours ago = ' + str(map_ago_format_timestamp_to_covisearch('15 hours ago')))
    # print('6 months ago = ' + str(map_ago_format_timestamp_to_covisearch('6 months ago')))
    # print('3 years ago = ' + str(map_ago_format_timestamp_to_covisearch('3 years ago')))
    #
    # print('150 minutes ago = ' + str(map_ago_format_timestamp_to_covisearch('150 minutes ago')))
    # print('72 hours ago = ' + str(map_ago_format_timestamp_to_covisearch('72 hours ago')))
    # print('40 days ago = ' + str(map_ago_format_timestamp_to_covisearch('40 days ago')))
    # print('18 months ago = ' + str(map_ago_format_timestamp_to_covisearch('18 months ago')))
    print('end')
