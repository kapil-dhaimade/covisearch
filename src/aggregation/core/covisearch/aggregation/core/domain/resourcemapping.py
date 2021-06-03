from enum import Enum
from typing import List, Dict, Tuple
import re
from datetime import datetime, timezone
from dateutil import tz
import dateutil.parser as dateutilparser
from abc import ABC, abstractmethod
import urllib.parse

from phonenumbers import PhoneNumberMatcher, format_number, PhoneNumberFormat

from covisearch.util.mytypes import *
import covisearch.aggregation.core.domain.entities as entities
from covisearch.aggregation.core.domain.entities import \
    CovidResourceInfo, CovidResourceType, OxygenInfo, BloodInfo, \
    PlasmaInfo, HospitalBedsInfo, SearchFilter, HospitalBedsICUInfo
import covisearch.util.datetimeutil
import covisearch.util.geoutil as geoutil


# NOTE: KAPIL: Python Dict convertible to JSON provided data types are
# serializable. 'None' gets converted to 'null' in JSON. Dict has objects
# like datetime, etc. as values, but JSON needs it to be serializable.
# Need to use JSONEncoder to serialize datetime, etc.


# Classes related to Covid resource websites and resource mapping
def map_res_info_to_covisearch(web_src_res_info: Dict, search_filter: SearchFilter,
                               web_src: 'WebSource') -> Dict:
    covisearch_res_info = {
        # NOTE: KAPIL: Commenting for now as res-type and city are redundant.
        # CovidResourceInfo.RESOURCE_TYPE_LABEL:
        #     CovidResourceType.to_string(search_filter.resource_type),
        # CovidResourceInfo.CITY_LABEL: search_filter.city,
        CovidResourceInfo.WEB_SOURCE_NAME_LABEL: web_src.name,
        CovidResourceInfo.CARD_SOURCE_URL_LABEL: web_src.card_source_url,
        CovidResourceInfo.SOURCES_LABEL: [
            {
                CovidResourceInfo.SOURCE_NAME_LABEL: web_src.name,
                CovidResourceInfo.SOURCE_URL_LABEL: web_src.card_source_url
            }
        ]
    }

    _map_common_res_info(web_src_res_info, web_src.resource_mapping_desc, covisearch_res_info, search_filter)
    map_specific_res_info = _get_specific_res_info_mapper(search_filter.resource_type)
    map_specific_res_info(web_src_res_info, web_src.resource_mapping_desc, covisearch_res_info)
    return covisearch_res_info


