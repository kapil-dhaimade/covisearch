from enum import Enum
from typing import List, Dict, Tuple
import re
import datetime
from datetime import datetime
from dateutil import relativedelta

from covisearch.util.types import *
import covisearch.aggregation.aggregator.domain.entities as entities
from covisearch.aggregation.aggregator.domain.entities import CovidResourceInfo, CovidResourceType


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


class DatetimeFormat(enum.Enum):
    # '5 hours ago' OR '2 days ago' manner
    AGO = 1,
    UTC_TIMESTAMP = 2,
    # 2/05 5:35 PM OR 27/12 at 6:09 AM
    DD_SLASH_MM_H_M_12 = 3


def datetime_format_to_str(datetime_format: DatetimeFormat) -> str:
    datetime_format_strings = {
        DatetimeFormat.AGO: 'ago',
        DatetimeFormat.UTC_TIMESTAMP: 'utc-timestamp'
    }
    return datetime_format_strings[datetime_format]


def datetime_format_from_str(datetime_format_str: str) -> DatetimeFormat:
    datetime_formats = {
        'ago': DatetimeFormat.AGO,
        'utc-timestamp': DatetimeFormat.UTC_TIMESTAMP
    }
    return datetime_formats[datetime_format_str]


# NOTE: KAPIL: Refer 'https://regexr.com/' to test out regex
def map_ago_format_timestamp_to_covisearch(ago_format_datetime: str) -> datetime:
    # Minutes
    re_minutes_result = re.search('(\d+|a)\s+minutes?\s+ago', ago_format_datetime, re.IGNORECASE)
    if re_minutes_result is not None:
        mins_ago_str = re_minutes_result.group(1)
        if mins_ago_str.lower() == 'a':
            mins_ago = 1
        else:
            mins_ago = float(mins_ago_str)
        return datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=mins_ago)

    # Hours
    re_hours_result = re.search('(\d+|an)\s+hours?\s+ago', ago_format_datetime, re.IGNORECASE)
    if re_hours_result is not None:
        hrs_ago_str = re_hours_result.group(1)
        if hrs_ago_str.lower() == 'an':
            hrs_ago = 1
        else:
            hrs_ago = float(hrs_ago_str)
        return datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hrs_ago)

    # Days
    re_days_result = re.search('(\d+|a)\s+days?\s+ago', ago_format_datetime, re.IGNORECASE)
    if re_days_result is not None:
        days_ago_str = re_days_result.group(1)
        if days_ago_str.lower() == 'a':
            days_ago = 1
        else:
            days_ago = float(days_ago_str)
        return datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_ago)

    # Weeks
    re_weeks_result = re.search('(\d+|a)\s+weeks?\s+ago', ago_format_datetime, re.IGNORECASE)
    if re_weeks_result is not None:
        weeks_ago_str = re_weeks_result.group(1)
        if weeks_ago_str.lower() == 'a':
            weeks_ago = 1
        else:
            weeks_ago = float(weeks_ago_str)
        return datetime.now(datetime.timezone.utc) - datetime.timedelta(weeks=weeks_ago)

    # Months
    re_months_result = re.search('(\d+|a)\s+months?\s+ago', ago_format_datetime, re.IGNORECASE)
    if re_months_result is not None:
        months_ago_str = re_months_result.group(1)
        if months_ago_str.lower() == 'a':
            months_ago = 1
        else:
            months_ago = float(months_ago_str)
        return datetime.now(datetime.timezone.utc) - relativedelta(months=months_ago)

    # Years
    re_years_result = re.search('(\d+|a)\s+years?\s+ago', ago_format_datetime, re.IGNORECASE)
    if re_years_result is not None:
        years_ago_str = re_years_result.group(1)
        if years_ago_str.lower() == 'a':
            years_ago = 1
        else:
            years_ago = float(years_ago_str)
        return datetime.now(datetime.timezone.utc) - relativedelta(years=years_ago)
# verified/updated time, phone number separation, mandatory, remove chars
# ----Covid Resource Web Source - ENDS ----
