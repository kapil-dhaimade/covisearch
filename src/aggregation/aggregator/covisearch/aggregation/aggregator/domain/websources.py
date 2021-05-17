from enum import Enum
from typing import List, Dict, Tuple
import re
from datetime import datetime, timezone
from dateutil import tz

from covisearch.util.types import *
import covisearch.aggregation.aggregator.domain.entities as entities
from covisearch.aggregation.aggregator.domain.entities import \
    CovidResourceInfo, CovidResourceType, VerificationInfo, OxygenInfo, \
    PlasmaInfo, HospitalBedsInfo
import covisearch.util.datetimeutil


# NOTE: KAPIL: Python Dict convertible to JSON provided data types are
# serializable. 'None' gets converted to 'null' in JSON. Dict has objects
# like datetime, etc. as values, but JSON needs it to be serializable.
# Need to use JSONEncoder to serialize datetime, etc.


# Classes related to Covid resource websites and resource mapping
class WebSourceType(Enum):
    PAN_INDIA = 1,
    CITY_SPECIFIC = 2,
    RESOURCE_SPECIFIC = 3


class WebSource:
    def __init__(self, homepage_url: URL, web_resource_url: URL, source_type: WebSourceType,
                 response_content_type: ContentType,
                 data_table_extract_selectors: List[Tuple[str, str]],
                 res_mapping_desc: Dict[str, 'FieldMappingDesc']):
        self._homepage_url: URL = homepage_url
        self._web_resource_url = web_resource_url
        self._source_type: WebSourceType = source_type
        self._response_content_type: ContentType = response_content_type
        self._data_table_extract_selectors: List[Tuple[str, str]] = \
            data_table_extract_selectors
        self._res_mapping_desc: Dict[str, 'FieldMappingDesc'] = res_mapping_desc

    @property
    def homepage_url(self) -> URL:
        return self._homepage_url

    @property
    def web_resource_url(self) -> URL:
        return self._web_resource_url

    @property
    def source_type(self) -> WebSourceType:
        return self._source_type

    @property
    def response_content_type(self) -> ContentType:
        return self._response_content_type

    @property
    def data_table_extract_selectors(self) -> List[Tuple[str, str]]:
        return self._data_table_extract_selectors

    @property
    def res_mapping_desc(self) -> Dict[str, 'FieldMappingDesc']:
        return self._res_mapping_desc


# maps covid resource from third-party source format to Covisearch format
def map_to_covisearch(web_src_res: Dict, res_type: CovidResourceType,
                      res_mapping_desc: Dict[str, 'FieldMappingDesc']) -> Dict:
    covisearch_res_info = {
        CovidResourceInfo.RESOURCE_TYPE_LABEL: CovidResourceType.to_string(res_type)
    }
    _map_common_res_info(web_src_res, res_mapping_desc, covisearch_res_info)
    map_specific_res_info = _get_specific_res_info_mapper(res_type)
    map_specific_res_info(web_src_res, res_mapping_desc, covisearch_res_info)
    return covisearch_res_info


def _get_specific_res_info_mapper(res_type: CovidResourceType):
    _web_res_to_covisearch_res_mapper = {
        entities.CovidResourceType.PLASMA: _map_plasma,
        entities.CovidResourceType.OXYGEN: _map_oxygen,
        entities.CovidResourceType.HOSPITAL_BED: _map_hospital_bed,
        entities.CovidResourceType.HOSPITAL_BED_ICU: _map_hospital_bed,
    }
    return _web_res_to_covisearch_res_mapper[res_type]