class WebSource:
    WEB_SRC_CITY_PLACEHOLDER = '{CITY}'
    WEB_SRC_RESOURCE_TYPE_PLACEHOLDER = '{RESOURCE_TYPE}'
    WEB_SRC_STATE_PLACEHOLDER = '{STATE}'

    def __init__(self, name: str, homepage_url: URL, web_resource_url_template: URL,
                 card_source_url_template: URL,
                 request_content_type: ContentType, request_body_template: str,
                 response_content_type: ContentType,
                 data_table_extract_selectors: Dict[str, str],
                 data_table_filter_templates: Dict[str, str],
                 resource_mapping_desc: Dict[str, 'FieldMappingDesc'],
                 resource_type_label_mapping: Dict[str, str],
                 city_name_case_mapping: LetterCaseType, search_filter: SearchFilter):

        self._name = name
        self._homepage_url: URL = homepage_url
        web_src_city = self._map_to_web_src_city_by_letter_case_mapping(
            search_filter.city, city_name_case_mapping)
        # NOTE: KAPIL: URL with place-holders for search filter params in {param} blocks
        # Eg: http://covidres.com/city={CITY}&resource={RESOURCE_TYPE}
        self._web_resource_url = self._url_from_template(
            web_resource_url_template, web_src_city, search_filter, resource_type_label_mapping)
        self._card_source_url: URL = self._url_from_template(
            card_source_url_template, web_src_city, search_filter, resource_type_label_mapping)

        self._request_content_type: ContentType = request_content_type
        self._request_body: str = self._request_body_from_template(
            request_body_template, web_src_city, search_filter, resource_type_label_mapping)
        self._response_content_type: ContentType = response_content_type

        self._data_table_extract_selectors: Dict[str, str] = \
            data_table_extract_selectors
        self._data_table_filters: Dict[str, str] = self._data_table_filters_from_templates(
            data_table_filter_templates, web_src_city, search_filter, resource_type_label_mapping)

        self._resource_mapping_desc: Dict[str, 'FieldMappingDesc'] = resource_mapping_desc

    @property
    def name(self) -> str:
        return self._name

    @property
    def homepage_url(self) -> URL:
        return self._homepage_url

    @property
    def card_source_url(self) -> URL:
        return self._card_source_url

    @property
    def web_resource_url(self) -> URL:
        return self._web_resource_url

    @property
    def request_content_type(self) -> ContentType:
        return self._request_content_type

    @property
    def request_body(self) -> str:
        return self._request_body

    @property
    def response_content_type(self) -> ContentType:
        return self._response_content_type

    @property
    def data_table_extract_selectors(self) -> Dict[str, str]:
        return self._data_table_extract_selectors

    @property
    def data_table_filters(self) -> Dict[str, str]:
        return self._data_table_filters

    @property
    def resource_mapping_desc(self) -> Dict[str, 'FieldMappingDesc']:
        return self._resource_mapping_desc

    @classmethod
    def _url_from_template(
            cls, url_template: URL, web_src_city: str, search_filter: SearchFilter,
            resource_type_label_mapping: Dict[str, str]) -> URL:
        if url_template is None:
            return ''

        url = url_template

        url = url.replace(
            cls.WEB_SRC_CITY_PLACEHOLDER,
            urllib.parse.quote(web_src_city))

        possible_states = geoutil.get_states_for_city(search_filter.city)
        if possible_states:
            url = url.replace(cls.WEB_SRC_STATE_PLACEHOLDER, possible_states[0])

        filter_res_type_str = CovidResourceType.to_string(search_filter.resource_type)

        if filter_res_type_str not in resource_type_label_mapping:
            raise NoResourceTypeMappingError()

        url = url.replace(
            cls.WEB_SRC_RESOURCE_TYPE_PLACEHOLDER,
            urllib.parse.quote(resource_type_label_mapping[filter_res_type_str]))

        # TODO: KAPIL: Blood group filter mapping
        return url

    @classmethod
    def _request_body_from_template(cls, request_body_template: str, web_src_city: str, search_filter: SearchFilter,
                                    resource_type_label_mapping: Dict[str, str]) -> str:
        if request_body_template is None:
            return None

        request_body = request_body_template
        request_body = request_body.replace(cls.WEB_SRC_CITY_PLACEHOLDER, web_src_city)

        possible_states = geoutil.get_states_for_city(search_filter.city)
        if possible_states:
            request_body = request_body.replace(
                cls.WEB_SRC_STATE_PLACEHOLDER, possible_states[0])

        filter_res_type_str = CovidResourceType.to_string(search_filter.resource_type)

        if filter_res_type_str not in resource_type_label_mapping:
            raise NoResourceTypeMappingError()
        request_body = request_body.replace(
            cls.WEB_SRC_RESOURCE_TYPE_PLACEHOLDER,
            resource_type_label_mapping[filter_res_type_str])

        # TODO: KAPIL: Blood group filter mapping
        return request_body

    @classmethod
    def _map_to_web_src_city_by_letter_case_mapping(cls, city: str, city_case_mapping: LetterCaseType) -> str:
        if city_case_mapping is None:
            return city

        if city_case_mapping is LetterCaseType.LOWERCASE:
            return city.lower()

        if city_case_mapping is LetterCaseType.UPPERCASE:
            return city.upper()

        if city_case_mapping is LetterCaseType.TITLECASE:
            return city.title()

    @classmethod
    def _data_table_filters_from_templates(cls, data_table_filters: Dict[str, str],
                                           web_src_city: str, search_filter: SearchFilter,
                                           resource_type_label_mapping: Dict[str, str]) -> Dict[str, str]:
        if data_table_filters is None:
            return {}
        return {key: cls._data_table_filter_from_template(filter_template, web_src_city, search_filter,
                                                          resource_type_label_mapping)
                for (key, filter_template) in data_table_filters.items()}

    @classmethod
    def _data_table_filter_from_template(cls, data_table_filter_template: str, web_src_city: str,
                                         search_filter: SearchFilter,
                                         resource_type_label_mapping: Dict[str, str]) -> str:
        data_table_filter = data_table_filter_template
        data_table_filter = data_table_filter.replace(cls.WEB_SRC_CITY_PLACEHOLDER, web_src_city)

        possible_states = geoutil.get_states_for_city(search_filter.city)
        if possible_states:
            data_table_filter = data_table_filter.replace(cls.WEB_SRC_STATE_PLACEHOLDER, possible_states[0])

        filter_res_type_str = CovidResourceType.to_string(search_filter.resource_type)

        if filter_res_type_str not in resource_type_label_mapping:
            raise NoResourceTypeMappingError()
        data_table_filter = data_table_filter.replace(cls.WEB_SRC_RESOURCE_TYPE_PLACEHOLDER,
                                                      resource_type_label_mapping[filter_res_type_str])
        return data_table_filter


