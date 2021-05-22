from abc import ABC, abstractmethod
from typing import Dict, List, Callable
import enum
import urllib.parse

import covisearch.util as util
import covisearch.util.datetimeutil as datetimeutil


class CovidResourceType(enum.Enum):
    OXYGEN = 1
    PLASMA = 2
    HOSPITAL_BED = 3
    HOSPITAL_BED_ICU = 4
    AMBULANCE = 5

    @staticmethod
    def to_string(resource_type: 'CovidResourceType') -> str:
        res_type_strings = {
            CovidResourceType.PLASMA: 'plasma',
            CovidResourceType.HOSPITAL_BED_ICU: 'hospital_bed_icu',
            CovidResourceType.HOSPITAL_BED: 'hospital_bed',
            CovidResourceType.OXYGEN: 'oxygen',
            CovidResourceType.AMBULANCE: 'ambulance',
        }
        return res_type_strings[resource_type]

    @staticmethod
    def from_string(resource_type_str: str) -> 'CovidResourceType':
        res_types = {
            'plasma': CovidResourceType.PLASMA,
            'hospital_bed_icu': CovidResourceType.HOSPITAL_BED_ICU,
            'hospital_bed': CovidResourceType.HOSPITAL_BED,
            'oxygen': CovidResourceType.OXYGEN,
            'ambulance': CovidResourceType.AMBULANCE
        }
        return res_types[resource_type_str.lower()]


class CovidResourceInfo:
    CONTACT_NAME_LABEL = 'contact_name'
    ADDRESS_LABEL = 'address'
    DETAILS_LABEL = 'details'
    PHONE_NO_LABEL = 'phone_no'
    POST_TIME_LABEL = 'post_time'
    RESOURCE_TYPE_LABEL = 'resource_type'
    CITY_LABEL = 'city'
    AVAILABILITY_LABEL = 'availability'
    LAST_VERIFIED_UTC_LABEL = 'last_verified_utc'
    WEB_SOURCE_NAME_LABEL = 'web_source_name'
    WEB_SOURCE_HOMEPAGE_LABEL = 'web_source_homepage'

    @classmethod
    def score(cls, res_info: Dict) -> int:
        score = 0
        last_verified_time = res_info[cls.LAST_VERIFIED_UTC_LABEL]
        if last_verified_time is not None:
            verified_ago = util.elapsed_days(last_verified_time)
            if verified_ago < 5:
                score += 5 - verified_ago

        post_time = res_info[cls.POST_TIME_LABEL]
        if post_time is not None:
            posted_ago = util.elapsed_days(post_time)
            if posted_ago < 1:
                score += 1 - posted_ago
        return score

    @classmethod
    def remove_duplicates(cls, covisearch_resources: List[Dict]) -> List[Dict]:
        covisearch_res_by_phone = {}
        phone_label = cls.PHONE_NO_LABEL
        for covisearch_res_info in covisearch_resources:
            phone_no = covisearch_res_info[phone_label]
            if covisearch_res_info[phone_label] in covisearch_res_by_phone:
                covisearch_res_by_phone[phone_no] = \
                    cls._get_more_recently_verified_res_info(covisearch_res_info,
                                                             covisearch_res_by_phone[phone_no])
            else:
                covisearch_res_by_phone[phone_no] = covisearch_res_info
        return list(covisearch_res_by_phone.values())

    @classmethod
    def remove_unavailable_resources(cls, covisearch_resources: List[Dict]) -> List[Dict]:
        return [x for x in covisearch_resources if x[cls.AVAILABILITY_LABEL] is True]

    @classmethod
    def remove_redundant_fields(cls, covisearch_resources: List[Dict]) -> List[Dict]:
        cls._remove_availability_field(covisearch_resources)
        # TODO:KAPIL: Remove empty fields if we decide to
        return covisearch_resources

    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        last_verified_times_comp = cls._compare_datetime_field(
            res_info_a, res_info_b, cls.LAST_VERIFIED_UTC_LABEL)
        if last_verified_times_comp is not 0:
            return -1 * last_verified_times_comp

        post_times_comp = cls._compare_datetime_field(
            res_info_a, res_info_b, cls.POST_TIME_LABEL)
        if post_times_comp is not 0:
            return -1 * post_times_comp

        return 0

    @classmethod
    def _get_more_recently_verified_res_info(cls, res_info_a: Dict, res_info_b: Dict) -> Dict:
        last_verified_label = cls.LAST_VERIFIED_UTC_LABEL
        last_verified_a = res_info_a[last_verified_label]
        last_verified_b = res_info_b[last_verified_label]

        if last_verified_a is None and last_verified_b is not None:
            return res_info_b
        if last_verified_b is None and last_verified_a is not None:
            return res_info_a
        if last_verified_a > last_verified_b:
            return res_info_a
        else:
            return res_info_b

    @classmethod
    def _remove_availability_field(cls, covisearch_resources: List[Dict]):
        for res_info in covisearch_resources:
            res_info.pop(cls.AVAILABILITY_LABEL, None)

    @classmethod
    def _compare_datetime_field(cls, res_info_a: Dict, res_info_b: Dict,
                                field_name: str) -> int:
        return datetimeutil.compare_datetimes(res_info_a[field_name], res_info_b[field_name])