def _map_common_res_info(web_src_res: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                         covisearch_res: Dict):
    contact_name_label = CovidResourceInfo.CONTACT_NAME_LABEL
    name_mapping = res_mapping_desc[contact_name_label]
    covisearch_res[contact_name_label] = web_src_res[name_mapping.web_src_field_name]

    address_label = CovidResourceInfo.ADDRESS_LABEL
    if address_label in res_mapping_desc:
        address_mapping = res_mapping_desc[address_label]
        covisearch_res[address_label] = \
            _sanitize_string_field(web_src_res[address_mapping.web_src_field_name])
    else:
        covisearch_res[address_label] = ''

    phone_label = CovidResourceInfo.PHONE_NO_LABEL
    phone_mapping = res_mapping_desc[phone_label]
    covisearch_res[phone_label] = \
        _sanitize_string_field(web_src_res[phone_mapping.web_src_field_name])

    details_label = CovidResourceInfo.DETAILS_LABEL
    if details_label in res_mapping_desc:
        details_mapping = res_mapping_desc[details_label]
        covisearch_res[details_label] = \
            _sanitize_string_field(web_src_res[details_mapping.web_src_field_name])
    else:
        covisearch_res[details_label] = ''

    post_time_label = CovidResourceInfo.POST_TIME_LABEL
    if post_time_label in res_mapping_desc:
        post_time_mapping = res_mapping_desc[post_time_label]
        web_src_post_time = web_src_res[post_time_mapping.web_src_field_name]
        map_web_src_datetime_to_covisearch = \
            get_datetime_format_mapper(post_time_mapping.datetime_fmt)
        covisearch_res[post_time_label] = map_web_src_datetime_to_covisearch(web_src_post_time)
    else:
        covisearch_res[post_time_label] = None

    last_verified_label = VerificationInfo.LAST_VERIFIED_UTC_LABEL
    last_verified_mapping = res_mapping_desc[last_verified_label]
    web_src_last_verified_time = web_src_res[last_verified_mapping.web_src_field_name]
    map_web_src_datetime_to_covisearch = \
        get_datetime_format_mapper(last_verified_mapping.datetime_fmt)
    covisearch_res[CovidResourceInfo.VERIFICATION_INFO_LABEL] = \
        {last_verified_label: map_web_src_datetime_to_covisearch(web_src_last_verified_time)}


# TODO: KAPIL: Add proper details for specific res types later if websites give the info.
def _map_plasma(web_src_res: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                covisearch_res: Dict):
    covisearch_res[PlasmaInfo.BLOOD_GROUP_LABEL] = None


def _map_oxygen(web_src_res: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                covisearch_res: Dict):
    covisearch_res[OxygenInfo.LITRES_LABEL] = None


re_available_beds_pattern = re.compile('(\d+)', re.IGNORECASE)


def _map_hospital_bed(web_src_res: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                      covisearch_res: Dict):
    available_beds_label = HospitalBedsInfo.AVAILABLE_BEDS_LABEL
    if available_beds_label in res_mapping_desc:
        available_beds_mapping = res_mapping_desc[available_beds_label]
        web_src_available_beds = web_src_res[available_beds_mapping.web_src_field_name]
        re_available_beds_result = re_available_beds_pattern.search(web_src_available_beds)
        if re_available_beds_result is not None:
            covisearch_res[available_beds_label] = int(re_available_beds_result.group(1))
        else:
            covisearch_res[available_beds_label] = None
    else:
        covisearch_res[available_beds_label] = None


def _sanitize_string_field(field_value: str):
    sanitized_field = field_value.strip()
    sanitized_field = sanitized_field.replace('\n', ', ')
    sanitized_field = sanitized_field.replace('\r', '')
    sanitized_field = sanitized_field.replace('\t', ' ')
    return sanitized_field