class NoResourceTypeMappingError(Exception):
    pass


class WebSourceRepo(ABC):
    @abstractmethod
    def get_web_sources_for_filter(self, search_filer: SearchFilter) -> Dict[str, WebSource]:
        raise NotImplementedError()


def _get_specific_res_info_mapper(res_type: CovidResourceType):
    _web_res_to_covisearch_res_mapper = {
        entities.CovidResourceType.PLASMA: _map_plasma,
        entities.CovidResourceType.OXYGEN: _map_oxygen,
        entities.CovidResourceType.HOSPITAL_BED: _map_hospital_bed,
        entities.CovidResourceType.HOSPITAL_BED_ICU: _map_hospital_bed_icu,
        entities.CovidResourceType.AMBULANCE: _map_ambulance,
        entities.CovidResourceType.ECMO: _map_ecmo,
        entities.CovidResourceType.FOOD: _map_food,
        entities.CovidResourceType.TESTING: _map_testing,
        entities.CovidResourceType.MEDICINE: _map_medicine,
        entities.CovidResourceType.VENTILATOR: _map_ventilator,
        entities.CovidResourceType.HELPLINE: _map_helpline,
        entities.CovidResourceType.BLOOD: _map_blood
    }
    return _web_res_to_covisearch_res_mapper[res_type]


def _map_common_res_info(web_src_res_info: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                         covisearch_res: Dict, search_filter: SearchFilter):
    _map_contact_name(covisearch_res, res_mapping_desc, web_src_res_info)

    _map_address(covisearch_res, res_mapping_desc, web_src_res_info)

    _map_phones(covisearch_res, res_mapping_desc, web_src_res_info, search_filter)

    _map_details(covisearch_res, res_mapping_desc, web_src_res_info)

    _map_post_time(covisearch_res, res_mapping_desc, web_src_res_info)

    _map_last_verified_time(covisearch_res, res_mapping_desc, web_src_res_info)

    _map_card_source_url(covisearch_res, res_mapping_desc, web_src_res_info)