class BloodGroup(enum.Enum):
    A_P = 1
    A_N = 2
    B_P = 3
    B_N = 4
    O_P = 5
    O_N = 6
    AB_P = 7
    AB_N = 8
    ALL = 9

    @classmethod
    def to_string(cls, blood_grp: 'BloodGroup') -> str:
        blood_grp_str_mapping = {
            cls.A_P: 'a+',
            cls.A_N: 'a-',
            cls.B_P: 'b+',
            cls.B_N: 'b-',
            cls.O_P: 'o+',
            cls.O_N: 'o-',
            cls.AB_P: 'ab+',
            cls.AB_N: 'ab-',
            cls.ALL: 'all'
        }
        return blood_grp_str_mapping[blood_grp]

    @classmethod
    def from_string(cls, blood_grp_str: str) -> 'BloodGroup':
        blood_grp_str_mapping = {
            'a+': cls.A_P,
            'a-': cls.A_N,
            'b+': cls.B_P,
            'b-': cls.B_N,
            'o+': cls.O_P,
            'o-': cls.O_N,
            'ab+': cls.AB_P,
            'ab-': cls.AB_N,
            'all': cls.ALL
        }
        return blood_grp_str_mapping[blood_grp_str.lower()]


class PlasmaInfo(CovidResourceInfo):
    BLOOD_GROUP_LABEL = 'blood_group'

    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        return super().compare(res_info_a, res_info_b)


class OxygenInfo(CovidResourceInfo):
    LITRES_LABEL = 'litres'

    # TODO: Change when oxygen litres are implemented.
    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        return super().compare(res_info_a, res_info_b)


class HospitalBedsInfo(CovidResourceInfo):
    AVAILABLE_BEDS_LABEL = 'available_beds'

    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        super_comp = super().compare(res_info_a, res_info_b)
        if super_comp is not 0:
            return super_comp

        available_beds_a = res_info_a[cls.AVAILABLE_BEDS_LABEL]
        available_beds_b = res_info_b[cls.AVAILABLE_BEDS_LABEL]
        if available_beds_a is not None and available_beds_b is None:
            return -1
        if available_beds_b is not None and available_beds_a is None:
            return 1
        if available_beds_a is None and available_beds_b is None:
            return 0
        if available_beds_a > available_beds_b:
            return -1
        if available_beds_b > available_beds_a:
            return 1
        return 0


class AmbulanceInfo(CovidResourceInfo):
    @classmethod
    def compare(cls, res_info_a: Dict, res_info_b: Dict) -> int:
        return super().compare(res_info_a, res_info_b)


def get_res_info_comparator(resource_type: CovidResourceType):
    res_type_classes = {
        CovidResourceType.PLASMA: PlasmaInfo,
        CovidResourceType.OXYGEN: OxygenInfo,
        CovidResourceType.HOSPITAL_BED: HospitalBedsInfo,
        CovidResourceType.HOSPITAL_BED_ICU: HospitalBedsInfo,
        CovidResourceType.AMBULANCE: AmbulanceInfo
    }
    return res_type_classes[resource_type].compare


class SearchFilter:
    CITY_LABEL = 'city'
    RESOURCE_TYPE_LABEL = 'resource_type'
    BLOOD_GROUP_LABEL = 'blood_group'

    def __init__(self, city: str, resource_type: CovidResourceType, blood_group: BloodGroup):
        self._city: str = city.lower()
        self._resource_type: CovidResourceType = resource_type
        self._blood_group: BloodGroup = blood_group
        self._validate()

    @property
    def city(self) -> str:
        return self._city

    @property
    def resource_type(self) -> CovidResourceType:
        return self._resource_type

    @property
    def blood_group(self) -> BloodGroup:
        return self._blood_group

    def to_url_query_string_fmt(self) -> str:
        query_string = \
            self.CITY_LABEL + '=' + urllib.parse.quote(self._city) + '&' + \
            self.RESOURCE_TYPE_LABEL + '=' + \
            urllib.parse.quote(CovidResourceType.to_string(self._resource_type))
        if self._blood_group is not None and self._blood_group is not '':
            query_string = query_string + '&' + self.BLOOD_GROUP_LABEL + '=' + \
                           urllib.parse.quote(BloodGroup.to_string(self._blood_group))
        return query_string

    def _validate(self):
        if self._city is None or self._city is '':
            raise ValueError('city param must have non-empty value')
        if self._resource_type is None or self._resource_type is '':
            raise ValueError('resource_type param must have non-empty value')

    @classmethod
    def create_from_url_query_string_fmt(cls, search_filter: str) -> 'SearchFilter':
        query_params = \
            urllib.parse.parse_qs(search_filter, keep_blank_values=True, strict_parsing=True)

        if cls.CITY_LABEL not in query_params:
            raise ValueError('city param is mandatory')
        city = query_params[cls.CITY_LABEL][0]

        if cls.RESOURCE_TYPE_LABEL not in query_params:
            raise ValueError('resource_type param is mandatory')
        resource_type = CovidResourceType.from_string(query_params[cls.RESOURCE_TYPE_LABEL][0])

        if cls.BLOOD_GROUP_LABEL in query_params:
            blood_group = BloodGroup.from_string(query_params[cls.BLOOD_GROUP_LABEL][0])
        else:
            blood_group = None

        return SearchFilter(city, resource_type, blood_group)


class FilteredAggregatedResourceInfo:
    def __init__(self, search_filter: SearchFilter, res_info_data: List[Dict]):
        super().__init__()
        self.search_filter = search_filter
        self.data = res_info_data


class AggregatedResourceInfoRepo(ABC):
    @abstractmethod
    def set_resources_for_filter(self,
                                 filtered_aggregated_resource_info: FilteredAggregatedResourceInfo):
        raise NotImplementedError('FilteredAggregatedResourceInfoRepo is an interface')