# NOTE: KAPIL: Desc format:
# -Tuple['covisearch_res_field_name',
#        'datetimeformat(ago/isoformat/short-datetime-dd-mm),<web_src_field_name>']
# Eg: last verified, web src res format is 'hours/days ago', convert to UTC
#       -('last_verified_utc', 'datetimeformat(ago),lastVerified')
class FieldMappingDesc:
    DATETIMEFORMAT_TOKEN = 'datetimeformat'
    re_datetime_fmt_str_pattern = re.compile('\((.*)\)')

    def __init__(self, field_mapping_desc: Tuple[str, str]):
        self._covisearch_field_name: str = field_mapping_desc[0]
        mapping_desc_tokens = self._split_mapping_desc_csv(field_mapping_desc[1])
        self._web_src_field_name: str = mapping_desc_tokens.pop()
        self._datetime_fmt: covisearch.util.datetimeutil.DatetimeFormat = \
            self._get_datetime_fmt_if_specified(mapping_desc_tokens)

    @property
    def covisearch_field_name(self) -> str:
        return self._covisearch_field_name

    @property
    def web_src_field_name(self) -> str:
        return self._web_src_field_name

    @property
    def datetime_fmt(self) -> covisearch.util.datetimeutil.DatetimeFormat:
        return self._datetime_fmt

    @classmethod
    def _get_datetime_fmt_if_specified(cls, mapping_desc_tokens):
        datetimeformat_mapping_token = [fmt for fmt in mapping_desc_tokens if
                                        FieldMappingDesc.DATETIMEFORMAT_TOKEN in fmt]
        if datetimeformat_mapping_token is not []:
            datetimefmt_mapping = datetimeformat_mapping_token[0]
            datetime_fmt_str = cls.re_datetime_fmt_str_pattern.search(
                datetimefmt_mapping).group(1)
            return datetime_format_from_str(datetime_fmt_str)
        else:
            return None

    @staticmethod
    def _split_mapping_desc_csv(desc: str) -> List[str]:
        return desc.split(',')


def get_datetime_format_mapper(datetime_fmt: covisearch.util.datetimeutil.DatetimeFormat):
    datetime_fmt_mapper = {
        covisearch.util.datetimeutil.DatetimeFormat.AGO:
            map_ago_format_timestamp_to_covisearch,
        covisearch.util.datetimeutil.DatetimeFormat.ISOFORMAT:
            map_isoformat_timestamp_to_covisearch,
        covisearch.util.datetimeutil.DatetimeFormat.SHORT_DATETIME_DD_MM:
            map_short_datetime_timestamp_to_covisearch
    }
    return datetime_fmt_mapper[datetime_fmt]


def map_ago_format_timestamp_to_covisearch(ago_format_datetime: str) -> datetime:
    return covisearch.util.datetimeutil.\
        map_ago_format_timestamp_to_isoformat(ago_format_datetime)


def map_isoformat_timestamp_to_covisearch(isoformat_datetime_str: str) -> datetime:
    covisearch_datetime = datetime.fromisoformat(isoformat_datetime_str)
    # NOTE: KAPIL: Since we operate in IST, setting default to IST.
    # Need to change if region changes or becomes multi-region.
    covisearch_datetime = _set_timezone_ist_if_not_present(covisearch_datetime)
    covisearch_datetime = covisearch_datetime.astimezone(tz=timezone.utc)
    return covisearch_datetime


def map_short_datetime_timestamp_to_covisearch(short_datetime_str) -> datetime:
    return covisearch.util.datetimeutil.map_short_datetime_dd_mm_to_isoformat(short_datetime_str)


def datetime_format_to_str(datetime_format: covisearch.util.datetimeutil.DatetimeFormat) -> str:
    datetime_format_strings = {
        covisearch.util.datetimeutil.DatetimeFormat.AGO: 'ago',
        covisearch.util.datetimeutil.DatetimeFormat.ISOFORMAT: 'isoformat',
        covisearch.util.datetimeutil.DatetimeFormat.SHORT_DATETIME_DD_MM:
            'short-datetime-dd-mm'
    }
    return datetime_format_strings[datetime_format]


def datetime_format_from_str(datetime_format_str: str) -> \
        covisearch.util.datetimeutil.DatetimeFormat:
    datetime_formats = {
        'ago': covisearch.util.datetimeutil.DatetimeFormat.AGO,
        'isoformat': covisearch.util.datetimeutil.DatetimeFormat.ISOFORMAT,
        'short-datetime-dd-mm':
            covisearch.util.datetimeutil.DatetimeFormat.SHORT_DATETIME_DD_MM
    }
    return datetime_formats[datetime_format_str]


def _set_timezone_ist_if_not_present(timestamp: datetime) -> datetime:
    if not covisearch.util.datetimeutil.is_timezone_aware(timestamp):
        timestamp = timestamp.replace(tzinfo=tz.gettz('Asia/Kolkata'))
    return timestamp
# verified/updated time, phone number separation, mandatory, remove chars
# ----Covid Resource Web Source - ENDS ----


if __name__ == '__main__':

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