def _map_last_verified_time(covisearch_res, res_mapping_desc, web_src_res_info):
    last_verified_label = CovidResourceInfo.LAST_VERIFIED_UTC_LABEL
    if last_verified_label in res_mapping_desc:
        last_verified_mapping = res_mapping_desc[last_verified_label]
        web_src_last_verified_time = web_src_res_info[last_verified_mapping.web_src_field_name]
        map_web_src_datetime_to_covisearch = \
            get_datetime_format_mapper(last_verified_mapping.datetime_fmt)
        try:
            covisearch_res[last_verified_label] = \
                map_web_src_datetime_to_covisearch(web_src_last_verified_time)
        except:
            covisearch_res[last_verified_label] = None
    else:
        covisearch_res[last_verified_label] = None


def _map_post_time(covisearch_res, res_mapping_desc, web_src_res_info):
    post_time_label = CovidResourceInfo.POST_TIME_LABEL
    if post_time_label in res_mapping_desc:
        post_time_mapping = res_mapping_desc[post_time_label]
        web_src_post_time = web_src_res_info[post_time_mapping.web_src_field_name]
        map_web_src_datetime_to_covisearch = \
            get_datetime_format_mapper(post_time_mapping.datetime_fmt)
        try:
            covisearch_res[post_time_label] = \
                map_web_src_datetime_to_covisearch(web_src_post_time)
        except:
            covisearch_res[post_time_mapping] = None
    else:
        covisearch_res[post_time_label] = None


def _map_details(covisearch_res, res_mapping_desc, web_src_res_info):
    details_label = CovidResourceInfo.DETAILS_LABEL
    if details_label in res_mapping_desc:
        details_mapping = res_mapping_desc[details_label]
        covisearch_res[details_label] = \
            _sanitize_string_field(web_src_res_info[details_mapping.web_src_field_name])
    else:
        covisearch_res[details_label] = ''


def _map_phones(covisearch_res, res_mapping_desc, web_src_res_info, search_filter: SearchFilter):
    phone_label = CovidResourceInfo.PHONE_NO_LABEL
    phone_mapping = res_mapping_desc[phone_label]
    web_src_phone_no = web_src_res_info[phone_mapping.web_src_field_name]
    non_uniform_format_phones = _sanitize_phone_no(web_src_phone_no)
    covisearch_res[phone_label] = non_uniform_format_phones

    # NOTE: KAPIL: [AS ON 01-Jun-2021] The new field for keeping phone numbers as uniformized list.
    # Should replace old slash separated string later.
    covisearch_res[CovidResourceInfo.PHONES_LABEL] = \
        _extract_and_uniformized_phones(non_uniform_format_phones, search_filter.city)


def _map_address(covisearch_res, res_mapping_desc, web_src_res_info):
    address_label = CovidResourceInfo.ADDRESS_LABEL
    if address_label in res_mapping_desc:
        address_mapping = res_mapping_desc[address_label]
        covisearch_res[address_label] = \
            _sanitize_string_field(web_src_res_info[address_mapping.web_src_field_name])
    else:
        covisearch_res[address_label] = ''


def _map_contact_name(covisearch_res: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                      web_src_res_info: Dict):
    contact_name_label = CovidResourceInfo.CONTACT_NAME_LABEL
    name_mapping = res_mapping_desc[contact_name_label]
    covisearch_res[contact_name_label] = web_src_res_info[name_mapping.web_src_field_name]


def _map_card_source_url(covisearch_res: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                         web_src_res_info: Dict):
    card_source_url_label = CovidResourceInfo.CARD_SOURCE_URL_LABEL
    if card_source_url_label in res_mapping_desc:
        card_source_url_mapping = res_mapping_desc[card_source_url_label]
        # NOTE: KAPIL:
        # -For cases where post link present in card is relative url, we're
        # appending the relative link to existing card source url in covisearch which comes
        # from DB. In this case the websites which have relative link in post must have
        # card source url in DB as homepage URL so appending makes it full URL.
        # Eg: Covid Fight Club has post link as relative URL. So we append it here and in
        # WebSource of Covid Fight Club, its homepage is present.
        # -If post link is not present, then we should keep proper search filter in card source url
        # in web source.
        # -If post link has absolute URL, then we may not make field for card source url in web source.
        covisearch_res[card_source_url_label] = \
            covisearch_res[card_source_url_label] + web_src_res_info[card_source_url_mapping.web_src_field_name]


# TODO: KAPIL: Add proper details for specific res types later if websites give the info.
def _map_plasma(web_src_res_info: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                covisearch_res: Dict):
    covisearch_res[PlasmaInfo.BLOOD_GROUP_LABEL] = None


def _map_blood(web_src_res_info: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
               covisearch_res: Dict):
    covisearch_res[BloodInfo.BLOOD_GROUP_LABEL] = None


def _map_oxygen(web_src_res_info: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                covisearch_res: Dict):
    covisearch_res[OxygenInfo.LITRES_LABEL] = None


re_available_beds_pattern = re.compile('(\d+)', re.IGNORECASE)


def _map_hospital_bed(web_src_res_info: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                      covisearch_res: Dict):
    _map_bed_field(HospitalBedsInfo.AVAILABLE_COVID_BEDS_LABEL, covisearch_res,
                   res_mapping_desc, web_src_res_info)
    _map_bed_field(HospitalBedsInfo.AVAILABLE_COVID_BEDS_WITHOUT_OXYGEN_LABEL, covisearch_res,
                   res_mapping_desc, web_src_res_info)
    _map_bed_field(HospitalBedsInfo.AVAILABLE_COVID_BEDS_WITH_OXYGEN_LABEL, covisearch_res,
                   res_mapping_desc, web_src_res_info)
    HospitalBedsInfo.add_total_available_beds(covisearch_res)


def _map_hospital_bed_icu(web_src_res_info: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                      covisearch_res: Dict):
    _map_bed_field(HospitalBedsICUInfo.AVAILABLE_ICU_BEDS_LABEL, covisearch_res,
                   res_mapping_desc, web_src_res_info)
    _map_bed_field(HospitalBedsICUInfo.AVAILABLE_ICU_BEDS_WITH_VENTILATOR_LABEL, covisearch_res,
                   res_mapping_desc, web_src_res_info)
    HospitalBedsICUInfo.add_total_available_beds(covisearch_res)


def _map_bed_field(available_covid_beds_label, covisearch_res, res_mapping_desc, web_src_res_info):
    if available_covid_beds_label in res_mapping_desc:
        available_beds_mapping = res_mapping_desc[available_covid_beds_label]
        web_src_available_beds = web_src_res_info[available_beds_mapping.web_src_field_name]
        re_available_beds_result = re_available_beds_pattern.search(web_src_available_beds)
        if re_available_beds_result is not None:
            covisearch_res[available_covid_beds_label] = int(re_available_beds_result.group(1))
        else:
            covisearch_res[available_covid_beds_label] = None
    else:
        covisearch_res[available_covid_beds_label] = None


def _map_ambulance(web_src_res_info: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                   covisearch_res: Dict):
    pass


def _map_ecmo(web_src_res_info: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                   covisearch_res: Dict):
    pass


def _map_food(web_src_res_info: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                   covisearch_res: Dict):
    pass


def _map_testing(web_src_res_info: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                   covisearch_res: Dict):
    pass


def _map_medicine(web_src_res_info: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                  covisearch_res: Dict):
    pass


def _map_ventilator(web_src_res_info: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                    covisearch_res: Dict):
    pass


def _map_helpline(web_src_res_info: Dict, res_mapping_desc: Dict[str, 'FieldMappingDesc'],
                  covisearch_res: Dict):
    pass


# NOTE: KAPIL: Converts all phones to National phone number format for accurate matching.
# Eg: 08080867676, 02228763461
def _extract_and_uniformized_phones(non_uniform_phones: str, city: str) -> List[str]:
    non_uniform_phone_list = non_uniform_phones.split('/')
    return [uniformized_phone for non_uniform_phone_str in non_uniform_phone_list
            for uniformized_phone in _extract_and_uniformize_one_phone_str(non_uniform_phone_str, city)]


# NOTE: KAPIL: Returns list because one phone number string may end up having more than
# one phone number
def _extract_and_uniformize_one_phone_str(non_uniform_phone: str, city: str) -> List[str]:
    # NOTE: KAPIL: Country code is only IN as we operate in India only.
    phone_no_matcher: PhoneNumberMatcher = PhoneNumberMatcher(non_uniform_phone, 'IN')
    if phone_no_matcher.has_next():
        return [format_number(match.number, PhoneNumberFormat.NATIONAL).replace(' ', '')
                for match in phone_no_matcher]
    else:
        uniformized_phone = _retry_uniformize_phone_by_adding_area_code(non_uniform_phone, city)
        return uniformized_phone if uniformized_phone else [non_uniform_phone]


def _retry_uniformize_phone_by_adding_area_code(non_uniform_phone: str, city: str) -> List[str]:
    area_code = geoutil.get_phone_area_code_for_city(city)
    phone_with_area_code = area_code + non_uniform_phone
    phone_no_matcher: PhoneNumberMatcher = PhoneNumberMatcher(phone_with_area_code, 'IN')
    if phone_no_matcher.has_next():
        return [format_number(match.number, PhoneNumberFormat.NATIONAL).replace(' ', '')
                for match in phone_no_matcher]
    else:
        return []


def _sanitize_phone_no(phone_no: str) -> str:
    # NOTE: KAPIL: Intended format: '8888888888/9999999999'
    sanitized_phone_no = phone_no.strip()
    sanitized_phone_no = sanitized_phone_no.replace(' / ', '/')
    sanitized_phone_no = sanitized_phone_no.replace(' , ', '/')
    sanitized_phone_no = sanitized_phone_no.replace(',\n', '/')
    sanitized_phone_no = sanitized_phone_no.replace(', \n', '/')
    sanitized_phone_no = sanitized_phone_no.replace(', ', '/')
    sanitized_phone_no = sanitized_phone_no.replace(',', '/')
    sanitized_phone_no = sanitized_phone_no.replace(' | ', '/')
    sanitized_phone_no = sanitized_phone_no.replace('|', '/')
    sanitized_phone_no = sanitized_phone_no.replace('\n', '/')
    sanitized_phone_no = sanitized_phone_no.replace('\r', '')
    sanitized_phone_no = sanitized_phone_no.replace('\t', ' ')
    return sanitized_phone_no


def _sanitize_string_field(field_value: str) -> str:
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
                                        FieldMappingDesc.DATETIMEFORMAT_TOKEN in fmt.lower()]
        if datetimeformat_mapping_token:
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
            _map_ago_format_timestamp_to_covisearch,
        covisearch.util.datetimeutil.DatetimeFormat.ISOFORMAT:
            _map_isoformat_timestamp_to_covisearch,
        covisearch.util.datetimeutil.DatetimeFormat.SHORT_DATETIME_DD_MM:
            _map_short_datetime_dd_mm_time_to_covisearch,
        covisearch.util.datetimeutil.DatetimeFormat.SHORT_DATETIME_MM_DD:
            _map_short_datetime_mm_dd_time_to_covisearch,
        covisearch.util.datetimeutil.DatetimeFormat.UNIX_TIMESTAMP_SEC:
            _map_unix_timestamp_sec_to_covisearch,
        covisearch.util.datetimeutil.DatetimeFormat.UNIX_TIMESTAMP_MILLISEC:
            _map_unix_timestamp_millisec_to_covisearch
    }
    return datetime_fmt_mapper[datetime_fmt]


def _map_ago_format_timestamp_to_covisearch(ago_format_datetime: str) -> datetime:
    return covisearch.util.datetimeutil.\
        map_ago_format_timestamp_to_utc_datetime(ago_format_datetime)


def _map_isoformat_timestamp_to_covisearch(isoformat_datetime_str: str) -> datetime:
    # NOTE: KAPIL: Not using datetime.fromisoformat() here as it does not parse
    # timestamps with 'Z' suffix. It's supposed to be only inverse of isoformat().
    covisearch_datetime = dateutilparser.parse(isoformat_datetime_str)
    # NOTE: KAPIL: Since we operate in IST, setting default to IST.
    # Need to change if region changes or becomes multi-region.
    covisearch_datetime = _set_timezone_ist_if_not_present(covisearch_datetime)
    covisearch_datetime = covisearch_datetime.astimezone(tz=timezone.utc)
    return covisearch_datetime


def _map_short_datetime_dd_mm_time_to_covisearch(short_datetime_str: str) -> datetime:
    # NOTE: KAPIL: Done for smarter logic in case of outlier date of different format.
    try:
        return covisearch.util.datetimeutil.map_short_datetime_dd_mm_to_utc_datetime(
            short_datetime_str, tz.gettz('Asia/Kolkata'))
    except:
        return covisearch.util.datetimeutil.map_short_datetime_mm_dd_to_utc_datetime(
            short_datetime_str, tz.gettz('Asia/Kolkata'))


def _map_short_datetime_mm_dd_time_to_covisearch(short_datetime_str: str) -> datetime:
    # NOTE: KAPIL: Done for smarter logic in case of outlier date of different format.
    try:
        return covisearch.util.datetimeutil.map_short_datetime_mm_dd_to_utc_datetime(
            short_datetime_str, tz.gettz('Asia/Kolkata'))
    except:
        return covisearch.util.datetimeutil.map_short_datetime_dd_mm_to_utc_datetime(
            short_datetime_str, tz.gettz('Asia/Kolkata'))


def _map_unix_timestamp_sec_to_covisearch(unix_timestamp_sec_str: str) -> datetime:
    return covisearch.util.datetimeutil.map_unix_timestamp_to_utc_datetime(
        unix_timestamp_sec_str, False)


def _map_unix_timestamp_millisec_to_covisearch(unix_timestamp_sec_str: str) -> datetime:
    return covisearch.util.datetimeutil.map_unix_timestamp_to_utc_datetime(
        unix_timestamp_sec_str, True)


def datetime_format_to_str(datetime_format: covisearch.util.datetimeutil.DatetimeFormat) -> str:
    datetime_format_strings = {
        covisearch.util.datetimeutil.DatetimeFormat.AGO: 'ago',
        covisearch.util.datetimeutil.DatetimeFormat.ISOFORMAT: 'isoformat',
        covisearch.util.datetimeutil.DatetimeFormat.SHORT_DATETIME_DD_MM:
            'short_datetime_dd_mm',
        covisearch.util.datetimeutil.DatetimeFormat.SHORT_DATETIME_MM_DD:
            'short_datetime_mm_dd',
        covisearch.util.datetimeutil.DatetimeFormat.UNIX_TIMESTAMP_SEC:
            'unix_timestamp_sec',
        covisearch.util.datetimeutil.DatetimeFormat.UNIX_TIMESTAMP_MILLISEC:
            'unix_timestamp_millisec'
    }
    return datetime_format_strings[datetime_format]


def datetime_format_from_str(datetime_format_str: str) -> \
        covisearch.util.datetimeutil.DatetimeFormat:
    datetime_formats = {
        'ago': covisearch.util.datetimeutil.DatetimeFormat.AGO,
        'isoformat': covisearch.util.datetimeutil.DatetimeFormat.ISOFORMAT,
        'short_datetime_dd_mm':
            covisearch.util.datetimeutil.DatetimeFormat.SHORT_DATETIME_DD_MM,
        'short_datetime_mm_dd':
            covisearch.util.datetimeutil.DatetimeFormat.SHORT_DATETIME_MM_DD,
        'unix_timestamp_sec':
            covisearch.util.datetimeutil.DatetimeFormat.UNIX_TIMESTAMP_SEC,
        'unix_timestamp_millisec':
            covisearch.util.datetimeutil.DatetimeFormat.UNIX_TIMESTAMP_MILLISEC
    }
    return datetime_formats[datetime_format_str.lower()]


def _set_timezone_ist_if_not_present(timestamp: datetime) -> datetime:
    return covisearch.util.datetimeutil.set_timezone_if_not_present(
        timestamp, tz.gettz('Asia/Kolkata'))


# if __name__ == '__main__':
#
#     # print('a minute ago = ' + str(_map_ago_format_timestamp_to_covisearch('a minute ago')))
#     # print('an hour ago = ' + str(_map_ago_format_timestamp_to_covisearch('an hour ago')))
#     # print('a day ago = ' + str(_map_ago_format_timestamp_to_covisearch('a day ago')))
#     # print('a week ago = ' + str(_map_ago_format_timestamp_to_covisearch('a week ago')))
#     # print('a month ago = ' + str(_map_ago_format_timestamp_to_covisearch('a month ago')))
#     # print('a year ago = ' + str(_map_ago_format_timestamp_to_covisearch('a year ago')))
#     #
#     # print('1 minute ago = ' + str(_map_ago_format_timestamp_to_covisearch('1 minute ago')))
#     # print('1 hour ago = ' + str(_map_ago_format_timestamp_to_covisearch('1 hour ago')))
#     # print('1 day ago = ' + str(_map_ago_format_timestamp_to_covisearch('1 day ago')))
#     # print('1 week ago = ' + str(_map_ago_format_timestamp_to_covisearch('1 week ago')))
#     # print('1 month ago = ' + str(_map_ago_format_timestamp_to_covisearch('1 month ago')))
#     # print('1 year ago = ' + str(_map_ago_format_timestamp_to_covisearch('1 year ago')))
#     #
#     # print('5 minutes ago = ' + str(_map_ago_format_timestamp_to_covisearch('5 minutes ago')))
#     # print('5 hours ago = ' + str(_map_ago_format_timestamp_to_covisearch('5 hours ago')))
#     # print('5 days ago = ' + str(_map_ago_format_timestamp_to_covisearch('5 days ago')))
#     # print('5 weeks ago = ' + str(_map_ago_format_timestamp_to_covisearch('5 weeks ago')))
#     # print('5 months ago = ' + str(_map_ago_format_timestamp_to_covisearch('5 months ago')))
#     # print('5 years ago = ' + str(_map_ago_format_timestamp_to_covisearch('5 years ago')))
#     #
#     # print('15 minutes ago = ' + str(_map_ago_format_timestamp_to_covisearch('15 minutes ago')))
#     # print('15 days ago = ' + str(_map_ago_format_timestamp_to_covisearch('15 days ago')))
#     # print('15 weeks ago = ' + str(_map_ago_format_timestamp_to_covisearch('15 weeks ago')))
#     # print('15 hours ago = ' + str(_map_ago_format_timestamp_to_covisearch('15 hours ago')))
#     # print('6 months ago = ' + str(_map_ago_format_timestamp_to_covisearch('6 months ago')))
#     # print('3 years ago = ' + str(_map_ago_format_timestamp_to_covisearch('3 years ago')))
#     #
#     # print('150 minutes ago = ' + str(_map_ago_format_timestamp_to_covisearch('150 minutes ago')))
#     # print('72 hours ago = ' + str(_map_ago_format_timestamp_to_covisearch('72 hours ago')))
#     # print('40 days ago = ' + str(_map_ago_format_timestamp_to_covisearch('40 days ago')))
#     # print('18 months ago = ' + str(_map_ago_format_timestamp_to_covisearch('18 months ago')))
#     print('end')
